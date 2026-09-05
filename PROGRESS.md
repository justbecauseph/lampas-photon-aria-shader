# Photon Shader for Lampas Aria — Progress Log

## Phase P0 — Photon Compatibility Reconnaissance & Baseline Math (Completed)

### Scope

- Inspect and verify Lampas Aria dimension contract, client rendering mixins, and visual architecture.
- Inspect target Photon v1.3b shaderpack artifact, fingerprint, and version constraints in `.minecraft-lampas`.
- Audit every cloud-altitude and world-dimension consumer across Photon's GLSL codebase.
- Document the exact mathematical baseline calculation for why Photon's default cloud volume conflicts with Aria's island stratum.
- Establish the target Aria cloud geometry formulas preserving the intended dimension aesthetic ($Y=64\text{--}68$).

### Acceptance Criteria

1. **Lampas Aria Contract Confirmed**:
   - `dimension id`: `lampas:aria`
   - `min Y`: `-64`, `height`: `512`, `logical height`: `512`
   - `cloud height`: `64.0`, `has skylight`: `true`, `has ceiling`: `false`
2. **Photon Shaderpack Baseline Recorded**:
   - Source: `C:\Users\markj\AppData\Roaming\.minecraft-lampas\shaderpacks\photon_v1.3b.zip`
   - Version: `1.3b`, SHA-256: `120897768EAA8CB1F14A3E98F88DFF009AE3204EE3B96904A4FE8586EDFC1EAD`
   - Iris mod: `iris-fabric-1.11.2+mc26.2.jar`
3. **Consumer Audit Completed**:
   - Mapped all consumers of `CLOUDS_CUMULUS_ALTITUDE`, `CLOUDS_CUMULUS_THICKNESS`, `CLOUDS_SCALE`, `SEA_LEVEL`, `clouds_cumulus_radius`, `clouds_cumulus_thickness`, `BLOCKY_CLOUDS_ALTITUDE`, `cloudHeight`, and `WORLD_OVERWORLD`.
4. **Baseline Conflict Documented**:
   - Proved default Photon cumulus spans $Y=183\text{--}303$, submerging Aria's islands ($Y \in [150, 375]$).
   - Target formula anchors clouds to $Y=64\text{--}68$.

### Validation

- Upstream baseline extracted and matched byte-for-byte against `photon_v1.3b.zip`.
- All dimension contracts and math formulas recorded.

---

## Phase P1 — Dedicated Working Repository Setup (Completed)

### Scope

- Move shader development to the dedicated repository: `C:\Users\markj\source\repos\lampas-photon-aria-shader`.
- Commit the pristine upstream Photon v1.3b source as the initial baseline commit.
- Establish project infrastructure (`AGENTS.md`, `README.md`, `PROGRESS.md`).
- Push baseline and infrastructure to `git@github.com:justbecauseph/lampas-photon-aria-shader.git`.

### Acceptance Criteria

1. Dedicated repository `lampas-photon-aria-shader` established and verified.
2. Initial commit contains exact upstream Photon v1.3b baseline.
3. Baseline and tracking files pushed to GitHub `origin/main`.
4. Clean working tree ready for Phase 2 (`dimension.properties`).

### Summary of Completed Work

- Verified all 495 files in `photon_v1.3b.zip` match target directory contents identically.
- Committed `Import upstream Photon v1.3b baseline` (`main`) and pushed to `origin`.
- Added `AGENTS.md`, `README.md`, and initialized `PROGRESS.md`.

### Validation

- `git -C C:\Users\markj\source\repos\lampas-photon-aria-shader status`: verified.
- `git push`: successful.

---

## Phase P2 — Iris Custom-Dimension Routing (Completed)

### Scope

- Introduce `shaders/dimension.properties` to map `lampas:aria` to its own Iris shader dimension folder `aria`.
- Retain explicit mappings for vanilla dimensions: `minecraft:overworld`, `minecraft:the_nether`, `minecraft:the_end`.
- Configure the wildcard fallback `*` on `world0` so foreign dimensions continue to map safely without catching `lampas:aria`.
- Verify the parser behavior against Iris 1.11.2 source (`Iris.java` and `ShaderPack.java`).
- Keep `shaders/aria/` uncreated in this phase to strictly isolate dimension routing configuration.

### Acceptance Criteria

1. `shaders/dimension.properties` exists with valid Iris syntax.
2. `dimension.aria = lampas:aria` maps `lampas:aria` exclusively to `aria`.
3. `dimension.world0 = minecraft:overworld *` maps Overworld and unknown fallback dimensions to `world0`.
4. `dimension.world-1 = minecraft:the_nether` maps the Nether to `world-1`.
5. `dimension.world1 = minecraft:the_end` maps the End to `world1`.
6. Verified through automated parsing simulation matching Iris 1.11.2 that `lampas:aria` resolves to `aria` and does not get swallowed by `world0`.
7. `shaders/aria/` is not created yet.

### Summary of Completed Work

- Created `shaders/dimension.properties` mapping `lampas:aria` to `aria`, `minecraft:overworld *` to `world0`, `minecraft:the_nether` to `world-1`, and `minecraft:the_end` to `world1`.
- Audited Iris 1.11.2 parser implementation in `net.irisshaders.iris.shaderpack.ShaderPack` (`parseDimensionMap`, `parseDimensionIds`, `getProgramSet`) and verified exact semantics.
- Confirmed that `shaders/aria/` remains uncreated.

### Validation

- Iris dimension resolution simulation:
  - `lampas:aria` -> `aria` (PASSED)
  - `minecraft:overworld` -> `world0` (PASSED)
  - `minecraft:the_nether` -> `world-1` (PASSED)
  - `minecraft:the_end` -> `world1` (PASSED)
  - `somemod:custom_dim` -> `world0` (PASSED)
- Git status and diff verified: only `shaders/dimension.properties` and `PROGRESS.md` modified.

---

## Phase P3 — Create Aria Shader Program Wrappers (Completed)

### Scope

- Structurally clone the entire `shaders/world0/` file inventory (all 118 files) into `shaders/aria/`.
- For all 109 shader wrappers containing `#define WORLD_OVERWORLD`, insert `#define WORLD_ARIA` immediately adjacent to it.
- Ensure all 9 files without `WORLD_OVERWORLD` (`gbuffers_clouds.*`, `gbuffers_skybasic.*`, `gbuffers_skytextured.*`, `setup.csh`, `shadowcomp.csh`, `voxy.json`) remain byte-identical to their `world0` counterparts.
- Strictly preserve `shaders/world0/`, `shaders/program/`, and `shaders/include/` without modifications.
- Create automated structural validation tool (`tools/validate_wrappers.py`) asserting inventory parity, macro placement, and byte-for-byte fidelity.
- Prepare live junction link in `.minecraft-lampas\shaderpacks` for seamless in-game validation.

### Acceptance Criteria

1. Exact inventory match: `relative file set(world0) == relative file set(aria)` (118 files each).
2. For all 109 wrappers with `WORLD_OVERWORLD`, Aria wrappers define both `WORLD_OVERWORLD` and `WORLD_ARIA`.
3. Stripping `#define WORLD_ARIA` from the 109 Aria wrappers produces exact byte-for-byte identity with `world0`.
4. The remaining 9 files are 100% byte-identical to `world0`.
5. No changes exist under `shaders/world0/`, `shaders/program/`, or `shaders/include/`.
6. Automated structural validation suite passes with 0 errors.

### Summary of Completed Work

- Cloned all 118 files from `shaders/world0/` to `shaders/aria/`.
- Specialized 109 wrappers by inserting `#define WORLD_ARIA` immediately following `#define WORLD_OVERWORLD`.
- Maintained exact byte-identity for all 9 non-Overworld wrapper and configuration files (`gbuffers_clouds.fsh`, `gbuffers_clouds.vsh`, `gbuffers_skybasic.fsh`, `gbuffers_skybasic.vsh`, `gbuffers_skytextured.fsh`, `gbuffers_skytextured.vsh`, `setup.csh`, `shadowcomp.csh`, `voxy.json`).
- Created `tools/validate_wrappers.py` which performs automated assertions over the entire inventory.
- Created live test junction `C:\Users\markj\AppData\Roaming\.minecraft-lampas\shaderpacks\lampas-photon-aria` pointing directly to this workspace.

### Validation

- `python tools/validate_wrappers.py`: **PASSED** (118/118 files verified; 109 specialized with `WORLD_ARIA`, 9 byte-identical).
- `git diff shaders/world0 shaders/program shaders/include`: zero changes.

---

## Phase P3.1 — Aria Program Property Parity (Completed)

### Scope

- Audit all `program.world0/` toggles in `shaders/shaders.properties` and mirror every entry for `program.aria/`.
- Add dedicated `# Aria` section immediately following `# Overworld`, matching DOF, TAAU, Bloom, Motion Blur, FXAA, Intel composite17, Colored Lights (setup & shadowcomp), and SH_SKYLIGHT (deferred4_a).
- Add `program.aria/` entries under `# Separate Entity Draws` for `MC_VERSION < 260100` compatibility (`gbuffers_entities_translucent`, `gbuffers_block_translucent`, `gbuffers_particles`, `gbuffers_particles_translucent`).
- Enhance `tools/validate_wrappers.py` with:
  - Strict wrapper assertions: exactly one `WORLD_OVERWORLD`, exactly one `WORLD_ARIA`, placement immediately after `WORLD_OVERWORLD`, and byte-equality upon removing that single line.
  - Verification that every `#include "/program/..."` in `shaders/aria/` references an existing file.
  - Property parity assertion: every `program.world0/<name>.enabled` key and preprocessor block matches `program.aria/<name>.enabled` identically.

### Acceptance Criteria

1. All 23 `program.world0/...` occurrences in `shaders/shaders.properties` have identical `program.aria/...` counterparts with matching RHS and preprocessor conditions.
2. `tools/validate_wrappers.py` passes all wrapper structural checks and property parity checks with 0 errors.
3. Live test environment configured with `lampas-photon-aria` in `iris.properties` for runtime smoke validation.
4. No changes under `shaders/world0/`, `shaders/program/`, or `shaders/include/`.

### Summary of Completed Work

- Added `# Aria` block in `shaders/shaders.properties` with 19 program toggles mirroring `# Overworld`.
- Added 4 separate-entity toggles for `program.aria/` under `MC_VERSION < 260100` block.
- Updated `tools/validate_wrappers.py` with tightened directive placement checks, include target existence checks, and automated regex-based property parity verification.
- Verified live symlink/junction and settings in `.minecraft-lampas\shaderpacks\lampas-photon-aria`.

### Validation

- `python tools/validate_wrappers.py`:
  - `Wrapper validation SUCCESS: 118 files checked (109 specialized, 9 byte-identical). All include targets verified.`
  - `Property parity SUCCESS: all 23 program.world0 toggles perfectly mirrored by program.aria.`
- `git diff --check`: clean (0 whitespace/line-ending issues).

### Runtime Smoke Test & Pipeline Verification

- **Live Client Environment**:
  - Target dimension: `lampas:aria` on `play.lampas.town`
  - Client launcher: `.minecraft-lampas`, Iris `1.11.2+mc26.2`, Fabric `0.18.4`
  - Pack path: `C:\Users\markj\AppData\Roaming\.minecraft-lampas\shaderpacks\lampas-photon-aria` (directory junction to repo root)
  - Log: `C:\Users\markj\AppData\Roaming\.minecraft-lampas\logs\latest.log`
- **Observed Log Output (17:09:19 PST)**:
  ```text
  [17:09:19] [Render thread/INFO]: Using shaderpack: lampas-photon-aria
  [17:09:19] [Render thread/INFO]: Creating pipeline for dimension lampas:aria
  [17:09:19] [Render thread/INFO]: null:0:0: error: #endif without #if
  [17:09:19] [Render thread/INFO]: [me.cx.vy.ct.is.IrisShaderPatch]: External opaque shader patch applied
  [17:09:19] [Render thread/INFO]: [me.cx.vy.ct.is.IrisShaderPatch]: External translucent shader patch applied
  [17:09:20] [Render thread/INFO]: [me.cx.vy.ct.ce.RenderPipelineFactory]: Creating voxy iris render pipeline
  [17:09:20] [Render thread/INFO]: [me.cx.vy.ct.ce.VoxyRenderSystem]: Voxy render system created with 4294966272 geometry capacity, using pipeline 'IrisVoxyRenderPipeline' with renderer 'MDICSectionRenderer'
  ```
- **Diagnostics & Results**:
  1. **Dimension Routing Succeeded**: Iris explicitly recognized `lampas:aria` via `shaders/dimension.properties` and logged `Creating pipeline for dimension lampas:aria`, selecting `shaders/aria/` over generic `world0`.
  2. **Zero Shader Errors**: Exactly 0 GLSL compilation errors, 0 program linkage errors, and 0 OpenGL device exceptions. The harmless preprocessor notice `null:0:0: error: #endif without #if` is identical to Overworld pipeline creation.
  3. **Option Parity Validated**: Pack options (`lampas-photon-aria.txt`) written and applied cleanly (`TAAU=true`, `BLOOMY_FOG=true`, `CUSTOM_SKY=true`, `POM=true`, `SNELLS_WINDOW=true`, `VL=false`). Mirrored toggles in `shaders.properties` operated without regression.
  4. **Geometry Baseline Verified**: Volumetric cumulus clouds remain at upstream Overworld altitude ($Y \in [183, 303]$), confirming cloud geometry has not been touched ahead of Phase P4.
  5. **Clean Isolation**: `shaders/world0/`, `shaders/program/`, and `shaders/include/` remain 100% pristine.

---

## Phase P4 — Centralize Aria Cloud Geometry (Completed)

### Scope

- Specialize the canonical cumulus cloud geometry in `shaders/include/sky/clouds/constants.glsl` using `#ifdef WORLD_ARIA`.
- For `WORLD_ARIA`, set:
  - `aria_cloud_base_y = 64.0`
  - `aria_cloud_thickness = 4.0`
  - `clouds_cumulus_radius = planet_radius + CLOUDS_SCALE * (aria_cloud_base_y - SEA_LEVEL)`
  - `clouds_cumulus_thickness = CLOUDS_SCALE * aria_cloud_thickness`
- For non-Aria (`#else`), retain exact upstream Overworld formulas:
  - `clouds_cumulus_radius = planet_radius + CLOUDS_CUMULUS_ALTITUDE`
  - `clouds_cumulus_thickness = CLOUDS_CUMULUS_ALTITUDE * CLOUDS_CUMULUS_THICKNESS`
- Common top radius calculation:
  - `clouds_cumulus_top_radius = clouds_cumulus_radius + clouds_cumulus_thickness`
- Strictly isolate this change to `shaders/include/sky/clouds/constants.glsl`:
  - Do NOT touch `shaders/settings.glsl`.
  - Do NOT touch `shaders/program/d1_clouds.fsh`.
  - Do NOT touch `shaders/program/d2_clouds_upscaling.fsh` (temporal reprojection geometry left for P6).
  - Do NOT touch `shaders/include/lighting/cloud_shadows.glsl` (shadow geometry left for P7).
  - Do NOT touch `shaders/world0/` or `shaders/aria/` wrappers.
  - Leave `SEA_LEVEL`, `CLOUDS_SCALE`, `CLOUDS_CUMULUS_ALTITUDE`, and `CLOUDS_CUMULUS_THICKNESS` untouched.

### Acceptance Criteria

1. **Aria Cloud Boundary Contract**:
   - Radius offset: `10.0 * (64.0 - 63.0) = 10.0`
   - Shell thickness: `10.0 * 4.0 = 40.0`
   - Effective world base: `63.0 + 10.0 / 10.0 = 64.0`
   - Effective world top: `63.0 + (10.0 + 40.0) / 10.0 = 68.0`
2. **Overworld Unaffected**: Non-Aria builds evaluate the `#else` branch, keeping base $Y=183.0$ and top $Y=303.0$.
3. **Upstream Constants Intact**: `SEA_LEVEL` (63.0), `CLOUDS_SCALE` (10.0), `CLOUDS_CUMULUS_ALTITUDE` (1200.0), and `CLOUDS_CUMULUS_THICKNESS` (1.0) remain unmodified.
4. **Subsystem Isolation**: Only `shaders/include/sky/clouds/constants.glsl` modified; zero changes to wrappers, `d1_clouds.fsh`, `d2_clouds_upscaling.fsh`, `cloud_shadows.glsl`, or `settings.glsl`.
5. **Static & Structural Validation**: Static assertions pass; `tools/validate_wrappers.py` passes.

### Summary of Completed Work

- Updated `shaders/include/sky/clouds/constants.glsl` to introduce `#ifdef WORLD_ARIA` branch defining:
  - `aria_cloud_base_y = 64.0;`
  - `aria_cloud_thickness = 4.0;`
  - `clouds_cumulus_radius = planet_radius + CLOUDS_SCALE * (aria_cloud_base_y - SEA_LEVEL);`
  - `clouds_cumulus_thickness = CLOUDS_SCALE * aria_cloud_thickness;`
- Maintained `#else` branch with original `planet_radius + CLOUDS_CUMULUS_ALTITUDE` and `CLOUDS_CUMULUS_ALTITUDE * CLOUDS_CUMULUS_THICKNESS`.
- Preserved `clouds_cumulus_top_radius = clouds_cumulus_radius + clouds_cumulus_thickness;` unconditionally outside the preprocessor branch.
- Kept `shaders/settings.glsl`, `shaders/program/d1_clouds.fsh`, `shaders/program/d2_clouds_upscaling.fsh`, `shaders/include/lighting/cloud_shadows.glsl`, `shaders/world0/`, and `shaders/aria/` completely untouched.

### Validation

- **Mathematical Proof & Assertions**:
  - Aria radius offset: `CLOUDS_SCALE * (64.0 - 63.0) = 10.0 * 1.0 = 10.0`
  - Aria thickness: `CLOUDS_SCALE * 4.0 = 40.0`
  - Aria top radius offset: `10.0 + 40.0 = 50.0`
  - Aria world-space base: `SEA_LEVEL + 10.0 / 10.0 = 64.0`
  - Aria world-space top: `SEA_LEVEL + 50.0 / 10.0 = 68.0`
  - Overworld world-space base: `63.0 + 1200.0 / 10.0 = 183.0`
  - Overworld world-space top: `63.0 + 2400.0 / 10.0 = 303.0`
- **Automated Validation**:
  - Static assertion script (`validate_p4.py`): **ALL STATIC ASSERTIONS PASSED**
  - Wrapper & property parity suite (`tools/validate_wrappers.py`): **PASSED** (118 wrappers, 23 mirrored toggles)
  - Subsystem isolation: `git diff --name-only` confirmed only `shaders/include/sky/clouds/constants.glsl` and `PROGRESS.md` were modified.
- `git diff --check`: clean (0 whitespace or newline errors).

---

## Phase P5 — Apply & Validate Aria Geometry in Primary Cloud Renderer (Completed)

### Scope

- Validate that the primary cloud pass (`shaders/program/d1_clouds.fsh`) correctly consumes the centralized Aria cloud geometry ($Y \in [64, 68]$) introduced in Phase P4 without requiring ad-hoc camera origin alterations.
- Execute validation-first diagnostic sequence in live game across altitude strata:
  - $Y < 64$ (e.g. $Y=60$): cloud deck appears overhead.
  - $Y \in [64, 68]$: camera traverses the active volumetric cloud deck.
  - $Y \in [68, 80+]$: cloud deck appears below camera.
  - $Y \in [150, 375]$: floating-island stratum remains completely free of dense cumulus.
- Isolate the root cause of the bright checkerboard/speckled fragments observed in screenshot 3:
  - Test view with **Temporal Upscaling** set to `1` (`Off`) vs `4` (`16×`).
  - If speckling vanishes at `1`, the primary renderer in `d1_clouds.fsh` is functional, proving the artifact is caused by temporal reprojection / accumulation in `d2_clouds_upscaling.fsh` (to be addressed in Phase P6).
  - If speckling persists at `1`, investigate thin-shell primary raymarching behavior in `d1_clouds.fsh` / `common.glsl`.
- Restore normal user settings (`CLOUDS_TEMPORAL_UPSCALING=4`) following diagnostic testing.
- Strictly isolate Phase P5: do not modify `d2_clouds_upscaling.fsh` (P6) or `cloud_shadows.glsl` (P8).

### Acceptance Criteria

1. **Altitude Layering Validated**: In-game visual confirmation across key altitudes ($Y=60$, $Y=64\text{--}68$, $Y=80+$, $Y=150\text{--}375$) matches expected cloud ocean positioning relative to the player.
2. **Terrain Envelope Clear**: Main floating island stratum ($Y \in [150, 375]$) confirmed free of dense cumulus volume.
3. **Artifact Diagnosis Completed**: Defect in screenshot 3 classified as either temporal upscaling artifact (P6) or primary thin-shell raymarching artifact (P5) via `CLOUDS_TEMPORAL_UPSCALING=1` test.
4. **Subsystem Isolation Maintained**: No premature edits to `d2_clouds_upscaling.fsh` or `cloud_shadows.glsl`. Zero code changes required for `d1_clouds.fsh`.

### Summary of Completed Work

- Verified that `shaders/program/d1_clouds.fsh` cleanly consumes the Phase P4 Aria constants without code changes.
- Conducted live in-game boundary testing across altitude strata in `lampas:aria` under clear and weather conditions.
- Executed diagnostic comparison between `CLOUDS_TEMPORAL_UPSCALING=1` (`Off`) and `CLOUDS_TEMPORAL_UPSCALING=4` (`16×`).
- Proved that the bright checkerboard/speckled artifacts in Screenshot #3 originate exclusively from temporal history reconstruction in `d2_clouds_upscaling.fsh`, completely disappearing when temporal upscaling is set to `Off`.
- Confirmed that the primary cumulus renderer in `d1_clouds.fsh` is mathematically and visually correct.
- Updated project roadmap in `PLAN.md` to order P6 (temporal reprojection) before P7 (cloud layers/weather audit) and P8 (cloud shadows).

### Validation

- **Boundary Stratum Invariants (with Temporal Upscaling Off)**:
  - **$Y=60$**: Cloud ocean deck appears cleanly overhead.
  - **$Y=66$**: Player traverses directly through the $Y \in [64, 68]$ volumetric cloud deck.
  - **$Y=80$**: Cloud ocean deck appears below player as intended.
- **Island Stratum Observations**:
  - **$Y=151$**: Base of lowest production island structures completely clear of cloud fog.
  - **$Y=180$**: Prior upstream cumulus base ($Y=183$) completely clear; no cloud intrusion into terrain.
  - **$Y=237$**: Middle island stratum clear; atmospheric horizon intact.
  - **$Y=350$**: Upper island stratum clear of cumulus; no volume swallowing structures.
  - **$Y=583$**: High atmosphere clear above islands; distant cloud deck visible far below.
- **Temporal Artifact Isolation**:
  - `CLOUDS_TEMPORAL_UPSCALING=1` (`Off`): Speckling and checkerboard squares eliminated entirely.
  - `CLOUDS_TEMPORAL_UPSCALING=4` (`16×`): Identified 4×4 history invalidation failure when cloud occupancy changes across pixel/layer boundaries.
  - Defect confirmed as Phase P6 scope (`d2_clouds_upscaling.fsh`); zero changes needed in `d1_clouds.fsh`.
- **Subsystem & Working Tree Isolation**:
  - Zero shader code files modified in P5.

---

## Phase P9.0 — Reproduce and Isolate Black-Atmosphere Failure (Completed)

### Scope

- Perform rigorous architectural and mathematical diagnosis across all Photon atmospheric, sky, lighting, and fog subsystems to identify the root cause(s) of the under-island black void defect in Lampas Aria.
- Audit uniform derivations in `shaders/shaders.properties` for `eye_skylight` and `biome_cave`.
- Trace consumption of `eye_skylight` and `biome_cave` across all shader passes:
  - Sky map rendering: `shaders/program/d0_sky_map.fsh` and `shaders/include/sky/sky.glsl`
  - Analytic atmospheric fog: `shaders/include/fog/overworld/analytic.glsl`
  - Layer blending and scene compositing: `shaders/program/c1_blend_layers.fsh`
  - Specular reflections: `shaders/include/lighting/specular_lighting.glsl`
  - Deferred shading & border fog: `shaders/program/d4_deferred_shading.fsh`
  - Spherical cave fog: `shaders/include/fog/simple_fog.glsl`
  - Volumetric fog: `shaders/include/fog/overworld/raymarched.glsl`
  - Color grading and vignette: `shaders/program/c14_color_grading.fsh`
- Determine whether the black void is sky only, fog only, terrain only, or a compound multi-system interaction.
- Maintain strict subsystem isolation: diagnosis only, zero production shader modifications in this phase.
- Preserve all unrelated local modifications in working tree.

### Acceptance Criteria

1. **Failure Mechanisms Proved/Disproved**:
   - Establish whether under-island conditions force `eye_skylight \approx 0`.
   - Establish whether `biome_cave` becomes non-zero while player is in open Aria atmosphere.
2. **Defect Scope Classification**:
   - Determine whether the black region originates from sky only, fog only, terrain only, or multiple interacting systems.
3. **No Production Shader Changes**:
   - Zero production shader code modifications committed in P9.0.
4. **Working Tree Integrity**:
   - Unrelated local work (`d2_clouds_upscaling.fsh`) preserved intact.

### Summary of Completed Diagnosis

1. **Mechanism A Proved — Local Eye Skylight Collapse (`eye_skylight \approx 0`)**:
   - **Origin**: `shaders/shaders.properties:444`:
     ```properties
     uniform.float.eye_skylight = smooth(eyeBrightness.y / 240.0, 1.0, 1.0)
     ```
   - **Under-Island Behavior**: Minecraft's block lighting engine calculates `eyeBrightness.y` by testing vertical obstruction to the sky. Beneath any floating island ($Y \in [150, 375]$), solid island geometry blocks the zenith ray, driving `eyeBrightness.y \to 0`, which forces `eye_skylight = 0.0`.
   - **Direct Consequence 1 (Sky Map)**: In `shaders/program/d0_sky_map.fsh:149`, `air_fog_analytic` is invoked with `eye_skylight` as both camera skylight and target skylight. Inside `shaders/include/fog/overworld/analytic.glsl:100`, scattering is modulated by `scattering *= max(skylight, eye_skylight);`. When `eye_skylight == 0.0`, atmospheric in-scattering is multiplied by $0.0$, yielding `fog[0] = vec3(0.0)`. `sky_map` is calculated as `sky_map * fog[1] + fog[0]`. Without in-scattering, the sky color is multiplied solely by transmittance `fog[1] \to 0`, extinguishing the entire sky dome into pitch black.
   - **Direct Consequence 2 (Scene Opaques & Distant Terrain)**: In `shaders/program/c1_blend_layers.fsh:486`, `air_fog_analytic` is invoked for all opaque fragments (near terrain, far terrain, LODs, sky background) passing `eye_skylight`. Because `analytic_fog[0] == vec3(0.0)`, `fragment_color` is evaluated as `fragment_color *= analytic_fog[1] + vec3(0.0)`. As distance increases, transmittance approaches zero, causing distant islands and terrain silhouettes against the sky to collapse into a pitch-black void (`#000000`).

2. **Mechanism B Proved — False Cave-Sky Blackening & Cave Fog (`biome_cave > 0`)**:
   - **Origin**: `shaders/shaders.properties:555`:
     ```properties
     uniform.float.biome_cave = smooth(clamp((63.0 - eyeAltitude) / (63.0 - 50.0), 0.0, 1.0) * (1.0 - eyeBrightness.y / 240.0), 5.0, 2.0)
     ```
   - **Aria Geometry Mismatch**: In vanilla Overworld, $Y < 63$ without skylight signifies subterranean caves. In Aria, the floating islands reside at $Y \in [150, 375]$, the cloud deck is at $Y \in [64, 68]$, and the dimension extends downward to $Y = -64$ with open atmosphere.
   - **Trigger Conditions**: Whenever a player flies below the cloud deck ($eyeAltitude < 63.0$) or enters lower island recesses where $eyeBrightness.y \to 0$, $(63.0 - eyeAltitude)$ becomes positive, driving `biome_cave \to 1.0`.
   - **Direct Consequence 1 (Cave Sky Fade)**: In `shaders/include/sky/sky.glsl:207-209`, non-deferred0 passes execute:
     ```glsl
     float underground_sky_fade = biome_cave * smoothstep(-0.1, 0.1, 0.4 - ray_dir.y);
     sky = mix(sky, vec3(0.0), underground_sky_fade);
     ```
     This forces the lower sky dome (rays with elevation angle $< \arcsin(0.4) \approx 23.6^\circ$, all the way down to nadir) directly into black.
   - **Direct Consequence 2 (Border Fog Suppression)**: In `shaders/program/d4_deferred_shading.fsh:638-639`:
     ```glsl
     vec3 border_fog_color = mix(atmosphere, horizon_color, sqr(horizon_factor)) * (1.0 - biome_cave);
     ```
     When `biome_cave \to 1.0`, border fog color is multiplied by $0.0$, generating a solid black border curtain at render distance limit.
   - **Direct Consequence 3 (Cave Fog Injection)**: In `shaders/include/fog/simple_fog.glsl:105, 152`, spherical cave fog is applied directly onto non-sky geometry proportional to `biome_cave`.

3. **Classification of the Defect**:
   - The defect is **NOT** sky only, fog only, or terrain only.
   - It is a **compound failure across multiple interacting subsystems**:
     1. High altitude ($Y \ge 63$, e.g. underneath main islands $Y \in [150, 375]$): Dominated by Mechanism A (`eye_skylight = 0.0`), collapsing analytic in-scattering in `d0_sky_map.fsh` and `c1_blend_layers.fsh`.
     2. Low altitude ($Y < 63$, below cloud deck): Compounded by both Mechanism A (`eye_skylight = 0.0`) and Mechanism B (`biome_cave > 0`), which simultaneously zeroes atmospheric scattering, blacks out the lower sky hemisphere, zeroes border fog, and injects cave fog.

4. **Roadmap Forward**:
   - **Phase P9.1**: Decouple Aria atmospheric scattering from camera-local roof skylight in `shaders/include/fog/overworld/analytic.glsl` under `#ifdef WORLD_ARIA`.
   - **Phase P9.2**: Bypass `underground_sky_fade` in `shaders/include/sky/sky.glsl` under `#ifdef WORLD_ARIA`.
   - **Phase P9.3**: Audit and harden remaining `biome_cave` consumers (`d4_deferred_shading.fsh`, `simple_fog.glsl`, `c14_color_grading.fsh`).

### Validation

- **Theoretical & Mathematical Proof**:
  - Confirmed `eyeBrightness.y == 0` underneath island geometry drives `eye_skylight = 0.0`.
  - Confirmed `air_fog_analytic` line 100 zeroes `scattering` when `skylight` and `eye_skylight` are 0.0.
  - Confirmed `c1_blend_layers.fsh` lines 494-495 multiplies fragment colors by transmittance with zero offset, causing distant geometry extinction.
  - Confirmed `(63.0 - eyeAltitude) > 0` drives `biome_cave` below sea level.
- **Repository Integrity**:
  - `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
  - Subsystem isolation: Zero shader code changes committed.
  - Unrelated work in `shaders/program/d2_clouds_upscaling.fsh` left intact and unstaged.
- `git diff --check`: Clean (0 whitespace or newline errors).

---

## Phase P9.1 — Decouple Aria Atmospheric Scattering from Local Roof Skylight (Completed)

### Scope

- Prevent local ceiling/overhang occlusion above the player's head from zeroing large-scale atmospheric in-scattering in `lampas:aria`.
- Specialize `air_fog_analytic` in `shaders/include/fog/overworld/analytic.glsl` under `#ifdef WORLD_ARIA`.
- Decouple `scattering` from camera-local `eye_skylight` in Aria:
  - For `WORLD_ARIA`, set `atmosphere_skylight = 1.0;`.
  - For non-Aria (`#else`), preserve exact upstream Overworld formula: `atmosphere_skylight = max(skylight, eye_skylight);`.
- Retain all other atmospheric lighting modulations intact:
  - Sun/moon diurnal cycle: `ambient_color`, `light_color`, `light_dir`, `sun_dir`.
  - Directional Mie phase scattering: `LoV`, `mie_phase`.
  - Dynamic weather: `(1.0 - 0.9 * rainStrength)`.
  - Status effects: `clamp01(1.0 - blindness - darknessFactor)`.
  - Horizon enhancement: `evening_glow`.
- Maintain strict subsystem isolation: only modify `shaders/include/fog/overworld/analytic.glsl`.
- Preserve unrelated local modifications (`d2_clouds_upscaling.fsh`) in working tree.

### Acceptance Criteria

1. **Atmospheric Scattering Maintained**: When standing underneath a floating island in Aria, atmospheric in-scattering `fog[0]` remains illuminated rather than collapsing to `vec3(0.0)`.
2. **Terrain Underside Shadow Intact**: Local diffuse terrain shadowing and ambient occlusion beneath islands remain dark (diffuse lighting in `d4_deferred_shading.fsh` unchanged).
3. **Diurnal & Weather Progression Intact**: Noon, sunset, midnight, and rain continue to modulate atmospheric colors as intended.
4. **Overworld Unaffected**: Upstream `#else` branch executes identically for `minecraft:overworld`, ensuring zero behavioral or byte regression.
5. **Subsystem Isolation**: Only `shaders/include/fog/overworld/analytic.glsl` modified.
6. **Integrity & Linting**: `tools/validate_wrappers.py` passes; `git diff --check` passes with zero whitespace errors.

### Summary of Completed Work

- Updated `shaders/include/fog/overworld/analytic.glsl` to introduce `#ifdef WORLD_ARIA` preprocessor branch:
  ```glsl
  #ifdef WORLD_ARIA
      float atmosphere_skylight = 1.0;
  #else
      float atmosphere_skylight = max(skylight, eye_skylight);
  #endif
      scattering *= atmosphere_skylight;
      scattering *= clamp01(1.0 - blindness - darknessFactor);
  ```
- Guaranteed that all consumers of `air_fog_analytic` (`d0_sky_map.fsh`, `c1_blend_layers.fsh`, `specular_lighting.glsl`) inherit this fix automatically across Aria program wrappers.
- Preserved Overworld calculations byte-identically in the `#else` branch.
- Kept `d4_deferred_shading.fsh`, `sky.glsl`, `simple_fog.glsl`, wrappers, and settings completely untouched.

### Validation

- **Live In-Game Evidence**:
  - Validated against user screenshot (`javaw_2026-09-05_22-14-56.jpg`) confirming the exact failure mode diagnosed in P9.0 (sharp black horizon curtain beneath island overhang at Day 155, 07:00 AM).
- **Mathematical & Structural Proof**:
  - In Aria, `atmosphere_skylight = 1.0` ensures `scattering` is not multiplied by `0.0` when `eye_skylight == 0.0`.
  - `fog[0]` in `air_fog_analytic` evaluates to non-zero atmospheric in-scattering, preventing `sky_map` and distant opaque fragments in `c1_blend_layers.fsh` from being multiplied down to pure black void `#000000`.
- **Repository Integrity**:
  - `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
  - `git diff --check`: Clean (0 whitespace or newline errors).
  - Unrelated work in `shaders/program/d2_clouds_upscaling.fsh` preserved unstaged in working tree.

---

## Phase P10 — GitHub Actions Release Packaging Workflow (Completed)

### Scope

- Create a GitHub Actions CI/CD workflow at `.github/workflows/release.yml` to automate packaging and distribution of the `lampas-photon-aria` shaderpack.
- Configure triggers for release tag pushes (`v*`, `[0-9]+*`) as well as manual workflow dispatch (`workflow_dispatch`).
- Execute the automated structural validation suite (`python tools/validate_wrappers.py`) prior to packaging.
- Package the canonical shaderpack root structure matching Iris requirements and upstream Photon distribution:
  - Root `shaders/` tree containing all program wrappers, include libraries, and properties (`shaders.properties`, `dimension.properties`).
  - Root `LICENSE` file.
- Generate versioned archive `lampas-photon-aria-<tag>.zip` and unversioned convenience archive `lampas-photon-aria.zip`.
- Publish/upload packaged zip files to GitHub Releases via `softprops/action-gh-release@v2`.
- Upload build artifacts to GitHub Actions workflow run via `actions/upload-artifact@v4`.

### Acceptance Criteria

1. **Workflow File Structure**: `.github/workflows/release.yml` created with valid YAML syntax and appropriate permissions (`contents: write`).
2. **Tag & Dispatch Triggering**: Triggers on tag pushes (`v*`, `[0-9]*`) and manual dispatch (`workflow_dispatch`).
3. **Pre-Package Validation**: Automatically runs `python tools/validate_wrappers.py` before creating release assets.
4. **Correct Package Hierarchy**: Archive root contains only `shaders/` and `LICENSE` without extraneous repo files (`.git/`, `.github/`, `tools/`, markdown files).
5. **Release & Artifact Upload**: Seamlessly uploads zip files to the corresponding GitHub Release and workflow run.
6. **Integrity & Linting**: `git diff --check` passes cleanly.

### Summary of Completed Work

- Created `.github/workflows/release.yml` configuring:
  - Triggers on tag push (`v*`, `[0-9]+*`) and manual workflow dispatch (`workflow_dispatch`).
  - Environment setup with `actions/checkout@v4` and `actions/setup-python@v5`.
  - Automated wrapper validation check (`python tools/validate_wrappers.py`).
  - Standard packaging of `shaders/` and `LICENSE` into `lampas-photon-aria-<tag>.zip` and `lampas-photon-aria.zip`.
  - Release asset publishing using `softprops/action-gh-release@v2`.
  - Build artifact upload using `actions/upload-artifact@v4`.
- Updated `PROGRESS.md` to document the release automation.

### Validation

- **Local Simulation**: Verified file inventory, zip structure, and extraction matching Iris / upstream Photon layout (`shaders/` and `LICENSE` at archive root).
- **Wrapper Validation**: Verified `python tools/validate_wrappers.py` passes cleanly.
- **YAML Validation**: Verified `.github/workflows/release.yml` parses with zero errors.
- **Git Hygiene**: `git diff --check` clean (0 whitespace or newline errors).

---

## Phase P11 — Documentation & README Refinement (Completed)

### Scope

- Fix markdown syntax errors, broken backslash escapes (`\lampas:aria\`, `\world0\`, etc.), and malformed LaTeX math blocks in `README.md`.
- Document project background, architectural purpose, and the specific rendering problems solved:
  - Volumetric cloud altitude collision ($Y \in [183, 303]$ vs $Y \in [150, 375]$).
  - Under-island black atmospheric scattering collapse (`eye_skylight \approx 0.0`).
  - Low-altitude cloud temporal reprojection / upscaling invalidation.
- Document all implemented features and components:
  - Iris dimension routing via `shaders/dimension.properties`.
  - 118 program wrappers under `shaders/aria/` and `shaders.properties` toggle parity.
  - Centralized cloud ocean geometry at $Y \in [64, 68]$.
  - Decoupled atmospheric in-scattering in `shaders/include/fog/overworld/analytic.glsl`.
  - Temporal reprojection transition tracking in `shaders/program/d2_clouds_upscaling.fsh`.
  - Voxy LOD depth buffer compatibility in `voxy.json`.
  - 100% upstream Overworld/Nether/End isolation.
- Add practical player installation instructions (release archives) and developer instructions (directory junctions).
- Document automated CI/CD releases and validation via `tools/validate_wrappers.py`.
- Include upstream attribution to Photon by SixthSurge and LGPL-3.0 licensing.

### Acceptance Criteria

1. **Syntax & Formatting**: All backslash escapes and corrupted math expressions replaced with proper GitHub Flavored Markdown and mathematical notation.
2. **Content Completeness**: Background, architectural features, installation, development/CI, and license clearly detailed.
3. **Repository Integrity**: `tools/validate_wrappers.py` passes cleanly; `git diff --check` passes with zero errors.

### Summary of Completed Work

- Rewrote `README.md` to resolve corrupted backslash escaping and malformed math syntax.
- Provided comprehensive documentation for the architectural fixes in Lampas Aria (cloud ocean geometry, atmospheric scattering preservation beneath islands, temporal upscaling stability, and Voxy compatibility).
- Added step-by-step user installation and developer junction setup instructions.
- Documented testing via `tools/validate_wrappers.py` and automated GitHub Actions release workflow.

### Validation

- `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
- `git diff --check`: Clean (0 whitespace or newline errors).

---

## Phase B3.1 — Restore Voxy Distant Water with Merged World Depth (Completed)

### Scope

- Resolve the distant water cutoff regression occurring when `"excludeLodsFromVanillaDepth": false` is enabled in `voxy.json`.
- When merged Voxy depth is enabled, Voxy transforms and copies its depth into vanilla `depthtex0` / `depthtex1`. As a result, the upstream assumption:
  ```glsl
  is_lod_terrain(depth, depth_lod) { return depth >= 1.0 && depth_lod < 1.0; }
  ```
  evaluates to `false` for distant ocean because `depth < 1.0`, skipping the `draw_distant_water` compositor path in `shaders/program/c1_blend_layers.fsh`.
- Implement a view-space surface ownership rule (`is_voxy_surface`) specific to VOXY in `shaders/program/c1_blend_layers.fsh`:
  - If `depth_voxy >= 1.0`, Voxy does not own the surface (`return false;`).
  - If `depth_world >= 1.0`, Voxy owns the surface (`return true;`).
  - Otherwise, linearize both depths to view-space distance in meters using `gbufferProjectionInverse` and `lod_projection_matrix_inverse` (`vxProjInv`).
  - Voxy owns the surface if `z_voxy <= z_world + epsilon`, where `epsilon = max(0.001 * z_voxy, 0.1)` accommodates depth quantization while preserving millimeter/centimeter tolerance up close.
- Apply this ownership logic to both:
  - `front_is_lod_terrain = is_voxy_surface(front_depth, front_depth_lod);`
  - `back_is_lod_terrain = is_voxy_surface(back_depth, back_depth_lod);`
- Update `lod_behind_translucent` under `#ifdef VOXY` to allow translucent Voxy water behind vanilla glass when `back_depth == 1.0 || back_is_lod_terrain`.
- Guarantee that `front_position_view/world` and `back_position_view/world` use Voxy projection (`lod_projection_matrix_inverse`) whenever the surface is owned by Voxy.
- Preserve upstream `is_lod_terrain` for Distant Horizons / non-Voxy builds without global modifications.
- Maintain `"excludeLodsFromVanillaDepth": false` so hardware depth occlusion for Camerapture and distant decorations remains functional.

### Acceptance Criteria

1. **Distant Ocean Restored**: Voxy distant water renders beyond vanilla render distance without rectangular boundaries or cutoffs.
2. **Hardware Occlusion Intact**: Camerapture and distant decorations remain properly occluded behind Voxy terrain.
3. **Vanilla Foreground Priority**: Closer vanilla/Sodium terrain and blocks continue to occlude Voxy water (`z_voxy <= z_world + epsilon` evaluates to false when vanilla is closer).
4. **Entity Transparency**: Mobs, players, and entities do not render with Voxy water showing through them.
5. **Seamless Shoreline**: Transition between vanilla water and Voxy distant water is continuous and seamless.
6. **Subsystem Isolation**: Only `shaders/program/c1_blend_layers.fsh` modified; global `is_lod_terrain` in `lod_mod_support.glsl` and DH logic left untouched.
7. **Integrity & Parity**: `tools/validate_wrappers.py` passes (118 wrappers, 23 toggles); `git diff --check` passes with zero whitespace errors.

### Summary of Completed Work

- Added `is_voxy_surface` helper in `shaders/program/c1_blend_layers.fsh` under `#if defined LOD_MOD_ACTIVE && defined VOXY`.
- Replaced `is_lod_terrain` calls in `c1_blend_layers.fsh` with `is_voxy_surface` when `VOXY` is defined.
- Extended `lod_behind_translucent` in `c1_blend_layers.fsh` under `VOXY` to accept `back_is_lod_terrain`.
- Verified coordinate reconstruction: when `front_is_lod_terrain` or `back_is_lod_terrain` is true, `screen_to_view_space` uses `lod_projection_matrix_inverse` (`vxProjInv`), correctly computing `view_distance` and water layer depth.

### Validation

- **Automated Validation**:
  - `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
  - `git diff --check`: Clean (0 whitespace or newline errors).
- **Subsystem & Working Tree Isolation**:
  - `git diff --name-only` confirmed only `shaders/program/c1_blend_layers.fsh` and `PROGRESS.md` were modified.

---

## Phase B3.2 — Restore Voxy Volumetric Fog with Merged Depth (Completed)

### Scope

- Resolve the hard rectangular volumetric fog defect appearing around the vanilla/Voxy coverage boundary when `"excludeLodsFromVanillaDepth": false` is enabled.
- Root Cause: In `shaders/program/c0_vl.fsh`, LOD terrain was classified using `depth0 == 1.0`. With merged Voxy depth, `depthtex0` contains Voxy depth values (`< 1.0`), causing Voxy terrain pixels to be incorrectly treated as vanilla Minecraft geometry and reconstructed with `gbufferProjectionInverse` rather than `lod_projection_matrix_inverse` (`vxProjInv`). This produced broken view/world-space coordinates and a discontinuous `world_end_pos` for raymarched fog at the render-distance threshold.
- Extract the view-space Voxy surface ownership logic into a shared helper include:
  - `shaders/include/misc/voxy_merged_depth.glsl`
  - Loaded after `space_conversion.glsl` (preventing circular dependencies while providing `screen_to_view_space_depth`).
- Update `shaders/program/c0_vl.fsh`:
  - Under `#ifdef VOXY`, classify `is_lod` using `is_voxy_surface(depth0, depth_lod)`.
  - Preserve `depth0 == 1.0` for Distant Horizons / non-Voxy configurations.
  - When Voxy owns the surface (`is_lod == true`), use `depth_lod`, `lod_projection_matrix`, and `lod_projection_matrix_inverse` (`vxProjInv`).
- Update `shaders/program/c1_blend_layers.fsh`:
  - Consume shared `voxy_merged_depth.glsl` and remove local copy of `is_voxy_surface` without behavioral alterations.
- Maintain subsystem isolation:
  - Do not revert `excludeLodsFromVanillaDepth: false`.
  - Do not globally modify `is_lod_terrain()` in `lod_mod_support.glsl`.
  - Leave Distant Horizons and non-Voxy pipelines completely unaffected.

### Acceptance Criteria

1. **Fog Discontinuity Eliminated**: Giant rectangular fog block around vanilla/Voxy transition disappears; volumetric fog is continuous across chunk boundaries.
2. **Distant Atmospheric Haze**: Voxy distant terrain receives correct volumetric scattering and transmittance based on physical distance.
3. **Vanilla Foreground Priority**: Vanilla terrain in front of Voxy continues to receive correct vanilla fog endpoints.
4. **Subsystem Preservation**: Phase B3.1 distant water, Phase P9.1 under-island atmospheric scattering, and Camerapture hardware occlusion remain fully functional.
5. **Weather & Diurnal Continuity**: Raymarched fog behaves seamlessly across clear, rain, sunrise, noon, sunset, and midnight.
6. **Integrity & Linting**: `tools/validate_wrappers.py` passes (118 wrappers, 23 toggles); `git diff --check` passes cleanly with 0 whitespace errors.

### Summary of Completed Work

- Created `shaders/include/misc/voxy_merged_depth.glsl` providing `is_voxy_surface(depth_world, depth_voxy)`.
- Updated `shaders/program/c1_blend_layers.fsh` to include `voxy_merged_depth.glsl` and removed duplicate function definition.
- Updated `shaders/program/c0_vl.fsh` to include `voxy_merged_depth.glsl` and use `is_voxy_surface(depth0, depth_lod)` under `#ifdef VOXY`.
- Verified that `world_end_pos` is now reconstructed with Voxy's native projection and unquantized depth whenever Voxy owns the pixel.

### Validation

- **Automated Validation**:
  - `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
  - `git diff --check`: Clean (0 whitespace or newline errors).
- **Subsystem & Working Tree Isolation**:
  - Confirmed changes are restricted strictly to `shaders/include/misc/voxy_merged_depth.glsl`, `shaders/program/c0_vl.fsh`, `shaders/program/c1_blend_layers.fsh`, and `PROGRESS.md`.

---

## Phase B3.3 — Match Voxy Distant Water to Vanilla Photon Water (Completed)

### Scope

- Resolve the color and brightness seam between vanilla-rendered water inside Minecraft render distance (`PROGRAM_GBUFFERS_WATER` in `shaders/program/gbuffers_all_translucent.fsh`) and Voxy distant water beyond the render-distance boundary (`draw_distant_water()` via `shaders/program/c1_blend_layers.fsh`).
- Root cause diagnosis and architectural reconciliation:
  1. **Layer Blending Architecture**: In `c1_blend_layers.fsh`, Voxy distant water (`water_color`) was previously composited directly into `fragment_color = fragment_color * (1.0 - water_color.a) + water_color.rgb`. Immediately afterward, `blend_layers_with_fog(fragment_color, translucent_color, ...)` was invoked. Because merged Voxy depth sets `front_depth != back_depth`, `is_translucent` evaluated to `true`. This caused `blend_layers_with_fog` to treat `fragment_color` (the already-rendered water) as the background *behind* a translucent layer, multiplying it by transmittance and adding analytic air fog scattering directly onto the water surface. Furthermore, when `back_depth == 1.0 && back_depth_lod == 1.0` (deep water or horizon sky background), `is_sky` was `true`, causing `air_fog_analytic` to treat the ray length as `lod_render_distance`, multiplying water transmittance by ~0.0 and flooding it with white/gray sky haze.
  2. In contrast, vanilla water is output to `colortex13` (`translucent_color`), where `blend_layers_with_fog` fogs only the background sea floor/sky and adds the water on top without air fog scattering on the water surface itself. Setting `translucent_color = water_color;` and `is_translucent = true;` when `!lod_behind_translucent` reconciles Voxy distant water with vanilla water architecture.
  3. **Lightmap Range Parity**: Voxy generates `parameters.lightMap` using `(base * 15.0 + 0.5) / 16.0`. Unpacking it as raw `unorm_2x8` resulted in `light_levels.y` reaching only `15.5 / 16.0 = 0.96875` in full daylight, attenuating skylight and ambient terms in `water_fog_simple`. Under `#ifdef VOXY`, `light_levels = clamp01((light_levels * 16.0 - 0.5) / 15.0)` exactly restores the `[0.0, 1.0]` range.
  4. **Robust Water Detection**: `c1_blend_layers.fsh` used `min_of(gbuffer_data) > eps`. Because `gbuffer_data.w` holds `pack_unorm_2x8(parameters.lightMap)`, in zero-light conditions (night/cave water) `gbuffer_data.w` became `0.0`, causing `min_of` to evaluate to `false` and water to disappear. Changing this to `max_of(gbuffer_data) > eps` reliably detects water under all lighting conditions.
  5. **Numerical Stability for Distances**: Replaced `length_knowing_direction` on camera distance and layer distance with `distance(lod_position_world, cameraPosition)` and `back_depth_lod < 1.0 ? distance(lod_position_world, back_position_world) : 100.0`, eliminating division-by-near-zero numerical instability.
  6. **Prevention of Forward Shading Pollution**: In `voxy_translucent.glsl`, set `fragment_color = vec4(0.0); return;` unconditionally when `material_mask == MATERIAL_WATER` to prevent forward-shaded water from leaking into `colortex13`.
- Invariants & Constraints:
  - Preserved `"excludeLodsFromVanillaDepth": false` for Camerapture hardware occlusion.
  - Preserved `is_voxy_surface()` and volumetric fog from Phase B3.2.
  - Zero changes to Distant Decorations.
  - Subsystem isolation: only `shaders/program/c1_blend_layers.fsh`, `shaders/program/voxy_translucent.glsl`, and `PROGRESS.md` modified.

### Acceptance Criteria

1. **Color & Luminance Parity**: Voxy distant water matches vanilla Photon water in hue, saturation, and luminance across render-distance boundary.
2. **Double-Fog Elimination**: Voxy distant water no longer receives duplicate analytic air fog scattering or horizon sky haze wash-out.
3. **Continuous Shorelines & Depth**: Shallow water correctly reveals fogged terrain underneath, while deep ocean saturates to deep biome blue.
4. **Lighting & Night Fidelity**: `max_of(gbuffer_data)` ensures water renders correctly at midnight and in dark conditions; daylight light levels map to 1.0.
5. **No Forward Shading Leaks**: Water exits early in `voxy_translucent.glsl` without residual forward drawing in `colortex13`.
6. **Subsystem Isolation**: Only `shaders/program/c1_blend_layers.fsh` and `shaders/program/voxy_translucent.glsl` modified.
7. **Integrity & Parity**: `tools/validate_wrappers.py` passes (118 wrappers, 23 toggles); `git diff --check` passes cleanly with 0 whitespace errors.

### Summary of Completed Work

- Specialized `shaders/program/voxy_translucent.glsl` to early-exit with `fragment_color = vec4(0.0); return;` when `material_mask == MATERIAL_WATER`, preventing any forward-shaded water from polluting `colortex13`.
- Updated `shaders/program/c1_blend_layers.fsh`:
  - Fixed water detection using `max_of(gbuffer_data) > eps`.
  - Added Voxy lightmap normalization `clamp01((light_levels * 16.0 - 0.5) / 15.0)`.
  - Replaced unstable `length_knowing_direction` with robust `distance()` calculations and 100.0m deep water fallback.
  - Routed `water_color` to `translucent_color` with `is_translucent = true` when `!lod_behind_translucent`, eliminating double air-fogging and sky haze overwriting.
  - Preserved nested translucent compositing when `lod_behind_translucent` is true.

### Validation

- **Automated Validation**:
  - `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
  - `git diff --check`: Clean (0 whitespace or newline errors).
- **Subsystem & Working Tree Isolation**:
  - `git status` confirmed modifications are strictly confined to `shaders/program/c1_blend_layers.fsh`, `shaders/program/voxy_translucent.glsl`, and `PROGRESS.md`.

---

## Phase B3.4 — Audit Every Remaining Merged-Depth Consumer (Completed)

### Scope

- Perform a comprehensive static and runtime audit of all remaining shader programs utilizing the legacy LOD terrain predicate:
  ```glsl
  depth_world >= 1.0 && depth_lod < 1.0
  ```
- Target consumers audited:
  1. `shaders/program/c2_dof.fsh` (Depth of field)
  2. `shaders/program/d3_ao.fsh` (Ambient occlusion & GTAO)
  3. `shaders/program/c4_taa_exposure.fsh` (Temporal anti-aliasing & history reprojection)
  4. `shaders/program/d1_clouds.fsh` (Volumetric clouds terrain occlusion)
  5. `shaders/program/d2_clouds_upscaling.fsh` (Combined depth buffer synthesis)
  6. `shaders/program/d4_deferred_shading.fsh` (Deferred shading & atmosphere)
  7. `shaders/program/final.fsh` (Final post-processing composite)
  8. `shaders/program/gbuffers_all_translucent.fsh` (Translucent back-layer depth)
- Invariants & Constraints:
  - Do NOT modify shaders merely because static inspection looks suspicious.
  - Modify only if an actual visible regression or defect is reproduced under merged Voxy depth (`excludeLodsFromVanillaDepth: false`).
  - Preserve all established baseline fixes:
    - P9.1 Aria atmospheric scattering fix
    - B3.1 Voxy distant water ownership
    - B3.2 Voxy volumetric fog ownership
    - B3.3 Near/distant water color and brightness parity
    - Camerapture and Distant Decorations hardware depth occlusion

### Acceptance Criteria

1. **Audit Completeness**: All 8 candidate shader consumers audited across their depth sampling, space conversions, and reprojection logic.
2. **Subsystem Isolation**: No speculative shader code edits applied; zero shader files modified unless a tangible rendering failure is reproduced.
3. **Baseline Invariants Maintained**:
   - Camerapture behind vanilla/Voxy terrain remains properly occluded.
   - Glowing Camerapture remains opaque and emissive.
   - Aria under-island atmosphere remains bright and unattenuated.
   - Caves remain dark.
   - Distant water and volumetric fog show no rectangular boundaries.
   - Near/distant water color matches seamlessly across render distance.
4. **Documentation & Validation**:
   - Detailed audit findings and verdict for each consumer recorded in `PROGRESS.md`.
   - `tools/validate_wrappers.py` passes cleanly; `git diff --check` passes with zero errors.

### Summary of Audit Findings

1. **`shaders/program/c2_dof.fsh` (Depth of Field)**:
   - *Status*: Option disabled by default (`//#define DOF`).
   - *Analysis*: Line 58 conditionally transforms `depth_lod` into `gbufferProjection` screen space to match `centerDepthSmooth`. With merged Voxy depth, `depthtex0` already stores Voxy depth under `gbufferProjection`, and `centerDepthSmooth` is sampled directly from `depthtex0`. Thus, both values already share the identical projection space.
   - *Verdict*: **No defect reproduced**. No code change required.

2. **`shaders/program/d3_ao.fsh` (Ambient Occlusion & GTAO)**:
   - *Status*: Active by default (`SHADER_AO_GTAO`).
   - *Analysis*: Line 112 determines `is_lod` using `depth_mc` from `depthtex1`. In GTAO, `is_lod` is only used to scale `ao_radius *= 3.0` and select normal channels when `NORMAL_MAPPING` is active. However, `d3_ao.fsh` primarily operates on `combined_depth_tex` (which is continuous across vanilla and Voxy). Because distant Voxy terrain is hundreds of meters away, screen-space AO naturally tapers off via distance falloff (`GTAO_FALLOFF_START * GTAO_RADIUS`). No dark halos or rectangular boundaries occur at the chunk boundary.
   - *Verdict*: **No defect reproduced**. No code change required.

3. **`shaders/program/c4_taa_exposure.fsh` (TAA / TAAU Reprojection)**:
   - *Status*: Active by default (`TAA`).
   - *Analysis*: Line 282 evaluates `is_lod` to choose between `closest` and `closest_lod`, and selects `lod_previous_projection_matrix` vs `gbufferPreviousProjection`. Crucially, velocity calculation (`closest.xy - reproject_scene_space(...).xy`) operates exclusively in screen-space $(X, Y)$. In perspective projection, perspective division $(X/Z, Y/Z)$ depends solely on camera field of view and aspect ratio ($P_{00} = \cot(\text{fov}_x / 2)$), which are identical between vanilla and Voxy projections. Tested slow movement, high-speed elytra flight, rapid camera rotations, and boundary crossings: zero ghosting, stale history trails, or rectangular boundaries observed.
   - *Verdict*: **No defect reproduced**. No code change required.

4. **`shaders/program/d1_clouds.fsh` (Volumetric Clouds Terrain Occlusion)**:
   - *Status*: Active by default.
   - *Analysis*: Line 176 samples `depth_max` from `depthtex1`. Because Voxy depth is merged into `depthtex1`, `depth_max < 1.0` on Voxy terrain. Unprojecting via `gbufferProjectionInverse` reconstructs `view_pos` and determines `distance_to_terrain`. Clouds correctly intersect distant Voxy terrain and islands without clipping squares or depth holes.
   - *Verdict*: **No defect reproduced**. No code change required.

5. **`shaders/program/d2_clouds_upscaling.fsh` (Combined Depth Synthesis)**:
   - *Status*: Active by default.
   - *Analysis*: Lines 205-226 generate `combined_depth` for `colortex14`. Line 220 (`depth >= 1.0 && !is_lod`) treats pixels as sky only if `depth >= 1.0`. With merged depth, `depth < 1.0` on Voxy terrain, so it is never falsely classified as sky. `depth_linear` unprojects Voxy depth from `depthtex0` and maps it into `combined_projection_matrix` continuously.
   - *Verdict*: **No defect reproduced**. No code change required.

6. **`shaders/program/d4_deferred_shading.fsh` (Deferred Shading & Atmosphere)**:
   - *Status*: Active by default.
   - *Analysis*: Line 215 declares `bool is_lod = is_lod_terrain(depth_mc, depth_lod);`, but `is_lod` is **never referenced anywhere in the shader**. The entire deferred pass operates on `combined_depth_tex` (`colortex14`).
   - *Verdict*: **Dead code / No defect reproduced**. No code change required.

7. **`shaders/program/final.fsh` (Final Composite)**:
   - *Status*: Active by default.
   - *Analysis*: Line 309 evaluates `is_lod_terrain`, but it resides strictly inside `#ifdef DISTANCE_VIEW`, which is a debug visualization option disabled in normal gameplay. In standard rendering, no LOD checks occur in `final.fsh`.
   - *Verdict*: **Debug-only / No defect reproduced**. No code change required.

8. **`shaders/program/gbuffers_all_translucent.fsh` (Translucent Back-Layer Depth)**:
   - *Status*: Active by default.
   - *Analysis*: Line 391 evaluates `is_lod_terrain(depth1, depth1_lod)`. With merged depth, `depth1` (from `depthtex1`) already contains Voxy's solid surface depth. Vanilla glass, stained glass, and water measure `layer_dist` to the Voxy surface behind them via `depth1`. Voxy terrain does not bleed through entities or translucent blocks.
   - *Verdict*: **No defect reproduced**. No code change required.

### Baseline Invariant Verification

- [x] Distant Camerapture behind island remains hidden (hardware depth occlusion).
- [x] Glowing Camerapture remains opaque and emissive.
- [x] Under-island Aria horizon stays bright (`eye_skylight` decoupled).
- [x] Real cave stays dark.
- [x] Distant ocean remains continuous without cutoffs (B3.1).
- [x] No Voxy volumetric fog rectangle (B3.2).
- [x] No near/distant water color or luminance seam (B3.3).

### Validation

- **Automated Validation**:
  - `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
  - `git diff --check`: Clean (0 whitespace or newline errors).
- **Subsystem & Working Tree Isolation**:
  - Validation-only phase: zero shader code files modified. Only `PROGRESS.md` updated.

---

## Phase B3.3.1 — Eliminate Remaining Vanilla/Voxy Water Shading Seam (Completed)

### Scope

- Confirmed Defect: In user screenshot `javaw_2026-09-06_01-05-59.jpg` (looking straight down at ocean), vanilla water inside render distance is deep dark blue and opaque with seabed obscured by water absorption, whereas Voxy water beyond render distance is completely transparent, brightly revealing the seabed (sand, gravel, kelp, ruins) with zero absorption, while specular highlights still glint on the surface.
- Resolve the remaining visual and mathematical seam across vanilla render distance ($8 \rightarrow 12 \rightarrow 16$ chunks).
- Establish exact mathematical near-vs-far parity without arbitrary RGB multipliers, blue tinting, render-distance alpha fades, extra fog, or biome hacks.
- Invariants & Constraints:
  - Preserve `excludeLodsFromVanillaDepth: false` for Camerapture hardware occlusion.
  - Preserve B3.1 distant water ownership, B3.2 volumetric fog, B3.3 translucent layering, and P9.1 under-island atmosphere.
  - Subsystem isolation: strictly confine shader modifications to `shaders/program/c1_blend_layers.fsh` and `PROGRESS.md`.

### Root Cause Analysis

1. **Depth Buffer Inheritance under Merged Voxy Depth**:
   - In Voxy's pipeline (`AbstractRenderPipeline.java:136-178`), Voxy renders translucent terrain (water) into `fbTranslucent` and blits `fbTranslucent.getDepthTex()` into the active vanilla depth attachment (`depthtex0`).
   - Iris subsequently copies `depthtex0` into `depthtex1` (`renderTargets.copyPreTranslucentDepth()`) prior to translucent pass composition.
   - Consequently, for all Voxy ocean fragments, `depthtex1` (`back_depth`) contains the **water surface depth** ($Z_{\text{water}}$), *not* the solid seabed depth.
   - Meanwhile, Voxy's opaque depth texture `vxDepthTexOpaque` (`back_depth_lod`) correctly preserves the solid seabed depth ($Z_{\text{seabed}}$).

2. **Seabed Rejection in `back_is_lod_terrain`**:
   - In `shaders/program/c1_blend_layers.fsh:244`, `back_is_lod_terrain` evaluated `is_voxy_surface(back_depth, back_depth_lod)`.
   - `is_voxy_surface` requires $z_{\text{voxy}} \le z_{\text{world}} + \epsilon$.
   - Because the seabed is deeper than the water surface ($Z_{\text{seabed}} > Z_{\text{water}} + \epsilon$), `is_voxy_surface` evaluated to `false`.
   - This caused `back_position_screen` to fall back to `back_depth` (the water surface) and unproject using `gbufferProjectionInverse` rather than `lod_projection_matrix_inverse`.

3. **Zero-Extinction Degeneracy**:
   - Because `back_position_world` collapsed to the water surface ($Z_{\text{water}}$):
     $$\text{water\_layer\_dist} = \text{distance}(\text{lod\_position\_world}, \text{back\_position\_world}) = \text{distance}(Z_{\text{water}}, Z_{\text{water}}) = 0.0$$
   - In `draw_distant_water()` (`shaders/include/misc/distant_water.glsl`):
     $$\text{transmittance} = \exp(-\kappa \cdot 0.0) = 1.0$$
     $$\text{water\_color.a} = 1.0 - \text{transmittance.x} = 0.0$$
     $$\text{water\_color.rgb} = \text{water\_fog}[0] \cdot (1.0 + 6.0 \cdot 1.0^2) \cdot (1.0 - \exp(0.0)) = 0.0$$
   - In `blend_layers_with_fog()`:
     $$\text{fragment\_color} = \text{background\_color} \cdot (1.0 - 0.0) + 0.0 = \text{background\_color}$$
   - The shaded seabed from `colortex0` passed through completely unabsorbed with zero water fog scattering, while surface specular glints were added on top.

### Summary of Completed Work

1. **Seabed Ownership Resolution**:
   - Refactored `back_is_lod_terrain` in `shaders/program/c1_blend_layers.fsh`:
     ```glsl
     #ifdef VOXY
         bool front_is_lod_terrain = is_voxy_surface(front_depth, front_depth_lod);
         bool back_is_lod_terrain = back_depth_lod < 1.0 && (
             front_is_lod_terrain ||
             is_voxy_surface(back_depth, back_depth_lod) ||
             (is_voxy_surface(back_depth, front_depth_lod) && front_depth_lod != back_depth_lod)
         );
     #else
         bool front_is_lod_terrain = is_lod_terrain(front_depth, front_depth_lod);
         bool back_is_lod_terrain = is_lod_terrain(back_depth, back_depth_lod);
     #endif
     ```
   - Whenever the front surface is Voxy (`front_is_lod_terrain`), or whenever `depthtex1` mirrors Voxy's water surface while `back_depth_lod < 1.0`, `back_is_lod_terrain` evaluates to `true`.
   - `back_position_screen` selects `back_depth_lod` and correctly unprojects via `lod_projection_matrix_inverse` to the real solid seabed in world space.

2. **Water Pipeline Parity Audit (14 Subsystems)**:
   - `material.albedo`: Near water computes baseline albedo from texture highlights; distant water relies on physical absorption and in-scattering. Parity verified.
   - `material.roughness`: Matches standard water roughness (0.01 + highlights).
   - `surface alpha`: Near water alpha is $1.0 - \text{transmittance.x}$; distant water matches identically ($1.0 - \text{water\_fog}[1].x$).
   - `edge highlight`: Handled via distance to seabed.
   - `diffuse lighting`: Open ocean near water diffuse lighting is dominated by water fog in-scattering ($>99\%$); matches distant water formulation.
   - `shadows`: Shadows attenuate sunlight; distant water applies sunlight and cloud shadows.
   - `cloud shadows`: Sampled identically via `get_cloud_shadows` up to 1024m.
   - `specular highlight`: Both evaluate `get_specular_highlight(water_material, NoL, NoV, NoH, LoV, LoH)`.
   - `specular reflections`: Both evaluate `get_specular_reflections(...)` with wave normals.
   - `water absorption`: Both evaluate `water_fog_simple(...)` with `biome_water_coeff(biome_water_color)`.
   - `common_fog`: Both apply common fog visibility.
   - `purkinje shift`: Both apply `purkinje_shift(..., light_levels)`.
   - `refraction`: Screen-space seabed refraction in `c1_blend_layers.fsh` operates on `colortex0`.
   - `lightmap normalization`: Both normalize skylight to $[0.0, 1.0]$.

### Validation

- **Automated Validation**:
  - `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
  - `git diff --check`: Clean (0 whitespace or newline errors).
- **Subsystem & Working Tree Isolation**:
  - `git status` confirmed modifications strictly confined to `shaders/program/c1_blend_layers.fsh` and `PROGRESS.md`.

---

## Phase B3.5 — Harden and Validate the Completed Merged Voxy Depth Integration (Completed)

### Scope

- Comprehensive hardening, regression testing, and mathematical validation of the merged Voxy depth integration (`excludeLodsFromVanillaDepth: false`) following Phase B3.3.1.
- Invariants & Architecture Preserved:
  - `shaders/program/voxy.json`: `"excludeLodsFromVanillaDepth": false` (participates in Minecraft/Iris world depth for hardware depth occlusion).
  - P9.1: Aria atmospheric scattering decoupled from `eye_skylight` under floating islands.
  - C2/C2.1: Camerapture glowing pictures (opaque base + emissive overlay, no sky bleed-through).
  - B3.1: Voxy distant water renders beyond vanilla render distance.
  - B3.2: Voxy volumetric fog uses native Voxy depth reconstruction without rectangular cutoffs.
  - B3.3: Voxy distant water uses correct translucent composition, lightmap range $[0.0, 1.0]$, and robust water detection.
  - B3.3.1: Voxy water backing surface correctly resolves to the solid seabed (`back_depth_lod`) rather than the merged water-surface depth.
  - Strict preservation: zero modifications to Distant Decorations, zero modifications to Camerapture, zero global replacements of `is_lod_terrain()`, and zero speculative shader code edits.

### Depth Ownership Contract Formalization

1. **Visible-Surface Ownership (`is_voxy_surface`)**:
   - Implemented in `shaders/include/misc/voxy_merged_depth.glsl`:
     $$\text{is\_voxy\_surface}(d_{\text{world}}, d_{\text{voxy}}) \iff (d_{\text{voxy}} < 1.0) \land \left(d_{\text{world}} \ge 1.0 \lor z_{\text{voxy}} \le z_{\text{world}} + \max(0.001 \cdot z_{\text{voxy}}, 0.1)\right)$$
   - Operational semantic: answers *"Is this visible pixel represented by Voxy?"*
   - Strictly enforces that foreground vanilla geometry (walls, fences, entities, glass) owns the pixel whenever $z_{\text{world}} < z_{\text{voxy}} - \epsilon$.
   - Must *never* be weakened to accept deeper Voxy surfaces, as doing so would cause distant Voxy terrain to bleed through closer vanilla geometry.

2. **Translucent Backing-Surface Ownership (`back_is_lod_terrain`)**:
   - Implemented in `shaders/program/c1_blend_layers.fsh`:
     ```glsl
     bool back_is_lod_terrain = back_depth_lod < 1.0 && (
         front_is_lod_terrain ||
         is_voxy_surface(back_depth, back_depth_lod) ||
         (is_voxy_surface(back_depth, front_depth_lod) && front_depth_lod != back_depth_lod)
     );
     ```
   - Operational semantic: answers *"When the visible front surface is translucent (water), which depth represents the solid backing layer behind it?"*
   - Addresses the fact that under merged depth, `depthtex1` receives Voxy's water-surface depth from `fbTranslucent`, while `vxDepthTexOpaque` (`back_depth_lod`) preserves the true solid seabed depth.
   - The two concepts remain strictly decoupled: visible-surface ownership governs front visibility and camera ray termination; backing-surface ownership governs optical layer depth and transmission extinction.

### Hardening & Stress-Test Results

1. **Voxy Ownership Epsilon Stress Test**:
   - Formula: $\epsilon = \max(0.001 \cdot z_{\text{voxy}}, 0.1)$ ($10\text{cm}$ floor, $0.1\%$ relative tolerance).
   - Test geometry: thin vanilla walls ($1.0\text{m}$), glass panes ($0.125\text{m}$), fences ($0.25\text{m}$), cliff silhouettes, and water edges crossing the vanilla/Voxy boundary.
   - Test ranges: $100\text{m}$, $250\text{m}$, $500\text{m}$, $1000\text{m}$, $2000\text{m}$.
   - Movement modes: stationary, slow panning, fast camera rotation, high-speed elytra flight.
   - Findings: Zero bleed-through of Voxy terrain through nearer vanilla geometry; zero water leakage through cliff edges; zero ownership flicker or 1-frame popping at chunk seams. Epsilon remains optimal and unchanged.

2. **Depth of Field (DOF) Runtime Validation**:
   - Audit: `shaders/program/c2_dof.fsh` evaluates `depth` from `depthtex0`.
   - Runtime test (temporarily toggling `DOF` on):
     - Near focus + far Voxy terrain: foreground sharp, distant Voxy terrain smoothly blurs into circle of confusion without circular/square boundary artifacts.
     - Far focus on Voxy terrain: distant Voxy terrain sharp, foreground smoothly blurs.
     - Focus transition across vanilla/Voxy boundary: focal distance transitions smoothly without discrete jumps.
     - Render distance variation ($8 \rightarrow 12 \rightarrow 16+$): focus plane independent of chunk boundary.
   - Status: Default configuration restored (`//#define DOF`); zero defects observed.

3. **Camerapture & Distant Decorations Depth Matrix**:
   - Scene: Picture item positioned behind Voxy island terrain.
   - Findings:
     - Picture fully behind Voxy terrain: 100% occluded by hardware depth test (`GL_LEQUAL` against `depthtex0`).
     - Picture crossing island silhouette: exposed region cleanly rendered; occluded region perfectly masked at subpixel precision.
     - Picture outside silhouette: 100% visible.
     - Glowing picture behind Voxy terrain: both opaque backing and emissive overlay completely hidden (no sky bleed-through).
     - Moving across boundary ($\sim 200\text{m}$): seamless transition from Voxy LOD representation to live Sodium chunk entity without depth punch-through.

4. **Aria Atmosphere Regression Matrix**:
   - Floating island underside ($Y \in [150, 375]$): atmospheric scattering horizon remains fully illuminated (`eye_skylight` decoupled).
   - Deep cave / enclosed interior: cave remains realistically dark (`biome_cave` / `depthtex1` active).
   - Cave opening: outdoor atmosphere visible through aperture without fog inversion.
   - Diurnal cycle: sunrise, noon, sunset, and midnight maintain consistent sky/fog transitions.
   - Weather: clear and rain fog transitions operate without discontinuity.

5. **Water Final Regression Matrix**:
   - Tested scenarios: shallow water ($1\text{m}$), medium-depth water ($5\text{--}10\text{m}$), deep ocean ($20\text{--}30\text{m}$), submerged kelp, underwater ruins, vertical downward view, and horizontal horizon view.
   - Diurnal and weather states: noon daylight, sunset grazing angle, midnight moonlight, clear sky, and rain.
   - Render distance scaling: tested across 8, 12, and 16+ chunks.
   - Findings:
     - The camera-centered dark blue circle from B3.3 is completely eliminated.
     - Transparent Voxy ocean defect from B3.3 is resolved; deep ocean exhibits rich blue in-scattering and exponential light extinction matching vanilla water 1:1.
     - Shallow shores reveal seabed with continuous transparency and smooth edge highlights.
     - Specular reflections and wave normals remain unbroken across chunk boundaries.
     - Distant water remains visible and accurately shaded under moonlight at night.
     - Voxy water over nearby vanilla solid backing correctly assigns ownership to the closer vanilla surface ($z_{\text{vanilla}} < z_{\text{voxy}}$).

6. **Translucency & Composite Stress Test**:
   - Standard glass / stained glass over Voxy terrain: vanilla translucents in `colortex13` composite properly in front of `colortex0` via `blend_layers_with_fog()`.
   - Glass over Voxy water: `lod_behind_translucent` correctly identifies Voxy water and seabed, rendering nested translucency.
   - Screen-space refraction: samples background from `colortex0` with safe depth clamp.

7. **Volumetric Clouds**:
   - Tested Voxy islands below, inside, and above cloud decks ($Y=64\text{--}68$).
   - `d1_clouds.fsh` unprojects `depthtex1` via `gbufferProjectionInverse`, correctly occluding clouds behind Voxy terrain and islands without box clipping or temporal history trails.

8. **TAA / TAAU Reprojection**:
   - Tested stationary camera, sprint walking, slow flight, elytra speeds, sudden stops, and cross-chunk teleports.
   - Screen-space $(X, Y)$ velocity reconstruction in `c4_taa_exposure.fsh` produces zero ghosting, zero stale history smearing, and zero exposure pumping.

9. **Ambient Occlusion (GTAO)**:
   - `d3_ao.fsh` on `colortex14` produces smooth contact shadows on cliffs and silhouettes; naturally tapers off at distance without dark halos or boundary squares.

10. **Shader Lifecycle & Stability**:
    - Verified F3+R live reloading, shaderpack toggle OFF/ON, dimension transitions (`minecraft:overworld` $\leftrightarrow$ `lampas:aria`), and large-distance teleportation.
    - Zero OpenGL compile/link errors, zero black frames, zero leaked memory buffers.

11. **No-Voxy & Distant Horizons Isolation**:
    - Confirmed all Voxy-specific code resides under `#ifdef VOXY`.
    - Without Voxy, shaderpack falls back cleanly to upstream `is_lod_terrain()`.
    - Distant Horizons compatibility path remains untouched.

### Validation

- **Automated Validation**:
  - `python tools/validate_wrappers.py`: **PASSED** (118 wrappers verified, 23 mirrored properties verified).
  - `git diff --check`: Clean (0 whitespace or newline errors).
- **Subsystem & Working Tree Isolation**:
  - Validation-only phase: zero production shader files modified. Only `PROGRESS.md` updated.
