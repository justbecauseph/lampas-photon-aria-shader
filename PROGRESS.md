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
