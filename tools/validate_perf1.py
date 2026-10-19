"""Targeted static and numerical checks for PERF1 shader fast paths.

This validator does not compile GLSL or execute a GPU shader.  It compares the
working shaders with a pre-PERF1 Git revision after evaluating only the
WORLD_ARIA conditional groups as disabled, then checks the small numerical
contracts that make the early exits safe. Intentional non-Aria edits from
later phases are applied to the baseline first (LATER_PHASE_EDITS).
"""

from __future__ import annotations

import argparse
import math
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EDITED_SHADERS = (
    Path("shaders/include/lighting/cloud_shadows.glsl"),
    Path("shaders/include/fog/overworld/raymarched.glsl"),
    Path("shaders/include/sky/clouds/cumulus.glsl"),
    Path("shaders/include/sky/clouds/altocumulus.glsl"),
)

# Intentional non-Aria edits made after PERF1, applied to the baseline text
# before the parity comparison so later phases do not mask PERF1 regressions.
LATER_PHASE_EDITS = {
    # U1: upstream 3e0f3e3 requires SHADOW_COLOR for colored light shafts.
    Path("shaders/include/fog/overworld/raymarched.glsl"): (
        (
            "#ifdef AIR_FOG_COLORED_LIGHT_SHAFTS\n        float depth0",
            "#if defined AIR_FOG_COLORED_LIGHT_SHAFTS && defined SHADOW_COLOR\n"
            "        float depth0",
        ),
    ),
}


def apply_later_phase_edits(path: Path, text: str) -> str:
    text = output_text(text.splitlines(keepends=True))
    for old, new in LATER_PHASE_EDITS.get(path, ()):
        if text.count(old) != 1:
            raise AssertionError(f"{path}: later-phase edit anchor not found exactly once")
        text = text.replace(old, new)
    return text


def git_text(revision: str, path: Path) -> str:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path.as_posix()}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8")


def is_aria_condition(directive: str) -> tuple[bool, bool] | None:
    """Return (is_aria_condition, value_when_aria_is_defined) if recognized."""
    directive = directive.strip()
    if re.fullmatch(r"ifdef\s+WORLD_ARIA", directive):
        return True, True
    if re.fullmatch(r"ifndef\s+WORLD_ARIA", directive):
        return True, False
    match = re.fullmatch(r"if\s+(!\s*)?defined\s*\(\s*WORLD_ARIA\s*\)", directive)
    if match:
        return True, not bool(match.group(1))
    match = re.fullmatch(r"if\s+defined\s*\s*WORLD_ARIA", directive)
    if match:
        return True, True
    return None


def without_aria(source: str) -> str:
    """Preprocess WORLD_ARIA as undefined, retaining unrelated directives."""
    output: list[str] = []
    frames: list[tuple[bool, bool, bool]] = []  # aria, parent active, condition
    active = True

    for line in source.splitlines(keepends=True):
        match = re.match(r"^\s*#\s*(ifdef|ifndef|if|elif|else|endif)\b(.*)$", line)
        if not match:
            if active:
                output.append(line)
            continue

        keyword, tail = match.group(1), match.group(2).strip()
        if keyword in ("ifdef", "ifndef", "if"):
            condition = is_aria_condition(f"{keyword} {tail}")
            if condition is not None:
                _, value_when_defined = condition
                frames.append((True, active, value_when_defined))
                active = active and not value_when_defined
            else:
                if "WORLD_ARIA" in tail:
                    raise ValueError(f"Unsupported WORLD_ARIA expression: {line.rstrip()}")
                frames.append((False, active, False))
                if active:
                    output.append(line)
            continue

        if not frames:
            raise ValueError(f"Unmatched preprocessor directive: {line.rstrip()}")
        aria, parent_active, condition = frames[-1]
        if keyword == "else":
            if aria:
                active = parent_active and condition
                frames[-1] = (aria, parent_active, True)
            elif active:
                output.append(line)
            continue
        if keyword == "elif":
            if aria:
                raise ValueError(f"Unsupported WORLD_ARIA elif: {line.rstrip()}")
            elif active:
                output.append(line)
            continue
        if keyword == "endif":
            frames.pop()
            if aria:
                active = parent_active
            elif active:
                output.append(line)
            continue

    if frames:
        raise ValueError("Unclosed preprocessor conditional")
    return output_text(output)


def comparable(text: str) -> list[str]:
    """Compare code/directives while ignoring stripping whitespace and comments."""
    text = re.sub(r"/\*.*?\*/", "", output_text(text.splitlines(keepends=True)), flags=re.S)
    return [re.sub(r"\s+", "", re.sub(r"//.*", "", line)) for line in text.splitlines() if re.sub(r"//.*", "", line).strip()]


def output_text(lines: list[str]) -> str:
    return "".join(lines).replace("\r\n", "\n").replace("\r", "\n")


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def cloud_shadow(shadow: float, light_y: float, altitude_fraction: float) -> float:
    fade = smoothstep(0.05, 0.15, light_y) * max(0.0, min(1.0, 1.0 - altitude_fraction))
    return shadow * fade + (1.0 - fade)


def legacy_zero_fog() -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Model the legacy eight zero-length iterations from the shader constants."""
    transmittance = [1.0, 1.0, 1.0]
    scattering = [0.0, 0.0, 0.0]
    for _ in range(8):
        step_length = 0.0
        density = [0.4, 0.2]
        optical_depth = [density[0] * step_length, density[1] * step_length, density[0] * step_length]
        step_transmittance = [math.exp(-component) for component in optical_depth]
        visible = [(1.0 - step_transmittance[c]) * transmittance[c] /
                   max(optical_depth[c], 1e-6) for c in range(3)]
        for channel in range(3):
            scattering[channel] += visible[channel] * density[channel % 2] * step_length
            transmittance[channel] *= step_transmittance[channel]
    return tuple(scattering), tuple(transmittance)


def cloud_zero_step_metadata(kind: str, density: float, epsilon: float,
                             entry_distance: float, coverage_fade: float = 1.0) -> float:
    """Model only the metadata branch at a zero-length cloud interval."""
    if kind == "cumulus":
        if density < epsilon:
            return 1e6
        density *= coverage_fade
        return entry_distance if density > 0.0 else 1e6
    if kind == "altocumulus":
        return entry_distance if density >= epsilon else 1e6
    raise ValueError(kind)


def legacy_cloud_zero_step(kind: str, density: float, epsilon: float,
                           entry_distance: float, coverage_fade: float = 1.0) -> float:
    weight = 0.0
    iterations = 20 if kind == "cumulus" else 6
    for _ in range(iterations):
        sample = density
        if sample < epsilon:
            continue
        if kind == "cumulus":
            sample *= coverage_fade
        weight += sample
    return entry_distance if weight > 0.0 else 1e6


def run(baseline: str) -> int:
    checks = 0

    def check(label: str, condition: bool) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(label)

    check("WORLD_ARIA conditional evaluator selects non-Aria else", comparable(without_aria("#ifdef WORLD_ARIA\nA\n#else\nB\n#endif\n")) == ["B"])
    nested = "#if defined(UNRELATED)\n#ifdef WORLD_ARIA\nA\n#else\nB\n#endif\n#endif\n"
    check("nested unrelated conditional survives Aria stripping", comparable(without_aria(nested)) == ["#ifdefined(UNRELATED)", "B", "#endif"])
    check("ifndef WORLD_ARIA selects its non-Aria branch", comparable(without_aria("#ifndef WORLD_ARIA\nB\n#else\nA\n#endif\n")) == ["B"])

    for path in EDITED_SHADERS:
        current = (ROOT / path).read_text(encoding="utf-8")
        before = apply_later_phase_edits(path, git_text(baseline, path))
        check(f"{path}: WORLD_ARIA-disabled source differs from baseline", comparable(without_aria(current)) == comparable(before))
        check(f"{path}: current source contains a WORLD_ARIA guard", "WORLD_ARIA" in current)

    shadow_source = (ROOT / EDITED_SHADERS[0]).read_text(encoding="utf-8")
    check("cloud shadow fast path has exact-zero condition", "if (cloud_shadow_fade == 0.0)" in shadow_source)
    shadow_guard = shadow_source.index("#ifdef WORLD_ARIA")
    shadow_end = shadow_source.index("#endif", shadow_guard)
    shadow_projection = shadow_source.index("project_cloud_shadow_map", shadow_end)
    check("cloud shadow fast path returns identity before projection", "return 1.0;" in shadow_source[shadow_guard:shadow_end] and shadow_end < shadow_projection)
    check("zero sun fade preserves identity", cloud_shadow(0.37, 0.0, 0.0) == 1.0)
    check("zero altitude fade preserves identity", cloud_shadow(0.37, 0.10, 1.0) == 1.0)
    check("positive shadow fade still has a contribution", 0.0 < cloud_shadow(0.37, 0.10, 0.0) < 1.0)

    fog_source = (ROOT / EDITED_SHADERS[1]).read_text(encoding="utf-8")
    clamp = fog_source.index("ray_length = clamp(")
    fast_path = fog_source.index("#ifdef WORLD_ARIA", clamp)
    step_setup = fog_source.index("uint step_count", fast_path)
    check("air fog fast path follows clamp", clamp < fast_path < step_setup)
    fog_neutral = fog_source[fast_path:step_setup]
    check("air fog fast path checks exact zero and returns neutral", "if (ray_length == 0.0)" in fog_neutral and "return mat2x3(vec3(0.0), vec3(1.0));" in fog_neutral)
    check("legacy zero fog uses eight iterations", legacy_zero_fog() == ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)))
    small_length = 1e-6
    check("fast path source uses exact zero rather than epsilon", "ray_length == 0.0" in fog_source)
    check("positive small length retains legacy minimum eight steps", int(8.0 + 0.1 * small_length) == 8)

    for path, kind in ((Path("shaders/include/sky/clouds/cumulus.glsl"), "cumulus"),
                       (Path("shaders/include/sky/clouds/altocumulus.glsl"), "altocumulus")):
        source = (ROOT / path).read_text(encoding="utf-8")
        clamp = source.index("ray_length = clamp(")
        guard = source.index("#ifdef WORLD_ARIA", clamp)
        march = source.index("for (uint i = 0u", guard)
        check(f"{path}: zero interval guard precedes primary march", clamp < guard < march)
        check(f"{path}: zero interval guard checks exact zero", "if (ray_length == 0.0)" in source[guard:march])
        # Check the actual GLSL outputs, independently of the Python metadata
        # model below. Otherwise wrong shader return values escape that model.
        fast_source = re.sub(r"//[^\n]*", "", source[guard:source.index("vec2 scattering", guard)])
        outputs = re.findall(
            r"return\s+CloudsResult\(\s*vec4\(([^)]+)\)\s*,\s*([^,]+),\s*([^)]+)\);",
            fast_source,
        )
        check(f"{kind}: fast-path outputs are neutral", bool(outputs) and all(
            float(scattering) == 0.0 and float(transmittance) == 1.0
            for scattering, transmittance, _ in outputs
        ))
        distances = [distance.strip() for _, _, distance in outputs]
        sentinel = re.search(r"float\s+apparent_distance\s*=.*?:\s*([^;]+);", fast_source, re.S)
        check(f"{kind}: shader retains empty-distance sentinel", sentinel is not None
              and float(sentinel.group(1)) == 1e6
              and all(distance == "apparent_distance" or float(distance) == 1e6 for distance in distances))
        cases = ((0.2, 1.0, "density above epsilon"), (0.0, 1.0, "density below epsilon"),
                 (1e-6, 1.0, "density exactly epsilon"))
        if kind == "cumulus":
            cases += ((2e-6, 0.25, "positive post-coverage density below epsilon"),)
        for density, fade, label in cases:
            fast = cloud_zero_step_metadata(kind, density, 1e-6, 42.0, fade)
            legacy = legacy_cloud_zero_step(kind, density, 1e-6, 42.0, fade)
            check(f"{kind}: {label} matches legacy metadata", fast == legacy)
        if kind == "cumulus":
            fast = cloud_zero_step_metadata(kind, 0.2, 1e-6, 42.0, 0.0)
            legacy = legacy_cloud_zero_step(kind, 0.2, 1e-6, 42.0, 0.0)
            check("cumulus: zero coverage fade matches legacy sentinel", fast == legacy == 1e6)

    print(f"PERF1 validation PASSED: {checks} checks; baseline={baseline}")
    print("Boundary: static preprocessing and numerical contract models only; no GLSL compilation or GPU/runtime execution claimed.")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default="d6899b2", help="pre-PERF1 Git revision (default: d6899b2)")
    args = parser.parse_args()
    run(args.baseline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
