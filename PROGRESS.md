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
