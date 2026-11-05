# Plan — Shader Optimization Audit Follow-up (PERF5, FIX1, PERF6)

Source: read-only audit of 2026-11-05. It covered the sky/clouds, composite/post, gbuffer/shadow, deferred, SSRT and SSR paths. Impact ratings come from counting taps, steps and pass resolution, not from GPU timing.

Validated on 2026-11-05 against the source, with standalone glslang compiles of a scratch prototype (see [Validation Record](#validation-record)). The corrections from that pass are folded into the items below.

## Execution Contract

- Follow `AGENTS.md`:
  - Before implementing a phase, copy its scope and acceptance criteria into `PROGRESS.md`.
  - Record completed work and validation there.
  - Commit and push after every completed phase, then **stop for code review**.
- Phases run in order: PERF5, then FIX1, then PERF6. Do not bundle them.
- Do not claim a speed-up without an in-game measurement. Record the hardware, scene and profile next to every number.
- Keep the PERF1 to PERF4 behaviour, Voxy merged-depth ownership (B3.5 contract), and the Aria routing and wrapper parity intact.
- Standard validation for every phase:
  - `python tools/validate_wrappers.py`
  - `python tools/validate_perf1.py` (needs the PERF5 update described in the [validator update](#validator-update-for-validate_perf1py))
  - `python tools/validate_profiles.py`
  - `git diff --check`
  - Standalone glslang compiles of every touched program. Use world0 and Aria variants, no-LOD and Voxy variants where they apply, and the default, `low` and `lowest` option sets, plus any option sets the phase names.
    - **Compiler:** glslang 16.6.0 at `C:\Users\markj\.local\bin\glslang.exe`.
    - **Harness:** the harness must expand `/`-rooted includes, apply option overrides to `settings.glsl`, inject the Iris `MC_*` macros, and raise the version to `460 compatibility`. The wrappers' `400` profile rejects the existing multi-line directives.
    - **Boundary:** this is a GLSL semantic check, not an Iris link or driver test.

## Measurement Protocol (all phases)

- **Scenes:** use fixed positions and facings at `/time set noon` with clear weather. Scene 6 is the exception.
  1. Overworld vista over Voxy terrain
  2. Dense forest
  3. Distant ocean
  4. Aria under-island horizon
  5. Cave
  6. Rain (`/weather rain`), for the puddle and crepuscular items
- **Before/after:** record F3 average FPS and p98 frame time after 10 s of settling, with VSync off. Use the same profile (High) before and after.
- **Pass timings:** where possible, capture per-pass GPU timings with Nsight, RenderDoc or a driver profiler. Iris has no per-pass GPU timer. FPS on this machine is often CPU-bound (see LS1 closeout), so pass timings are the real evidence. Passes to time:

  | Pass | Program | Covers |
  |---|---|---|
  | `shadow*` | — | shadow map |
  | `deferred1` | `d1_clouds` | clouds |
  | `deferred4` | `d4_deferred_shading` | deferred shading |
  | `composite` | `c0_vl` | volumetric light |
  | `composite1` | `c1_blend_layers` | translucent blend |
  | `composite11` | `c11_bloom_merge_buffers` | bloom merge |
  | `composite14` | `c14_color_grading` | colour grading |
  | `composite16` | `c15_fxaa` | FXAA |

---

## Phase PERF5 — Image-preserving Optimizations

### Scope

Every item must produce the same image apart from floating-point rounding, except where an item says otherwise.

1. **Opaque shadow pass skips texture work.** `program/shadow.fsh:161-171`
   - **Now:** under `PROGRAM_SHADOW_SOLID`, the shader does three things for every opaque shadow fragment:
     - it fetches the texture;
     - it alpha-tests with `discard`;
     - it runs `srgb_eotf_inv` (3 `pow`).

     For texels with alpha 1 the written colour is always 0, because of `step(a, 1 - 1/255)`.
   - **Change:** under `PROGRAM_SHADOW_SOLID`, write `shadowcolor0_out = vec3(0.0)` and skip the fetch, the `discard` and the colour work. With no `discard` left, the GPU's early depth test can work in the shadow pass.
   - **What reaches `shadow_solid`** (from the Iris and Sodium source):
     - Only Sodium terrain. Iris picks `SHADOW_SODIUM_TERRAIN_SOLID` for any Sodium pipeline that has no blending and no `CUTOUT` define (`IrisPipelines.java:224-231`). Iris applies no alpha test to it (`ShaderKey.java:131`, `AlphaTests.OFF`).
     - Sodium adds the `ALPHA_CUTOUT` define only to the CUTOUT and TRANSLUCENT passes (`ShaderChunkRenderer.java:71-75`). So `shadow_solid` receives exactly the SOLID chunk layer.
     - Leaves go into the SOLID layer when the vanilla **Cutout Leaves** option is off. `BlockRenderer.java:94,117` sets `forceOpaque` and switches the material to `ChunkSectionLayer.SOLID`.
   - **Exception (document it):** solid-layer texels with alpha below 1 change.
     - Texels with alpha below 0.1 currently punch holes in the shadow. After the change they cast solid shadow.
     - Texels with alpha from 0.1 up to 1 currently write a tinted colour. After the change they write 0.
   - **Visible case:** with Cutout Leaves off, leaves are drawn opaque (`gbuffers_terrain_solid` doesn't discard), but they currently cast holey shadows because of the pack's own `discard`. After the change their shadows are solid, matching what is drawn. This also affects resource packs with alpha in solid-layer textures.
   - **No exact alternative:** keeping the `discard` for leaves only would keep the old look, but any `discard` in the program turns off the early depth test for the whole pass, which removes the gain. **Owner decision:** accept the change (recommended) or drop the item. Either way, check leaf shadows in game with Cutout Leaves on and off.
2. **Cutout shadow fragments skip colour work when fully opaque.** `shadow.fsh:166-170`
   - **Change:** applies only with `SHADOW_COLOR`, since item 3 covers the other case. After the alpha-test `discard`, if `base_color.a > 1.0 - rcp(255.0)`, write 0 and return before the colour conversion.
   - **Exact:** `step()` already zeroes these texels today.
3. **Shadow colour work only when `SHADOW_COLOR` is on.** `shadow.fsh`
   - **Now:** colour is computed and written even though every `shadowcolor0` reader is behind `SHADOW_COLOR`. The readers are:
     - `pcss.glsl:71,77,138`
     - `raymarched.glsl:133` (colored light shafts, which have needed `SHADOW_COLOR` since U1)
     - the sampler declarations in `c0_vl.fsh`, `c1_blend_layers.fsh` and `d4_deferred_shading.fsh`
   - **Change:** under `#ifndef SHADOW_COLOR`, keep only the cutout alpha test and write a constant 0. This covers the water caustics branch too.
   - **Clear flag:** with `SHADOW_COLOR` off, also stop the per-frame clear.
     - **Why it costs:** Iris always allocates `shadowcolor0`. The `ShadowRenderTargets` constructor builds framebuffers that write to target 0 (`ShadowRenderTargets.java:73-75`, which calls `getOrCreate(0)`). Its clear setting defaults to on (`PackShadowDirectives.java:402`), so every frame Iris clears both of its textures at shadow-map resolution (`ClearPassCreator.java:139-187`).
     - **How Iris reads the flag:** it scans the preprocessed fragment source of every program, including `final`, line by line for `const` directives (`ProgramSet.java:217-266`, `ConstDirectiveParser.java`). The preprocessor (JCPP) runs first (`ShaderPack.java:317`) and keeps comments.
     - **Why the comment block won't work:** text inside a `/* … */` comment is never evaluated as a directive, so a conditional written inside the `buffers.glsl` comment block would always apply. The existing `#ifdef VOXY` there is already ignored, which is harmless: it only means the `colortex16` settings are always read.
     - **Change:** add real code, outside the comment block in `include/buffers.glsl`: `#ifndef SHADOW_COLOR` / `const bool shadowcolor0Clear = false;` / `#endif`. A global `const` after `main()` compiles with or without `SHADOW_COLOR` (glslang).
     - **Exact:** with `SHADOW_COLOR` off nothing samples `shadowcolor0`, so stale contents are never read. Iris still does a full clear when the target is first created.
4. **`c1` reads clouds only behind translucents.** `c1_blend_layers.fsh:444-453`, `include/sky/clouds/sampling.glsl:17-18`
   - **Change:** move `read_clouds_and_aurora()` and its two output variables inside `if (is_translucent || is_translucent_lod)`. Its outputs have no other consumer in `c1`.
   - **Required companion edit:** the lightning-flash read uses `texture(colortex12, …)`. That is an implicit-derivative lookup, and inside a non-uniform branch its derivatives are undefined. Change it to `textureLod(colortex12, …, 0.0)`. `colortex12` has no mipmaps, so the result is unchanged.
   - The other reads (`texelFetch`, `textureGather`, and `textureLod` on `colortex11`) are safe in non-uniform control flow.
5. **Crepuscular rays return early at zero strength.** `include/sky/crepuscular_rays.glsl:8-30`
   - **Change:** return `vec4(vec3(0.0), 1.0)` when `clouds_params.crepuscular_rays_amount == 0.0`. The function already always returns `w = 1`.
   - **Exact:** scattering is multiplied by the amount (`:133`) and the extinction is `dampen(amount) * …`, which is 0. That makes `step_transmitted_fraction` 0 and the output 0.
   - **Use exact zero, not `< eps`:** the amount comes from a clamped `linear_step` (`weather/clouds.glsl:175-182`), so it is exactly 0 in the cases that matter. `< eps` would drop tiny non-zero contributions.
   - **Callers:** `d1_clouds.fsh:232-239` and `sky.glsl:256-259` both apply `.w` as a multiply and `.xyz` as an add, so the neutral value is correct for both.
6. **VL shadow fetch only inside the shadow map (air and End fog).** `include/fog/overworld/raymarched.glsl:123-150`, `include/fog/end_fog_vl.glsl:139-148`
   - **Now:** the shadow textures are fetched every step, and out-of-map results are masked afterwards. Those out-of-map reads are undefined in GL.
   - **Change:** start with `shadow = 1.0` (`vec3(1.0)` on the colored path) and fetch only when `clamp01(shadow_screen_pos) == shadow_screen_pos`. In End fog, also delete the unused `depth0` fetch (`:142`).
   - **Exact:**
     - *Plain path:* outside the map it computes `step(0.0, depth1)`, which is 1 for any depth value.
     - *Colored path:* it already selects `vec3(1.0)` outside the map.
   - **Water fog is excluded** (`water_fog_vl.glsl:84-103`). It uses the out-of-map `depth0` to compute `distance_traveled`, so today's result there depends on undefined data and cannot be preserved. It moves to FIX1 item 13.
   - **Optional:** compute the exit step once with a slab test and split the loop in two.
7. **Zero-length air-fog early-out in every Overworld-family world.** `raymarched.glsl:93-97`
   - **Change:** remove the `#ifdef WORLD_ARIA` gate.
   - **Exact:** the legacy zero-length march runs 8 steps with `step_length = 0`. Each step has transmittance 1 and transmitted fraction `(1 - 1) / eps = 0`, so it returns `(0, 1)`. `validate_perf1.py` already models this.
8. **Cloud layers that hit no cloud return early.** `clouds/cumulus.glsl:372-402`, `altocumulus.glsl:368-398`, `cumulus_congestus.glsl:343-389`
   - **Change:** right after the primary loop, `if (distance_weight_sum == 0.0) return CloudsResult(vec4(0.0), 1.0, 1e6);`. This skips the three `atmosphere_transmittance` calls and the aerial perspective.
   - **Why it's neutral:** with zero weight, every sample had zero post-fade density. Scattering is then 0, transmittance 1, and the apparent distance is already the 1e6 sentinel, not `clouds_not_hit`'s 1e5.
   - **PERF1 interaction:** the Aria zero-length paths return earlier and are unaffected.
   - **Rounding:** today's output is `linear_step(0.075, 1, 1)`. With true division that is exactly 1. If a driver lowers division to reciprocal-and-multiply it is 0.99999994, plus about 6e-8 × clear-sky scattering, so the early return differs only at rounding level.
9. **Stars skip invisible work.** `include/sky/stars.glsl:6-25`
   - **Change:** in `unstable_star_field`, return `vec3(0.0)` when `star == 0.0` after the `linear_step`. This skips `pow16`, `blackbody` and the twinkle `cos`.
   - **Daytime:** `GALAXY` is off by default and the coverage term is 0 by day, so `star_threshold` is exactly 1. `linear_step(1, 1, x)` then clamps −∞ to 0 for every star (checked numerically). The per-texel return covers that case; a separate frame-uniform check is optional.
10. **FXAA fetches its corners late.** `c15_fxaa.fsh:55-94`
    - **Change:** fetch the corner texels a, c, g and i after the local-contrast early exit (`:83-86`). The exit returns `e` and uses only the cross-shaped neighbours. All fetches are `texelFetch`.
11. **Rain puddles reject early.** `include/surface/rain_puddles.glsl:30-42, 86-105`
    - **Change:** before the noise fetch, return `false` when `flat_normal.y < 0.99` or `light_levels.y <= 14.0 / 15.0`. Either condition makes `puddle` exactly 0, which is already rejected at `:72`.
    - **Ripples:** skip them when `rainStrength == 0.0`. `mix(normal, ripple, 0)` returns `normal` exactly. Keep the final `normalize_safe`.
12. **Frame-uniform colour-grading work moves out of the fragment shader.** `c14_color_grading.fsh:114-117, 174-181, 191`; `c14_color_grading.vsh`
    - **Exposure and vignette:** pass the exposure (the `colortex5` texel at (0,0)) and the vignette exponent from the vertex shader as flat varyings. The `.vsh` already does this for `white_balance_matrix`.
    - **Contrast:** skip the contrast step with `if (contrast != 1.0)` on the existing `const float contrast`; the compiler folds it. **Do not use `#if GRADE_CONTRAST != 1.0`:** the preprocessor can't compare floats, and glslang rejects it ("bad expression"). At the default contrast the skipped `log2`/`exp2` round trip differs only at rounding level.
13. **Bloom merge pass only covers the area it copies.** `c11_bloom_merge_buffers.vsh:19`, `.fsh:25-31`
    - **Odd tiles:** tile 1 is x∈[0.5,0.75], y∈[0.75,1]. Tiles 3 and 5 sit inside x∈[0.875,1], y∈[0.9375,1].
    - **Readers:** `c12` and `c13` only read rows inside each tile's y-range, but `c14`'s bilinear tile lookup also reads the row just below each tile's bottom edge. Neither `c12` nor `c13` writes that row; only `c11` does.
    - **Change:** draw the quad over x∈[0.5,1] and y from `0.75 − 2·view_pixel_size.y` to 1. Without the margin, that row would change from today's copied value to stale data.
14. **Unused fog buffers are not sampled when VL is off.** `c1_blend_layers.fsh:218-221, 458-468`
    - **Change:** guard both blocks with `defined VL || (defined LPV_VL && defined COLORED_LIGHTS)`.
    - **Required fallback:** add `#else const vec3 fog_transmittance = vec3(1.0);`. The `BLOOMY_FOG` branch for Overworld without VL (`:509-511`) reads `fog_transmittance`, and without the fallback that configuration fails to compile (reproduced with glslang).
    - **Exact:** when the guard is false, `c0` writes transmittance 1 and scattering 0 (`c0_vl.fsh:230-238`), so the skipped blend is the identity.
    - **Keep `c0` running:** `colortex6` takes part in the AO history swap.
15. **Shadow filter disc taps without per-tap trig.** `include/lighting/shadows/pcss.glsl:43-55, 118-170`; `include/utility/sampling.glsl:4-11`
    - **Now:** each tap computes a `sqrt`, `sin` and `cos`.
    - **Change:** compute `cos`/`sin` of the dither rotation once per pixel, then advance the golden-angle rotation by a constant 2D rotation per tap. Keep the radius term.
    - **Exact:** mathematically identical; drift over at most 32 taps is rounding-level. This was PERF6 item 7.
16. **Fog phase terms once per pixel, not per step.** `include/fog/water_fog_vl.glsl:122-141`, `include/fog/end_fog_vl.glsl:162-179`
    - **Now:** `LoV` and the anisotropy sequence are the same for every step, but the Henyey-Greenstein calls run inside the step loop.
    - **Change:** precompute the phase values before the step loop. Only underwater and End fog are affected. This was PERF6 item 9.

Out of scope: anything that changes the image, which goes to PERF6, and the bugs listed under FIX1.

### Validator update for `validate_perf1.py`

Items 6, 7 and 8 all change non-Aria code in files that `validate_perf1.py` compares with the pre-PERF1 baseline: `raymarched.glsl`, `cumulus.glsl` and `altocumulus.glsl`. Run against the prototype, the validator stops at its first failure, on `raymarched.glsl` ("WORLD_ARIA-disabled source differs from baseline"). Required changes:

- **Baseline edits:** add `LATER_PHASE_EDITS` entries for the item 6, 7 and 8 edits in those three files.
- **Guard checks:** `raymarched.glsl` will have no `WORLD_ARIA` left after item 7. Two checks therefore break:
  - The "contains a `WORLD_ARIA` guard" check must not apply to it.
  - The fast-path checks find the fast path with `fog_source.index("#ifdef WORLD_ARIA", clamp)`, which would raise `ValueError`. Key them on `if (ray_length == 0.0)` instead, and keep the exact-zero and neutral-return assertions.
- **Record:** note every validator change in `PROGRESS.md`.

### Acceptance Criteria

- Each item matches the original output, apart from floating-point rounding, on finite valid inputs. The only exception is item 1's alpha behaviour (leaf shadows with Cutout Leaves off), which needs the owner's approval and must be documented.
- Source review shows each early exit produces the exact neutral value its consumer expects:
  - cloud layers: zero scattering, transmittance 1, apparent distance 1e6;
  - fog: `(0, 1)`;
  - crepuscular rays: `w = 1` and zero scattering;
  - VL shadow outside the map: 1;
  - `shadowcolor0`: 0.
- No implicit-derivative lookup (`texture()` without an explicit LOD, `dFdx`/`fwidth`) is moved into non-uniform control flow.
- Standard validation passes. The `validate_perf1.py` changes are limited to those listed above and are recorded.
- Glslang also compiles these extra option sets:
  - `BLOOMY_FOG` with VL off;
  - `AIR_FOG_COLORED_LIGHT_SHAFTS` with `SHADOW_COLOR`;
  - `COLORED_LIGHTS` with VL off;
  - `GRADE_CONTRAST=1.20`.
- In game on the High profile, the six measurement scenes look unchanged in side-by-side screenshots. Check shadows (including leaves with Cutout Leaves on and off), the Voxy distant water and the Aria horizon. On the Low profile, confirm that shadows still look correct with `SHADOW_COLOR` off and the `shadowcolor0` clear disabled.
- Timings follow the measurement protocol. If none are taken, the phase is recorded as "FPS unverified", as LS1 was.

---

## Phase FIX1 — Correctness Bugs Found During the Audit

### Scope

Every item below was confirmed against the source during validation.

1. **Histogram index out of bounds.** `program/c4_taa_exposure.vsh:105-112`
   - **Now:** `get_bin_from_luminance` can return `HISTOGRAM_BINS - 1`, and the shader then writes `pdf[bin0 + 1]` with weight 0. That write is out of bounds, which is undefined.
   - **Fix:** clamp `bin1` to `HISTOGRAM_BINS - 1`.
   - **Scope:** only `AUTO_EXPOSURE_HISTOGRAM` is affected, and the default is `AUTO_EXPOSURE_OFF`.
2. **Voxy material IDs wrap.** `program/voxy_opaque.glsl:19`, `voxy_translucent.glsl:158`
   - **Now:** `max(customId - 10000u, 0u)` does nothing, because unsigned subtraction wraps.
   - **Fix:** `customId >= 10000u ? customId - 10000u : 0u`.
3. **Sun halo test reads an unassigned variable.** `program/gbuffers_skytextured.fsh:48, 66-69`
   - **Now:** `offset` is declared without a value and read before it is assigned.
   - **Fix (as implemented):** since Minecraft 26.1 the sun is a sprite in the celestials atlas, so moving `offset = uv * 2.0 - 1.0` above the `if` would discard the whole vanilla sun. On 26.1+, `offset` is measured from `uv_mid` and divided by the sprite's half-size in UV (a flat varying); older versions keep `uv * 2.0 - 1.0`. Only `VANILLA_SUN` builds change; check the sun disc and halo cut-out in game with it on.
4. **Wrong value written to cloud history.** `program/d2_clouds_upscaling.fsh:323`
   - **Now:** `history.z = ambient_scattering` overwrites the history's blue channel. The intended target was `history_data.z`, which `:378` and `:408` read.
   - **Fix:** `history_data.z = ambient_scattering`.
   - **Image unchanged:** on disocclusion `pixel_age` is 0, so `history_weight` is exactly 0 and the corrupted channel never reaches the output.
5. **Broken include guards.** `include/sky/clouds/cumulus_congestus.glsl:1` checks `INCLUDe_…`, and `include/sky/sky.glsl:1` checks `INCLUDE_SKY_SKYsky`. Make each guard match its `#define`.
6. **Screen-space shadow jitter missing without LOD mods.** `include/lighting/shadows/ssrt.glsl:176-186`
   - **Now:** the non-LOD path passes `view_light_dir` instead of the jittered `ray_dir` that the LOD path uses.
   - **Before fixing:** check upstream Photon `main` for the intent.
   - **Effect:** soft shadows will look slightly different.
7. **Shadow vertex material ID can be negative.** `program/shadow.vsh:86`
   - **Now:** `uint(mc_Entity.x - 10000.0)` is undefined for unmapped blocks and entities, where `mc_Entity.x` is −1 or 0. The result feeds `update_voxel_map` under `COLORED_LIGHTS`.
   - **Fix:** `uint(max0(…))`, as in `include/vertex/utility.glsl:7`.
8. **`VL_RENDER_SCALE` broken except at 0.5.** `program/c0_vl.fsh:128-130`, `settings.glsl:310`, `shaders.properties:285-286`
   - **Now:** `colortex6`/`colortex7` are fixed at 0.5× size, but the depth texel is divided by `VL_RENDER_SCALE`. At 0.75, depth comes from only the lower-left 2/3 of the screen.
   - **Owner decision required:** remove the option, or support only values ≤ 0.5 with a scaled viewport and scaled `c1` UVs.
9. **Cloud depth footprints skip the centre.** `program/d1_clouds.fsh:131-153`, `d2_clouds_upscaling.fsh:109-127`
   - **Now:** the footprints gather at ±2 px. For a pixel-centred coordinate that covers texel offsets {−2, −1, +2, +3} and skips 0 and +1, including the pixel itself in `d2`.
   - **Fix:** use ±1 px offsets for a contiguous 4×4. This changes the image.
10. **Puddle guard that can never fire.** `include/surface/rain_puddles.glsl:65` tests `wetness < 0.0 || biome_may_rain < 0.0`; it should be `< eps`. Harmless today, because `d4` already guards with `> eps`.
11. **Water parallax reads an uninitialised value.** `include/surface/water_normal.glsl:197-213`
    - **Now:** if the first height is ≤ 0, the loop never runs and `depth_previous` is read without a value.
    - **Fix:** initialise it to `depth_value`. PERF6 item 3 also bounds this loop.
12. **Bloomy fog ignores analytic fog.** `c1_blend_layers.fsh:508-511`
    - **Now:** with VL off, bloomy fog uses VL's `fog_transmittance`, which is neutral there, instead of `analytic_fog[1]`. `BLOOMY_FOG` is off by default.
    - **Fix:** use `analytic_fog[1]`. This changes the image when the option is on.
    - **After PERF5 item 14:** `fog_transmittance` is the constant `vec3(1.0)` in this configuration.
13. **Water VL reads shadow depth outside the shadow map.** `include/fog/water_fog_vl.glsl:84-103` (moved here from PERF5 item 6)
    - **Now:** `depth0` and `depth1` are fetched outside the map, and `depth0` feeds `distance_traveled`.
    - **Fix:** fetch only inside the map. Outside it, use shadow 1 and `distance_traveled = 0`, the same values as the non-shadow branch (`:104-108`).
    - **Effect:** this defines behaviour that is currently undefined, and may change underwater shafts at long range.

**Noted only:** `include/lighting/cloud_shadows.glsl:110,128,139` use `length(pos.xy)`. Since y is about the planet radius, the fade is a near-constant ~4%. This is inherited from upstream, and changing it alters the look of cloud shadows. Leave it unless the owner approves.

### Acceptance Criteria

- Each fix is applied exactly as scoped, and any deviation found during implementation is recorded.
- Fixes that change the image (items 3, 6, 8, 9, 13, and 12 when `BLOOMY_FOG` is on) are checked in game, and the visual difference is recorded. Items 1, 2, 4, 5, 7, 10 and 11 must not change the default-profile image.
- Standard validation passes, and every touched program compiles in its affected variants (`AUTO_EXPOSURE_HISTOGRAM`, `COLORED_LIGHTS`, `BLOOMY_FOG`, Voxy).

---

## Phase PERF6 — Optimizations That Change the Image Slightly (A/B Gated)

### Scope

Implement each item behind its own switch, or as a separately reviewable commit, so it can be A/B tested and reverted on its own.

1. **Cirrus light march.** `include/sky/clouds/cirrus.glsl:16-17, 84, 119-171`
   - **Change:** reuse the view sample's curl noise for the 6 light steps. Also use a cheaper light-step density that skips the cirrocumulus detail and `curl_cc`.
   - **Same density in `p0`:** use it for the cirrus cloud shadow (`cloud_shadows.glsl:136+`) too.
   - **Unverified assumption:** the claim that the curl noise varies too slowly across a light march to matter (period about 50 km) has not been checked. Confirm it before relying on the reuse.
2. **Lighter noise in cumulus-family light and ambient marches.** `cumulus.glsl:79-82, 110-133, 335-346`; `altocumulus.glsl:88-89, 114-138`; `cumulus_congestus.glsl:92-95, 120-144`
   - **Change:** add a level-of-detail flag so secondary samples skip the high-frequency worley noise, at least from the second light step on.
3. **Water normal and parallax.** `include/surface/water_normal.glsl:76-93, 151-154, 197-205`
   - **Change:** turn the parallax `while` into a bounded `for` (`step_count + 2` iterations). Fetch the wave noise and height-variation noise once per pixel for the parallax steps.
4. **Shadow vertex work.** `program/shadow.vsh:103-120`, `include/vertex/displacement.glsl:121-162`
   - **Change:** skip the `shadowModelViewInverse`/`shadowModelView` round-trip unless the material animates. Return early for plant bottom vertices, and compute `player_displacement` only in the plant cases.
   - **Risk:** the differences are rounding-level, but check for shadow acne.
5. **`d1` skips sky work for terrain pixels.** `program/d1_clouds.fsh:195-244`
   - **Change:** when the terrain is closer than the cumulus shell entry and the camera is below the layer, write the cleared outputs and skip atmosphere, aurora and noctilucent clouds.
   - **Risk:** `deferred4` enables `colortex11` mipmaps (`d4_deferred_shading.fsh:155`), so the `textureLod` blur in `read_clouds_and_aurora` does pull in neighbouring values. Check sky/terrain edges.
6. **Cumulus step count follows ray length.** `cumulus.glsl:220-221, 246-249`
   - **Change:** `clamp(ceil(ray_length / min_step), 4u, primary_steps)`. This matters most in Aria's thin cloud layer.
7. **Fewer crepuscular steps for downward rays.** `crepuscular_rays.glsl:62`
   - **Change:** clamp `ray_length` for downward rays, where the underground fade is about 0 (affects `d0` and `d1`).

Former PERF6 items 7 (shadow disc taps) and 9 (fog phase terms) moved to PERF5 items 15 and 16, because they only change rounding.

### Acceptance Criteria

- Each item has before/after screenshots of the relevant scenes:
  - cirrus sky and cumulus overcast (items 1, 2, 6)
  - water close-up (item 3)
  - forest shadows (item 4)
  - Aria cloud sea (items 5, 6)
  - sunset rays (item 7)
- The owner approves each visual difference before it ships.
- Each item has a pass timing taken under the measurement protocol. Items with no measurable gain are dropped or left off by default.
- Standard validation passes. PERF1 metadata contracts and Voxy depth ownership are unchanged.

---

## Checked and Not Recommended

- **`textureGather` for the TAA 3×3 neighbourhood:** RGB needs 3 gathers per 2×2 quad, so it would not reduce fetches.
- **5-tap Catmull-Rom for the TAAU current colour (`c4:336`):** the history and final upscale paths already use 5 taps. Changing this path carries visual risk, and TAAU is off by default.
- **Cheaper bloom downsample (`c5`):** the 13-tap CoD downsample would look visibly different with fewer taps.
- **Transmittance early exit in the air-fog march:** the default fog densities rarely drop transmittance low enough for it to help.
- **Analytic water normals:** the finite-difference noise term dominates the current look, so the change would be visible.

---

## Validation Record

2026-11-05. Source review and standalone compilation only; no game client or GPU run.

- **Validators on the current tree:**
  - wrappers: 118 files and 23 mirrored properties, pass;
  - PERF1: 37 checks, pass;
  - profiles: 5 profiles, pass;
  - `git diff --check`: pass.
- **Compile check of the PERF5 prototype:** a scratch copy of `shaders/` had PERF5 items 1–9, 12 and 14 applied, written the way this plan now specifies. Items 10, 11, 13, 15 and 16 were checked by source review only. glslang 16.6.0 compiled:
  - the shadow programs (solid, cutout, water, entities) and `composite`, `composite1`, `deferred`, `deferred1`, `deferred4`, `composite14` and `prepare`;
  - in world0, Aria, Nether and End variants where present, with Voxy variants for the deferred and composite passes;
  - under 7 option sets: default, `low`, `lowest`, `BLOOMY_FOG` with VL off, colored light shafts with `SHADOW_COLOR`, `COLORED_LIGHTS` with VL off, and `GRADE_CONTRAST=1.20`.

  Baseline: 273/273. Prototype: 273/273.
- **Reproduced failures in the earlier draft of this plan:**
  - `#if GRADE_CONTRAST != 1.0` fails to compile ("bad expression").
  - Item 14 without the `fog_transmittance` fallback fails to compile with `BLOOMY_FOG` on and VL off ("undeclared identifier").
  - `validate_perf1.py` fails on the prototype ("`raymarched.glsl`: WORLD_ARIA-disabled source differs from baseline"). Items 6 and 8 hit the same parity check, as described in the validator update section.
- **Numerical checks (float32):**
  - `linear_step(0.075, 1, 1)` is exactly 1 with true division, and 0.99999994 with reciprocal-and-multiply.
  - `linear_step(1, 1, x)` is 0 for every x < 1 tested (100,000 samples).
  - At zero amount, the crepuscular transmitted fraction is 0.
- **Iris and Sodium source review (2026-11-05):**
  - Sources: Iris `26.2` branch at `4ce5bb6dd` (2026-10-09), and Sodium `26.2/stable` at `9c69d268` (2026-09-20). These are source tips, not the exact Iris 1.11.4 and Sodium 0.9.2 release builds in the modpack.
  - **Routing:** `shadow_solid` receives exactly Sodium's SOLID chunk layer, which includes leaves when Cutout Leaves is off (PERF5 item 1).
  - **Allocation:** `shadowcolor0` is always allocated and, by default, cleared twice per frame. A `shadowcolor0Clear` directive is honoured from real preprocessed code, not from inside a block comment (PERF5 item 3).
  - **Mipmaps:** `colortexNMipmapEnabled` is a per-program directive (`ProgramDirectives.java:108`). This supports PERF5 item 4 (`colortex12` has no mipmaps) and the PERF6 item 5 risk (`colortex11` mipmaps exist).
- **Not verified:**
  - the JCPP comment behaviour was not run; it follows from standard preprocessor rules;
  - GPU filtering exactness of `smooth_filter` on a constant buffer;
  - the speed-up of any item.
