"""Compile every shader program with glslang under several option sets.

For each option set (settings.glsl defaults, each profile in
shaders.properties, and optionally a list of extra feature combinations) the
tool:

* applies the options to settings.glsl the way Iris would,
* evaluates shaders.properties (including its #if blocks) to skip programs the
  option set disables (`program.<world>/<name>.enabled`),
* expands `#include` directives, injects the Iris built-in macros, and
* compiles each wrapper in shaders/world0, aria, world-1 and world1 with
  glslang, without LOD mods, and with Voxy or Distant Horizons where the
  program supports them.

Wrappers declare `#version 400 compatibility`, but glslang rejects the
multi-line preprocessor directives used throughout the pack in that profile,
so sources are compiled as `460 compatibility`. This is a GLSL semantic check:
it does not run Iris's GLSL transformer, link program stages, or test a
driver. The Voxy patch files (voxy_*.glsl) need Voxy's injected header and are
not compiled.

With `--baseline REV`, the same matrix is compiled for REV and only programs
that compiled at REV but fail now are reported as errors.

The injected macros follow Iris's StandardMacros (MC_VERSION 260200 for
Minecraft 26.2, the DH_BLOCK_* IDs, render stages, subgroup extensions). DH
vertex shaders also get the `int dhMaterialId` global that Iris's DH
transformers add.

glslang is located with --glslang, the GLSLANG environment variable,
`glslang`/`glslangValidator` on PATH, or ~/.local/bin.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import fnmatch
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORLDS = ("world0", "aria", "world-1", "world1")
STAGES = {".vsh": "vert", ".fsh": "frag", ".gsh": "geom", ".csh": "comp"}

# Feature combinations that profiles never select but that have their own code
# paths. Each applies on top of the settings.glsl defaults.
EXTENDED_SETS: dict[str, dict[str, str | bool]] = {
    "bloomy-fog-no-vl": {"BLOOMY_FOG": True, "VL": False},
    "colored-light-shafts": {"AIR_FOG_COLORED_LIGHT_SHAFTS": True, "SHADOW_COLOR": True},
    "colored-lights-no-vl": {"COLORED_LIGHTS": True, "VL": False},
    "dof-motion-blur": {"DOF": True, "MOTION_BLUR": True},
    "grade-contrast": {"GRADE_CONTRAST": "1.20"},
    "histogram-exposure": {"AUTO_EXPOSURE": "AUTO_EXPOSURE_HISTOGRAM"},
    "ssao": {"SHADER_AO": "SHADER_AO_SSAO"},
    "taau": {"TAAU": True},
    "vanilla-sun-moon": {"VANILLA_SUN": True, "VANILLA_MOON": True},
    "water-caustics": {"WATER_CAUSTICS": True},
    "water-detail-distance": {"WATER_DETAIL_DISTANCE": "128"},
}

VENDORS = {
    "nvidia": ("MC_GL_VENDOR_NVIDIA", "MC_GL_RENDERER_GEFORCE"),
    "amd": ("MC_GL_VENDOR_ATI", "MC_GL_RENDERER_RADEON"),
    "intel": ("MC_GL_VENDOR_INTEL", "MC_GL_RENDERER_INTEL"),
}

DH_BLOCKS = (
    "UNKNOWN", "LEAVES", "STONE", "WOOD", "METAL", "DIRT", "LAVA", "DEEPSLATE",
    "SNOW", "SAND", "TERRACOTTA", "NETHER_STONE", "WATER", "GRASS", "AIR", "ILLUMINATED",
)

RENDER_STAGES = (
    "NONE", "SKY", "SUNSET", "CUSTOM_SKY", "SUN", "MOON", "STARS", "VOID",
    "TERRAIN_SOLID", "TERRAIN_CUTOUT_MIPPED", "TERRAIN_CUTOUT", "ENTITIES",
    "BLOCK_ENTITIES", "DESTROY", "OUTLINE", "DEBUG", "HAND_SOLID",
    "TERRAIN_TRANSLUCENT", "TRIPWIRE", "PARTICLES", "CLOUDS", "RAIN_SNOW",
    "WORLD_BORDER", "HAND_TRANSLUCENT",
)

INCLUDE = re.compile(r'^[ \t]*#include[ \t]+"([^"]+)"', re.M)
ACTIVE_DEFINE = re.compile(r"^[ \t]*#define[ \t]+([A-Za-z_]\w*)(?:[ \t]+([^/\n]*?))?[ \t]*(?://.*)?$", re.M)


def iris_macros(mc_version: int, vendor: str, extensions: list[str],
                extra: dict[str, str | bool]) -> dict[str, str]:
    """Macros Iris defines for every program (see Iris StandardMacros)."""
    vendor_macro, renderer_macro = VENDORS[vendor]
    macros = {
        "MC_VERSION": str(mc_version),
        "MC_MIPMAP_LEVEL": "4",
        "IRIS_VERSION": "11104",
        "MC_GL_VERSION": "460",
        "MC_GLSL_VERSION": "460",
        "MC_OS_WINDOWS": "",
        vendor_macro: "",
        renderer_macro: "",
        "IS_IRIS": "",
        "IRIS_REQUIRES_SEPARATE_ENTITY_DRAWS": "",
        "MAX_COLOR_BUFFERS": "16",
        "IRIS_HAS_TRANSLUCENCY_SORTING": "",
        "IRIS_TAG_SUPPORT": "2",
        "MC_NORMAL_MAP": "",
        "MC_SPECULAR_MAP": "",
        "MC_RENDER_QUALITY": "1.0",
        "MC_SHADOW_QUALITY": "1.0",
        "MC_HAND_DEPTH": "0.125",
    }
    for index, name in enumerate(DH_BLOCKS):
        macros[f"DH_BLOCK_{name}"] = str(index)
    for extension in extensions:
        macros[f"MC_GL_{extension}"] = ""
    for index, name in enumerate(RENDER_STAGES):
        macros[f"MC_RENDER_STAGE_{name}"] = str(index)
    for name, value in extra.items():
        if value is False:
            macros.pop(name, None)
        else:
            macros[name] = "" if value is True else str(value)
    return macros


# --------------------------------------------------------------------------
#   Options
# --------------------------------------------------------------------------

def apply_options(settings: str, options: dict[str, str | bool]) -> str:
    """Return settings.glsl text with the given options applied."""
    for name, value in options.items():
        escaped = re.escape(name)
        if isinstance(value, bool):
            pattern = re.compile(rf"^([ \t]*)(?://[ \t]*)?#define[ \t]+{escaped}\b(.*)$", re.M)
            prefix = "#define " if value else "//#define "
            settings, count = pattern.subn(lambda m: m.group(1) + prefix + name + m.group(2), settings, count=1)
        else:
            pattern = re.compile(rf"^([ \t]*)(?://[ \t]*)?#define[ \t]+{escaped}[ \t]+\S+", re.M)
            settings, count = pattern.subn(lambda m: f"{m.group(1)}#define {name} {value}", settings, count=1)
            if count == 0:
                pattern = re.compile(rf"(const\s+\w+\s+{escaped}\s*=\s*)[^;]+;")
                settings, count = pattern.subn(lambda m: f"{m.group(1)}{value};", settings, count=1)
        if count == 0:
            raise SystemExit(f"error: option {name} is not declared in settings.glsl")
    return settings


def parse_option_tokens(tokens: list[str]) -> dict[str, str | bool]:
    options: dict[str, str | bool] = {}
    for token in tokens:
        if token.startswith("!"):
            options[token[1:]] = False
        elif "=" in token:
            key, value = token.split("=", 1)
            options[key] = value
        else:
            options[token] = True
    return options


def read_profiles(properties: str) -> dict[str, dict[str, str | bool]]:
    raw: dict[str, list[str]] = {}
    for line in properties.splitlines():
        match = re.match(r"^profile\.(\w+)\s*=\s*(.*)$", line.strip())
        if match:
            raw[match.group(1)] = match.group(2).split()

    def resolve(name: str, seen: tuple[str, ...] = ()) -> dict[str, str | bool]:
        if name in seen:
            raise SystemExit(f"error: profile include cycle at profile.{name}")
        options: dict[str, str | bool] = {}
        for token in raw[name]:
            if token.startswith("profile."):
                options.update(resolve(token[len("profile."):], seen + (name,)))
            else:
                options.update(parse_option_tokens([token]))
        return options

    return {name: resolve(name) for name in raw}


def active_macros(settings: str, base: dict[str, str]) -> dict[str, str]:
    """Macros defined by uncommented #define lines, plus the Iris macros."""
    macros = dict(base)
    for match in ACTIVE_DEFINE.finditer(settings):
        macros[match.group(1)] = (match.group(2) or "").strip()
    return macros


# --------------------------------------------------------------------------
#   Preprocessor expressions (shaders.properties and program toggles)
# --------------------------------------------------------------------------

TOKEN = re.compile(r"\s*(defined|&&|\|\||==|!=|>=|<=|[!()<>+\-*/]|[A-Za-z_]\w*|\d+(?:\.\d+)?)")


def macro_value(name: str, macros: dict[str, str], depth: int = 0) -> float:
    if name == "true":
        return 1
    if name == "false" or name not in macros or depth > 16:
        return 0
    value = macros[name]
    if value == "":
        return 1
    try:
        return float(value)
    except ValueError:
        if re.fullmatch(r"[A-Za-z_]\w*", value):
            return macro_value(value, macros, depth + 1)
        return 0


def evaluate(expression: str, macros: dict[str, str]) -> bool:
    tokens = TOKEN.findall(expression)
    python: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "defined":
            if tokens[i + 1] == "(":
                name, i = tokens[i + 2], i + 4
            else:
                name, i = tokens[i + 1], i + 2
            python.append(str(name in macros))
            continue
        if token == "&&":
            python.append(" and ")
        elif token == "||":
            python.append(" or ")
        elif token == "!":
            python.append(" not ")
        elif re.fullmatch(r"[A-Za-z_]\w*", token):
            python.append(repr(macro_value(token, macros)))
        else:
            python.append(token)
        i += 1
    try:
        return bool(eval("".join(python), {"__builtins__": {}}, {}))
    except Exception as error:  # noqa: BLE001 - report the unparsable expression
        raise SystemExit(f"error: cannot evaluate preprocessor expression {expression!r}: {error}")


def preprocess_properties(text: str, macros: dict[str, str]) -> str:
    """Evaluate #if blocks the way Iris preprocesses shaders.properties."""
    macros = dict(macros)
    output: list[str] = []
    stack: list[tuple[bool, bool]] = []  # (branch active, any branch taken)
    for line in text.splitlines():
        stripped = line.strip()
        enclosing = all(active for active, _ in stack)
        if match := re.match(r"#(ifdef|ifndef)\s+(\w+)", stripped):
            condition = (match.group(2) in macros) == (match.group(1) == "ifdef")
            stack.append((enclosing and condition, condition))
        elif match := re.match(r"#if\s+(.*)", stripped):
            condition = evaluate(match.group(1), macros)
            stack.append((enclosing and condition, condition))
        elif match := re.match(r"#elif\s+(.*)", stripped):
            _, taken = stack.pop()
            enclosing = all(active for active, _ in stack)
            condition = not taken and evaluate(match.group(1), macros)
            stack.append((enclosing and condition, taken or condition))
        elif stripped.startswith("#else"):
            _, taken = stack.pop()
            enclosing = all(active for active, _ in stack)
            stack.append((enclosing and not taken, True))
        elif stripped.startswith("#endif"):
            stack.pop()
        elif enclosing:
            if match := re.match(r"#define\s+(\w+)\s*(.*)", stripped):
                macros[match.group(1)] = match.group(2)
            else:
                output.append(line)
    return "\n".join(output)


def program_toggles(properties: str, macros: dict[str, str]) -> dict[tuple[str, str], bool]:
    toggles: dict[tuple[str, str], bool] = {}
    for line in preprocess_properties(properties, macros).splitlines():
        match = re.match(r"^\s*program\.([^/\s]+)/(\w+)\.enabled\s*=\s*(.+?)\s*$", line)
        if match:
            toggles[(match.group(1), match.group(2))] = evaluate(match.group(3), macros)
    return toggles


def is_enabled(toggles: dict[tuple[str, str], bool], world: str, program: str) -> bool:
    if (world, program) in toggles:
        return toggles[(world, program)]
    if program.startswith("shadow_") and (world, "shadow") in toggles:
        return toggles[(world, "shadow")]
    return True


# --------------------------------------------------------------------------
#   Compilation
# --------------------------------------------------------------------------

@dataclass
class OptionSet:
    name: str
    options: dict[str, str | bool]


@dataclass
class Job:
    option_set: str
    wrapper: str  # e.g. "aria/composite1.fsh"
    variant: str  # "nolod", "voxy" or "dh"
    stage: str
    source: str
    digest: str = field(init=False)

    def __post_init__(self) -> None:
        self.digest = hashlib.sha1(f"{self.stage}\0{self.source}".encode()).hexdigest()


def find_glslang(explicit: str | None) -> str:
    candidates = [explicit, os.environ.get("GLSLANG"), shutil.which("glslang"), shutil.which("glslangValidator")]
    home_bin = Path.home() / ".local" / "bin"
    candidates += [str(home_bin / name) for name in ("glslang.exe", "glslang", "glslangValidator.exe", "glslangValidator")]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise SystemExit("error: glslang not found; pass --glslang, set GLSLANG, or put glslang on PATH")


def expand(shaders: Path, path: str, settings: str, stack: tuple[str, ...] = ()) -> str:
    path = path.lstrip("/")
    if path in stack:
        raise SystemExit(f"error: include cycle: {' -> '.join(stack + (path,))}")
    text = settings if path == "settings.glsl" else (shaders / path).read_text(encoding="utf-8")

    def include(match: re.Match[str]) -> str:
        target = match.group(1)
        if not target.startswith("/"):
            target = (Path(path).parent / target).as_posix()
        return expand(shaders, target, settings, stack + (path,))

    return INCLUDE.sub(include, text)


def with_header(source: str, macros: dict[str, str], defines: tuple[str, ...],
                globals_: tuple[str, ...] = ()) -> str:
    header = ["#version 460 compatibility"]
    header += [f"#define {name} {value}".rstrip() for name, value in macros.items()]
    header += [f"#define {name}" for name in defines]
    lines = source.split("\n")
    version = next((i for i, line in enumerate(lines) if line.strip().startswith("#version")), None)
    if version is None:
        raise ValueError("wrapper has no #version line")
    # Injected globals go straight after the header, where they cannot end up
    # inside a conditional block
    lines[version] = "\n".join(header + list(globals_))
    return "\n".join(lines)


def build_jobs(shaders: Path, option_sets: list[OptionSet], args: argparse.Namespace) -> tuple[list[Job], int]:
    settings_base = (shaders / "settings.glsl").read_text(encoding="utf-8")
    properties = (shaders / "shaders.properties").read_text(encoding="utf-8")
    base_macros = iris_macros(args.mc_version, args.vendor, args.extensions, parse_option_tokens(args.define))
    jobs: list[Job] = []
    skipped = 0

    for option_set in option_sets:
        settings = apply_options(settings_base, option_set.options)
        toggles = program_toggles(properties, active_macros(settings, base_macros))
        for world in args.worlds:
            for wrapper_path in sorted((shaders / world).iterdir()):
                stage = STAGES.get(wrapper_path.suffix)
                if stage is None:
                    continue
                if args.programs and not any(fnmatch.fnmatch(wrapper_path.name, p) for p in args.programs):
                    continue
                if not is_enabled(toggles, world, wrapper_path.stem):
                    skipped += 1
                    continue
                wrapper = f"{world}/{wrapper_path.name}"
                expanded = expand(shaders, wrapper, settings)
                variants: list[tuple[str, tuple[str, ...]]] = []
                if wrapper_path.name.startswith("dh_"):
                    variants.append(("dh", ("DISTANT_HORIZONS",)))
                else:
                    variants.append(("nolod", ()))
                    if "voxy" in args.variants and re.search(r"\bVOXY\b", expanded):
                        variants.append(("voxy", ("VOXY",)))
                    if "dh" in args.variants and re.search(r"\bDISTANT_HORIZONS\b", expanded):
                        variants.append(("dh", ("DISTANT_HORIZONS",)))
                for variant, defines in variants:
                    # Iris's DH transformers declare this global in DH vertex shaders
                    globals_ = ("int dhMaterialId;",) if variant == "dh" and stage == "vert" else ()
                    jobs.append(Job(option_set.name, wrapper, variant, stage,
                                    with_header(expanded, base_macros, defines, globals_)))
    return jobs, skipped


def compile_jobs(jobs: list[Job], glslang: str, workdir: Path, parallel: int) -> dict[str, tuple[bool, str]]:
    unique = {job.digest: job for job in jobs}

    def run(job: Job) -> tuple[str, tuple[bool, str]]:
        source = workdir / f"{job.digest}.{job.stage}"
        source.write_text(job.source, encoding="utf-8")
        result = subprocess.run([glslang, "-S", job.stage, str(source)], capture_output=True, text=True)
        errors = [line for line in (result.stdout + result.stderr).splitlines() if "ERROR" in line]
        return job.digest, (result.returncode == 0, "\n".join(errors))

    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as pool:
        return dict(pool.map(run, unique.values()))


def matrix(shaders: Path, option_sets: list[OptionSet], args: argparse.Namespace, glslang: str,
           workdir: Path) -> tuple[dict[tuple[str, str, str], tuple[bool, str]], int, int]:
    jobs, skipped = build_jobs(shaders, option_sets, args)
    results = compile_jobs(jobs, glslang, workdir, args.jobs)
    outcome = {(job.option_set, job.wrapper, job.variant): results[job.digest] for job in jobs}
    return outcome, skipped, len({job.digest for job in jobs})


def extract_revision(revision: str, destination: Path) -> Path:
    archive = subprocess.run(["git", "archive", "--format=tar", revision, "shaders"],
                             cwd=ROOT, check=True, capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter="data")
    return destination / "shaders"


def select_option_sets(args: argparse.Namespace, profiles: dict[str, dict[str, str | bool]]) -> list[OptionSet]:
    overrides = parse_option_tokens(args.set)
    sets: list[OptionSet] = []
    for name in args.profiles:
        if name == "default":
            sets.append(OptionSet("default", dict(overrides)))
        elif name in profiles:
            sets.append(OptionSet(name, {**profiles[name], **overrides}))
        else:
            raise SystemExit(f"error: unknown profile {name!r}; known: default, {', '.join(profiles)}")
    if args.extended:
        for name, options in EXTENDED_SETS.items():
            sets.append(OptionSet(name, {**options, **overrides}))
    return sets


def report_failures(title: str, failures: list[tuple[tuple[str, str, str], str]], limit: int) -> None:
    print(f"{title}: {len(failures)}")
    for (option_set, wrapper, variant), errors in failures[:limit]:
        first = errors.splitlines()[0] if errors else "(no error text)"
        print(f"  {wrapper} [{option_set}, {variant}]: {first}")
    if len(failures) > limit:
        print(f"  ... {len(failures) - limit} more (use --verbose to list all)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--glslang", help="path to glslang or glslangValidator")
    parser.add_argument("--profiles", default="default,lowest,low,medium,high,ultra",
                        help="comma-separated option sets: 'default' (settings.glsl) and profile names")
    parser.add_argument("--extended", action="store_true",
                        help="also compile the feature combinations in EXTENDED_SETS")
    parser.add_argument("--set", action="append", default=[], metavar="OPTION[=VALUE]",
                        help="override an option in every set; '!OPTION' disables a boolean (repeatable)")
    parser.add_argument("--worlds", default=",".join(WORLDS), help="comma-separated dimension folders")
    parser.add_argument("--programs", default="", help="comma-separated wrapper filename globs, e.g. 'composite1.*,deferred*'")
    parser.add_argument("--variants", default="voxy",
                        help="LOD variants besides no-LOD for programs that support them: voxy, dh, or 'voxy,dh'")
    parser.add_argument("--vendor", choices=sorted(VENDORS), default="nvidia", help="GL vendor macro to define")
    parser.add_argument("--mc-version", type=int, default=260200, help="MC_VERSION macro (default 260200)")
    parser.add_argument("--extensions", default="KHR_shader_subgroup,KHR_shader_subgroup_arithmetic",
                        help="comma-separated GL extensions reported as MC_GL_<name> macros ('' for none)")
    parser.add_argument("--define", action="append", default=[], metavar="MACRO[=VALUE]",
                        help="add an Iris macro; '!MACRO' removes one (repeatable)")
    parser.add_argument("--baseline", metavar="REV", help="report only programs that compile at REV but fail now")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 4, help="parallel glslang processes")
    parser.add_argument("--keep", metavar="DIR", help="write the expanded sources to DIR")
    parser.add_argument("--verbose", action="store_true", help="list every failure")
    args = parser.parse_args()

    args.profiles = [p for p in args.profiles.split(",") if p]
    args.worlds = [w for w in args.worlds.split(",") if w]
    args.programs = [p for p in args.programs.split(",") if p]
    args.variants = {v for v in args.variants.split(",") if v}
    args.extensions = [e for e in args.extensions.split(",") if e]
    if not args.variants <= {"voxy", "dh"}:
        parser.error("--variants accepts voxy and dh")

    glslang = find_glslang(args.glslang)
    version = subprocess.run([glslang, "--version"], capture_output=True, text=True).stdout.splitlines()
    shaders = ROOT / "shaders"
    profiles = read_profiles((shaders / "shaders.properties").read_text(encoding="utf-8"))
    option_sets = select_option_sets(args, profiles)
    limit = sys.maxsize if args.verbose else 20

    with tempfile.TemporaryDirectory(prefix="lampas-glslang-") as temp:
        temp_path = Path(temp)
        workdir = Path(args.keep) if args.keep else temp_path / "current"
        workdir.mkdir(parents=True, exist_ok=True)
        current, skipped, unique = matrix(shaders, option_sets, args, glslang, workdir)
        failures = sorted((key, errors) for key, (ok, errors) in current.items() if not ok)

        print(f"glslang: {glslang} ({version[0] if version else 'unknown version'})")
        print(f"Option sets: {', '.join(s.name for s in option_sets)}")
        print(f"Compiled {len(current)} program variants ({unique} unique sources); "
              f"{skipped} disabled by program toggles were skipped")

        if args.baseline:
            baseline_dir = temp_path / "baseline"
            baseline_dir.mkdir()
            baseline_shaders = extract_revision(args.baseline, temp_path / "baseline-tree")
            baseline, _, _ = matrix(baseline_shaders, option_sets, args, glslang, baseline_dir)
            regressions = [(key, errors) for key, errors in failures if baseline.get(key, (False, ""))[0]]
            existing = [(key, errors) for key, errors in failures if key not in dict(regressions)]
            fixed = sorted(key for key, (ok, _) in current.items() if ok and key in baseline and not baseline[key][0])
            report_failures(f"Regressions against {args.baseline}", regressions, limit)
            report_failures("Failing at both revisions", existing, limit)
            print(f"Fixed since {args.baseline}: {len(fixed)}")
            status = 1 if regressions else 0
        else:
            report_failures("Failures", failures, limit)
            status = 1 if failures else 0

    print("COMPILE VALIDATION " + ("PASSED" if status == 0 else "FAILED"))
    print("Boundary: standalone glslang semantic check of expanded GLSL 460 compatibility sources; "
          "no Iris transformation, stage linking, or driver compilation.")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
