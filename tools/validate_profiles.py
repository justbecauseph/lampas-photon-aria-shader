"""Static checks for shader profiles and option menus in shaders.properties.

Every profile token must name an option declared in settings.glsl, every
`OPTION=value` must be in that option's allowed list, every `profile.X`
include must resolve without cycles, and every menu entry must resolve.
Menu entries that upstream Photon v1.3 already left unresolved are listed in
KNOWN_UNRESOLVED_MENU_ENTRIES so only new ones fail.

This mirrors how Iris discovers options from shader source; it does not run
Iris. A bare `#define NAME` (optionally commented out) is a boolean option,
`#define NAME value // [a b c]` and `const type name = value; // [a b c]` are
value options.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / "shaders" / "settings.glsl"
PROPERTIES = ROOT / "shaders" / "shaders.properties"

KNOWN_UNRESOLVED_MENU_ENTRIES = {
    "WATER_REFRACTION",
    "WATER_REFRACTION_INTENSITY",
    "CLOUDS_DAILY_WEATHER",
    "CLOUDS_CUMULUS_CONGESTUS_PRIMARY_STEPS_H",
    "CLOUDS_CUMULUS_CONGESTUS_PRIMARY_STEPS_Z",
}

BOOLEAN = re.compile(r"^\s*(?://\s*)?#define\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?://.*)?$")
VALUE_DEFINE = re.compile(
    r"^\s*(?://\s*)?#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(\S+)\s*//[^\[]*\[([^\]]*)\]")
VALUE_CONST = re.compile(
    r"^\s*const\s+\w+\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;]+);\s*//[^\[]*\[([^\]]*)\]")


def read_options() -> tuple[set[str], dict[str, list[str]]]:
    booleans: set[str] = set()
    values: dict[str, list[str]] = {}
    for line in SETTINGS.read_text(encoding="utf-8").splitlines():
        if m := VALUE_DEFINE.match(line) or VALUE_CONST.match(line):
            values[m.group(1)] = m.group(3).split()
        elif m := BOOLEAN.match(line):
            booleans.add(m.group(1))
    return booleans, values


def read_properties() -> dict[str, str]:
    """Return key -> value, joining backslash continuations."""
    entries: dict[str, str] = {}
    lines = PROPERTIES.read_text(encoding="utf-8").splitlines()
    buffer = ""
    for raw in lines:
        line = raw.rstrip()
        if line.endswith("\\"):
            buffer += line[:-1] + " "
            continue
        line = buffer + line
        buffer = ""
        if not line.strip() or line.lstrip().startswith(("#", "!")):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            entries[key.strip()] = value.strip()
    return entries


def same_number(a: str, b: str) -> bool:
    try:
        return float(a) == float(b)
    except ValueError:
        return False


def main() -> int:
    booleans, values = read_options()
    properties = read_properties()
    profiles = {k[len("profile."):]: v.split() for k, v in properties.items() if k.startswith("profile.")}
    errors: list[str] = []

    for name, tokens in profiles.items():
        for token in tokens:
            if token.startswith("profile.") or token.startswith("!profile."):
                target = token.lstrip("!")[len("profile."):]
                if target not in profiles:
                    errors.append(f"profile.{name}: unknown include {token}")
                continue
            if "=" in token:
                option, value = token.split("=", 1)
                if option not in values:
                    errors.append(f"profile.{name}: {option} is not a value option")
                elif not any(value == v or same_number(value, v) for v in values[option]):
                    errors.append(f"profile.{name}: {option}={value} not in {values[option]}")
                continue
            option = token.lstrip("!")
            if option not in booleans:
                errors.append(f"profile.{name}: {option} is not a boolean option")

    def check_cycle(name: str, stack: tuple[str, ...]) -> None:
        if name in stack:
            errors.append(f"profile include cycle: {' -> '.join(stack + (name,))}")
            return
        for token in profiles.get(name, ()):
            if token.lstrip("!").startswith("profile."):
                check_cycle(token.lstrip("!")[len("profile."):], stack + (name,))

    for name in profiles:
        check_cycle(name, ())

    screens = {k[len("screen."):] for k in properties if k.startswith("screen.") and "." not in k[len("screen."):]}
    unresolved: set[str] = set()
    for key, value in properties.items():
        if not (key == "screen" or (key.startswith("screen.") and "." not in key[len("screen."):]) or key == "sliders"):
            continue
        for entry in value.split():
            if entry in ("<empty>", "<profile>", "*"):
                continue
            if entry.startswith("[") and entry.endswith("]"):
                if entry[1:-1] not in screens:
                    errors.append(f"{key}: unknown screen {entry}")
                continue
            if entry not in booleans and entry not in values:
                unresolved.add(entry)
    for entry in sorted(unresolved - KNOWN_UNRESOLVED_MENU_ENTRIES):
        errors.append(f"menu entry {entry} does not resolve to an option")

    if errors:
        print("Profile validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Profile validation PASSED: {len(profiles)} profiles ({', '.join(profiles)}); "
          f"{len(booleans)} boolean and {len(values)} value options; "
          f"{len(unresolved & KNOWN_UNRESOLVED_MENU_ENTRIES)} known upstream menu gaps.")
    print("Boundary: static parsing only; Iris option discovery and runtime loading are not executed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
