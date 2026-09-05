# Photon Shader for Lampas Aria

A dedicated [Photon v1.3b](https://github.com/SixthSurge/Photon) shaderpack compatibility derivative specialized for **Lampas Aria** (`lampas:aria`), an open-atmosphere floating island dimension.

---

## Background & Purpose

Unpatched Photon v1.3b under Iris treats `lampas:aria` as generic `world0` (Overworld), leading to critical visual incompatibilities:

1. **Cloud Altitude Conflict**: Upstream Photon places its primary volumetric cumulus cloud deck at $Y \in [183, 303]$ ($Y = 183\text{--}303$). Aria's floating island archipelagos reside at $Y \in [150, 375]$, meaning unpatched clouds directly submerge and envelop the inhabited island terrain.
2. **Under-Island Black Atmospheric Void**: Unpatched Photon derives camera skylight from vertical ceiling clearance (`eyeBrightness.y / 240.0`). Standing underneath any floating island forces `eye_skylight \approx 0.0`. In the upstream analytic atmosphere, atmospheric in-scattering is scaled by `max(skylight, eye_skylight)`. When standing under an island overhang, in-scattering is multiplied by zero, causing the surrounding daytime sky dome and distant island silhouettes against the horizon to collapse into a pitch-black void (`#000000`).
3. **Low-Altitude Cloud Temporal Artifacts**: Re-anchoring clouds to a thin shell at $Y \in [64, 68]$ triggers checkerboard reprojection and history invalidation artifacts in high-ratio temporal upscaling (16×) when crossing cloud boundaries.

This repository provides a dedicated Iris dimension specialization that resolves these defects while leaving 100% of standard Overworld, Nether, and End rendering pipelines untouched.

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

- **Zero Upstream Regression**:
  - Upstream files in `shaders/world0/`, `shaders/program/`, and `shaders/include/` retain identical `#else` logic matching stock Photon v1.3b.

---

## Installation

### Prerequisites

- **Minecraft**: 1.21.x
- **Mod Loader**: Fabric Loader
- **Shader Loader**: [Iris Shaders](https://irisshaders.dev/) (v1.11.2+)
- **Dimension Mod**: Lampas Aria (`lampas:aria`)

### Adding to Minecraft

1. Download the latest `lampas-photon-aria.zip` from [Releases](https://github.com/justbecauseph/lampas-photon-aria-shader/releases).
2. Place the `.zip` file into your `.minecraft/shaderpacks/` folder (or your modpack's `shaderpacks/` directory).
3. In Minecraft, open **Options** $\to$ **Video Settings** $\to$ **Shader Packs**.
4. Select **lampas-photon-aria** and click **Apply**.

### Development / Symlink Setup

For active shader development, create a directory junction directly into your `.minecraft/shaderpacks/` directory:

```powershell
cmd /c mklink /J "$env:APPDATA\.minecraft\shaderpacks\lampas-photon-aria" "C:\path\to\lampas-photon-aria-shader"
```

---

## Development & CI/CD

### Structural Validation

An automated validation script verifies wrapper parity, directive placement, include target resolution, and `shaders.properties` toggle symmetry:

```bash
python tools/validate_wrappers.py
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
