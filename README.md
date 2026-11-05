# Photon Shader for Lampas Aria

A dedicated [Photon v1.3b](https://github.com/SixthSurge/Photon) shaderpack compatibility derivative specialized for **Lampas Aria** (`lampas:aria`), an open-atmosphere floating island dimension.

---

## Background & Purpose

Unpatched Photon v1.3b under Iris treats `lampas:aria` as generic `world0` (Overworld), leading to critical visual incompatibilities:

1. **Cloud Altitude Conflict**: Upstream Photon places its primary volumetric cumulus cloud deck at $Y \in [183, 303]$ ($Y = 183\text{--}303$). Aria's floating island archipelagos reside at $Y \in [150, 375]$, meaning unpatched clouds directly submerge and envelop the inhabited island terrain.
2. **Under-Island Black Atmospheric Void**: Unpatched Photon derives camera skylight from vertical ceiling clearance (`eyeBrightness.y / 240.0`). Standing underneath any floating island forces `eye_skylight \approx 0.0`. In the upstream analytic atmosphere, atmospheric in-scattering is scaled by `max(skylight, eye_skylight)`. When standing under an island overhang, in-scattering is multiplied by zero, causing the surrounding daytime sky dome and distant island silhouettes against the horizon to collapse into a pitch-black void (`#000000`).
3. **Low-Altitude Cloud Temporal Artifacts**: Re-anchoring clouds to a thin shell at $Y \in [64, 68]$ triggers checkerboard reprojection and history invalidation artifacts in high-ratio temporal upscaling (16×) when crossing cloud boundaries.

This repository provides a dedicated Iris dimension specialization for these defects, alongside shared rendering optimizations, Voxy compatibility fixes, and bug fixes ported from upstream Photon through v1.4. Standard Overworld, Nether, and End dimension routing is retained.

---

## Key Features

- **Dedicated Iris Dimension Routing**:
  - `shaders/dimension.properties` maps `lampas:aria` exclusively to its own Iris shader dimension folder `aria`.
  - Retains explicit vanilla mappings (`minecraft:overworld`, `minecraft:the_nether`, `minecraft:the_end`) and wildcard fallback routing on `world0`.

- **Aria Program Wrappers & Property Parity**:
  - 118 shader wrappers under `shaders/aria/` mirroring `shaders/world0/`.
  - Wrappers inject `#define WORLD_ARIA` alongside `#define WORLD_OVERWORLD`, allowing existing Overworld rendering passes to run while enabling targeted `#ifdef WORLD_ARIA` branches.
  - All 23 `program.world0/...` toggles in `shaders/shaders.properties` are mirrored for `program.aria/...` (Depth of Field, Bloom, TAAU, Motion Blur, FXAA, Intel fixes, colored lights, etc.).

- **Anchored Volumetric Cloud Ocean ($Y \in [64, 68]$)**:
  - Centralized in `shaders/include/sky/clouds/constants.glsl`:
    - Base altitude: $Y = 64.0$ (matching Aria's configured `cloud_height = 64.0`).
    - Thickness: $4.0$ blocks ($Y = 64\text{--}68$).
  - Leaves the entire floating island stratum ($Y \in [150, 375]$) completely clear of dense cumulus volume while establishing a picturesque cloud sea beneath the island archipelagos.

- **Atmospheric Scattering Decoupled from Roof Occlusion**:
  - In `shaders/include/fog/overworld/analytic.glsl`, decouples large-scale atmospheric scattering from local camera roof skylight under `#ifdef WORLD_ARIA`.
  - Looking out from beneath an island overhang preserves full daylight sky scattering and natural distant silhouettes, while keeping local underside terrain surfaces realistically shadowed.

- **Hardened Cloud Temporal Upscaling**:
  - In `shaders/program/d2_clouds_upscaling.fsh`, detects cloud presence transitions to prevent checkerboard artifacts across pixel boundaries during temporal accumulation.

- **Voxy LOD Depth Compatibility**:
  - Configured `voxy.json` with `excludeLodsFromVanillaDepth: false` to ensure seamless depth integration between Voxy LOD terrain and block entities.

- **Profiles**:
  - **Lowest**, **Low**, **Medium**, **High** (default) and **Ultra**.
  - **Lowest** targets integrated and GTX 1050-class GPUs: no sun shadows, TAAU at 0.67 render scale, fewer cloud layers and march steps, and no cloud shadows.
  - Low/Medium/High/Ultra select None/SSAO/GTAO/GTAO for shader ambient occlusion. Entity shadows are on only in Ultra.
  - Every profile lists the full set of options it controls, so switching profiles never leaves another profile's values behind.

- **Performance Improvements**:
  - Aria skips fully faded cloud shadows, empty cloud/fog marches, and temporal AO filtering when shader AO is disabled.
  - Bloom uses five filtered samples in tile interiors while preserving its original edge filter. LPV colored lighting skips neighbor reads for voxels with zero light transmission.
  - The opaque shadow pass casts without a texture read or `discard`, so the GPU can reject hidden fragments early. With colored shadows off (Low, Medium), shadow-color work and the per-frame `shadowcolor0` clear are skipped.
  - Work that cannot change the image is skipped: empty cloud layers, crepuscular rays at zero strength, volumetric-light shadow reads outside the shadow map, invisible stars, FXAA corner reads on non-edge pixels, rain puddles on surfaces that cannot hold them, and cloud reads in the blend pass for opaque pixels.
  - Frame-uniform work (exposure, vignette, fog phase functions, shadow-filter disc rotation) is computed once instead of per pixel or per step.
  - **Water → Water Waves → Distant Water Detail** optionally fades water surface detail and screen-space reflections with distance. The default **Off** preserves full detail. Selecting a distance retains full detail through half that distance, then fades to flat surface normals and sky reflections; at the selected distance, procedural normal/parallax and water reflection ray work is skipped. This trades distant visual detail for less shading work and applies consistently to regular water and the composite Voxy/DH water path.
  - **Visible change:** with Minecraft's **Cutout Leaves** option off, leaves are drawn opaque and now also cast solid shadows instead of holey ones.
  - Standalone shader compilation and targeted source/numerical checks are recorded in `PROGRESS.md`. Performance gains have not been measured in a live client.

- **Bug Fixes Beyond Upstream**:
  - Out-of-bounds reads and writes: the auto-exposure histogram, Voxy material IDs below 10000, shadow-pass material IDs for unmapped blocks, and underwater volumetric light outside the shadow map.
  - Uninitialized values in the vanilla-sun halo cut-out (now atlas-aware for Minecraft 26.1+) and in water parallax.
  - Cloud upscaling: contiguous 4×4 depth footprints and the correct history channel on disocclusion.
  - Screen-space shadows jitter their rays without LOD mods, as they already did with Voxy/DH.
  - Bloomy fog without volumetric light follows the analytic fog.
  - **Fog → VL Render Scale** works and is in the menu, with values from 0.25 to 0.50 (default 0.50). Lower values render volumetric fog at a smaller resolution. Upstream's values above 0.5 sampled the wrong part of the screen.

---

## Installation

### Prerequisites

- **Minecraft**: 26.2
- **Mod Loader**: Fabric Loader
- **Shader Loader**: [Iris Shaders](https://irisshaders.dev/) 1.11.4 with Sodium 0.9.2
- **Dimension Mod**: Lampas Aria (`lampas:aria`)
- **Optional**: Voxy 0.2.19 for LOD terrain. Voxy currently needs lampas2-overrides 1.0.6 or later, which converts its projection to the forward-Z depth this pack expects; without it, LOD terrain draws into the sky.

### Adding to Minecraft

1. Download the latest `lampas-photon-aria.zip` from [Releases](https://github.com/justbecauseph/lampas-photon-aria-shader/releases).
2. Place the `.zip` file into your `.minecraft/shaderpacks/` folder (or your modpack's `shaderpacks/` directory).
3. In Minecraft, open **Options** $\to$ **Video Settings** $\to$ **Shader Packs**.
4. Select **lampas-photon-aria** and click **Apply**.

### Development / Symlink Setup

For active shader development, link the repository into your `shaderpacks/` directory with a directory junction. Iris reads the working tree directly, so press **R** in game to reload after an edit.

```powershell
New-Item -ItemType Junction -Path "$env:APPDATA\.minecraft\shaderpacks\lampas-photon-aria-dev" -Target "C:\path\to\lampas-photon-aria-shader"
```

For the Lampas launcher, the `shaderpacks/` directory is `%LOCALAPPDATA%\Packages\59450PUPProgGuild.LampasLauncher_bdagfy06snw12\LocalCache\.minecraft-lampas\shaderpacks`. Deleting the junction removes only the link, not the repository.

---

## Development & CI/CD

### Workflow

Work is planned in phases. [`AGENTS.md`](AGENTS.md) sets the rules: define scope and acceptance criteria first, record progress in [`PROGRESS.md`](PROGRESS.md), run the validators below before every commit that touches `shaders/` or `tools/`, and commit and push at the end of each phase for review. [`PLAN.md`](PLAN.md) holds the current plan.

### Validation

The validators in `tools/` need only Python 3.12+; the compile check also needs [glslang](https://github.com/KhronosGroup/glslang).

| Command | Checks |
|---|---|
| `python tools/validate_wrappers.py` | Wrapper parity, directive placement, include targets, and `program.aria` toggle symmetry |
| `python tools/validate_profiles.py` | Profile tokens, option values, profile includes, and menu entries in `shaders.properties` |
| `python tools/validate_perf1.py` | PERF1 fast-path contracts and non-Aria source parity against the pre-PERF1 baseline (needs git history) |
| `python tools/validate_compile.py` | Compiles every program with glslang |

`validate_compile.py`:

- **Matrix:** it compiles every program in `world0`, `aria`, `world-1` and `world1`, for the `settings.glsl` defaults and each profile, without LOD mods plus Voxy or Distant Horizons variants where a program supports them.
- **Skips** programs the option set disables (`program.<world>/<name>.enabled`).
- **Macros:** it injects Iris's standard macros for Minecraft 26.2.
- **Finding glslang:** `--glslang`, the `GLSLANG` environment variable, `PATH`, or `~/.local/bin`.
- **Limits:** this is a standalone GLSL check (sources are compiled as `460 compatibility`). It does not run Iris's shader transformer, link program stages, or test a GPU driver. The Voxy patch files are not compiled.

```bash
python tools/validate_compile.py                       # defaults and every profile (~1 min)
python tools/validate_compile.py --extended            # plus feature combinations no profile selects
python tools/validate_compile.py --baseline HEAD       # only report programs that compiled at HEAD
python tools/validate_compile.py --programs "composite1.*" --profiles low --set BLOOMY_FOG --set '!VL'
```

### Packaging & Releases

Releases are automated via GitHub Actions ([`.github/workflows/release.yml`](.github/workflows/release.yml)):
- Triggers on tag pushes (`v*`, `[0-9]+*`) or via manual `workflow_dispatch`.
- Runs `tools/validate_wrappers.py` before building.
- Packages canonical shaderpack roots (`shaders/` and `LICENSE`) into `lampas-photon-aria-<tag>.zip` and `lampas-photon-aria.zip`.
- Publishes assets to GitHub Releases and workflow artifacts.

---

## License & Attribution

- Based on [Photon Shader](https://github.com/SixthSurge/Photon) by **SixthSurge**, licensed under the **GNU Lesser General Public License v3.0 (LGPL-3.0)**.
- See [`LICENSE`](LICENSE) for complete license details.
