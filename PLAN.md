Yeah. Given the current state of both repos, I’d make this a **dedicated Aria atmosphere/cave-classification phase**, not a random “increase brightness” patch.

The important part is that this belongs primarily in **`lampas-photon-aria-shader`**. `lampas-aria` should be treated as the dimension contract/reference and should not be changed unless testing proves a vanilla-side defect. Aria already has `has_skylight: true`, `has_ceiling: false`, and `ambient_light: 0.0`; those are reasonable values for a floating-island dimension.

Also, the agent has to obey the shader repo's `AGENTS.md`: define scope/acceptance criteria, record material work in `PROGRESS.md`, commit+push after every completed phase, and **STOP after every phase for review**.

# Full agent plan — Fix Aria under-island blackness

## Execution contract

Work in:

```text
justbecauseph/lampas-photon-aria-shader
```

Reference only:

```text
justbecauseph/lampas-aria
```

Before touching shader code:

```text
1. Read AGENTS.md
2. Read PLAN.md
3. Read PROGRESS.md
4. Inspect current git status
5. Do not discard unrelated local work
6. Add the new phase scope + acceptance criteria to PROGRESS.md
7. Implement only that phase
8. Validate
9. Record evidence
10. git diff --check
11. git diff review
12. commit
13. push
14. STOP FOR REVIEW
```

Do **not** batch the phases below.

---

# Phase P9.0 — Reproduce and isolate the black-atmosphere failure

### Goal

Prove which Photon systems are responsible before changing anything.

The screenshot strongly suggests at least two independent mechanisms:

```text
A. local eye skylight → atmospheric scattering collapse
B. biome_cave → explicit sky-to-black operation
```

Photon currently derives:

```properties
uniform.float.eye_skylight = smooth(eyeBrightness.y / 240.0, 1.0, 1.0)
```

so standing underneath a large island can drive the atmospheric input toward zero.

Photon's analytic atmosphere then contains:

```glsl
scattering *= max(skylight, eye_skylight);
```



And Photon independently contains the cave sky blackening:

```glsl
float underground_sky_fade =
    biome_cave * smoothstep(-0.1, 0.1, 0.4 - ray_dir.y);

sky = mix(sky, vec3(0.0), underground_sky_fade);
```



### Reproduction matrix

Pick one large main island with an accessible underside.

Capture the same camera direction from:

```text
A — exposed beside island, same approximate Y
B — just underneath island edge
C — deep underneath island center
D — genuinely enclosed cavity inside island
E — open air below all island terrain
```

Prefer daytime/noon first.

Record:

```text
eyeAltitude
eyeBrightness / eye_skylight if debug instrumentation is practical
biome_cave
weather
time
camera coordinates
```

Test at least:

```text
noon
sunset
midnight
```

Do one clear-weather pass first.

### Temporary diagnostic only

If useful, introduce an **uncommitted temporary debug visualization** for:

```text
R = biome_cave
G = eye_skylight
B = 0
```

or use existing Photon debug infrastructure.

Remove diagnostic code before completing the phase.

### Acceptance criteria

Prove or disprove:

```text
under island:
    eye_skylight ≈ 0

and/or:
    biome_cave becomes non-zero

while:
    the player is still in open Aria atmosphere
```

Also establish whether the black region is:

```text
sky only
fog only
terrain only
or multiple systems together
```

### No production shader changes

This is diagnosis only.

### Commit

```text
Document Aria under-island darkness diagnosis
```

Push and **STOP**.

---

# Phase P9.1 — Decouple Aria atmospheric scattering from local roof skylight

This is the first actual fix.

### Goal

An island above the player's head may shadow the **player and terrain**, but it must not make kilometres of surrounding atmosphere stop scattering sunlight.

### Target

```text
shaders/include/fog/overworld/analytic.glsl
```

Current terminal scaling:

```glsl
scattering *= max(skylight, eye_skylight);
```

Photon applies this analytic fog directly over the sky map.

### Implementation

Introduce an Aria-specific atmosphere illumination factor.

Conceptually:

```glsl
float atmosphere_skylight = max(skylight, eye_skylight);

#ifdef WORLD_ARIA
    atmosphere_skylight = 1.0;
#endif

scattering *= atmosphere_skylight;
```

But before settling on exactly `1.0`, verify what the `skylight` argument represents at each caller.

The desired semantic is:

```text
local roof occlusion must NOT extinguish atmospheric in-scattering
```

It is **not**:

```text
force daytime
force white fog
ignore sun/moon cycle
ignore weather
ignore blindness/darkness effects
```

Keep these intact:

```glsl
ambient_color
light_color
light_dir
sun_dir
rainStrength
blindness
darknessFactor
evening_glow
```

### Call-site audit

Check at minimum:

```text
program/d0_sky_map.fsh
program/c1_blend_layers.fsh
include/lighting/specular_lighting.glsl
```

All currently feed `eye_skylight` into analytic atmosphere paths.

Prefer fixing the shared implementation rather than patching every caller.

### Test matrix

Repeat:

```text
open sky
under island edge
under island center
inside genuine enclosed cave
```

At:

```text
noon
sunset
midnight
```

### Expected result

Underneath the island:

```text
BEFORE
terrain silhouette → BLACK VOID

AFTER
terrain silhouette → illuminated blue/atmospheric background
```

The island underside should **remain dark**.

### Regression requirements

Overworld must be byte/behavior equivalent with respect to this branch:

```text
WORLD_ARIA only
```

Do not globally alter Photon's atmosphere.

### Acceptance criteria

- black atmospheric void substantially disappears;
- island underside remains shadowed;
- noon/sunset/night still visually distinct;
- blindness/darkness still work;
- Overworld unchanged;
- no shader compilation/link errors.

### Commit

```text
Preserve Aria atmospheric scattering under floating islands
```

Push and **STOP**.

---

# Phase P9.2 — Disable false cave-sky blackening in Aria

P9.1 may fix most of the screenshot, but this one removes the second incorrect assumption.

### Problem

Photon's `biome_cave` is based partly on being below approximately vanilla sea level plus lack of skylight:

```text
low altitude + low skylight = cave
```

That makes sense in the Overworld.

It is wrong in Aria.

Aria intentionally has open atmosphere from its lower boundary upward and has floating land beginning much higher. Its main islands are approximately Y150–270 and high islands Y280–375.

### Target

```text
shaders/include/sky/sky.glsl
```

Current cave sky behavior explicitly mixes toward zero.

### Implementation

Scope the cave sky fix away from Aria:

```glsl
#if !defined PROGRAM_DEFERRED0 && !defined WORLD_ARIA

float underground_sky_fade =
    biome_cave * smoothstep(-0.1, 0.1, 0.4 - ray_dir.y);

sky = mix(sky, vec3(0.0), underground_sky_fade);

#endif
```

Or equivalent structure preserving upstream behavior exactly.

### Important non-goal

Do **not** globally force:

```glsl
biome_cave = 0
```

yet.

There are multiple consumers of `biome_cave`, and some may still be aesthetically useful inside genuine enclosed Aria terrain.

This phase disables only the clearly invalid:

```text
"lower sky should become pure black because this looks cave-like"
```

behavior.

### Acceptance criteria

When looking outward/downward from beneath an island:

```text
sky remains atmospheric
no hard black lower hemisphere
no horizon discontinuity
```

Inside a real hole/cave:

```text
local terrain remains dark because Minecraft skylight/shadow/AO are still low
```

Overworld's cave behavior must remain untouched.

### Commit

```text
Disable cave sky blackening in Lampas Aria
```

Push and **STOP**.

---

# Phase P9.3 — Audit every remaining `biome_cave` consumer

Now that the two major mechanisms are fixed, inspect everything else systematically.

### Search

Audit every reference to:

```text
biome_cave
eye_skylight
eyeBrightness
cave_fog
CAVE_LIGHTING_I
```

Known relevant consumers already include:

```text
include/fog/simple_fog.glsl
program/d4_deferred_shading.fsh
program/c14_color_grading.fsh
include/lighting/diffuse_lighting.glsl
include/fog/overworld/raymarched.glsl
```

For example, cave fog density is multiplied directly by `biome_cave`.

Border atmospheric color also gets suppressed with:

```glsl
(1.0 - biome_cave)
```



And color grading increases vignette strength using `biome_cave`.

### Classification

Classify each consumer:

```text
A — definitely wrong for open Aria atmosphere
B — useful for actual enclosed caves
C — harmless visual grading
D — requires runtime test
```

Document the table in `PROGRESS.md`.

Example expected classification:

| Consumer | Likely policy |
|---|---|
| sky → black | disable in Aria |
| atmospheric border fog → zero | likely disable in Aria |
| cave fog | probably suppress or redesign |
| cave lighting | probably retain |
| vignette | probably retain unless visually annoying |
| Purkinje/night vision | retain unless reproduction proves wrong |

### Implementation rule

Do **not** make a blanket search-and-replace.

Only add `WORLD_ARIA` branches where a consumer interprets:

```text
"roof above player"
```

as:

```text
"entire world is underground"
```

### Acceptance criteria

- no remaining black atmospheric band;
- no black border fog;
- no sudden cave fog underneath an open island;
- legitimate enclosed spaces can still look darker;
- Overworld unchanged.

### Commit

```text
Harden Photon cave effects for Aria atmosphere
```

Push and **STOP**.

---

# Phase P9.4 — Audit raymarched fog / volumetric lighting

Analytic fog is not the only skylight-sensitive path.

Photon's raymarched fog currently does:

```glsl
if (!sky) {
    light_sky[0] *= max(skylight, eye_skylight);
    light_sky[1] *= max(skylight, eye_skylight);
}
```



### Goal

Determine whether volumetric fog beneath islands still becomes implausibly black after P9.1–P9.3.

### Do not preemptively change it

This path operates on **scene fog**, not simply the infinite atmosphere, so some occlusion response is correct.

The question is whether it overuses camera-local skylight for an enormous volume.

### Test

Enable the relevant Photon volumetrics:

```text
VL on
LPV/VL variants where applicable
```

Test:

```text
outside island
edge shadow
center shadow
between two islands
genuine enclosed cave
```

Look specifically for:

```text
a vertical curtain of darkness
fog turning black immediately after passing under terrain
light shafts disappearing globally
large region taking camera-local lighting state
```

### Possible fix if reproduced

Use an Aria-specific lower bound rather than unconditional `1.0`.

For example, conceptually:

```glsl
#ifdef WORLD_ARIA
float effective_skylight =
    max(max(skylight, eye_skylight), aria_atmosphere_floor);
#else
float effective_skylight =
    max(skylight, eye_skylight);
#endif
```

But **derive/tune the floor visually**. Don't blindly choose a magic constant.

The distinction should remain:

```text
ambient atmosphere = visible
deep cave = dark
```

### Acceptance criteria

Volumetric lighting/fog does not recreate the giant black void with VL enabled.

### Commit

Only if code changes:

```text
Tune Aria volumetric atmosphere beneath islands
```

Otherwise use a validation-only progress commit.

Push and **STOP**.

---

# Phase P9.5 — Preserve intentional underside shadows

This is important because we absolutely do **not** want to turn Aria into fullbright.

### Goal

Verify terrain itself still responds correctly to:

```text
sun shadow
skylight
AO
SSAO/GTAO
bounced lighting
block light
emission
night vision
```

Photon's diffuse lighting already has separate ambient/cave illumination mechanisms, including `CAVE_LIGHTING_I`.

### Test three surfaces

Use the same material if possible:

```text
1. island top in direct sun
2. vertical island side
3. island underside
```

Desired ordering:

```text
top > side > underside
```

But:

```text
underside != featureless #000000
```

when surrounded by bright daytime atmosphere.

### Do not solve with

```text
dimension ambient_light
global gamma
huge CAVE_LIGHTING_I
removing shadows
forcing light_levels.y
forcing eyeBrightness
```

Those would destroy the visual hierarchy instead of fixing the atmosphere.

### Optional adjustment

Only if the actual underside geometry remains too crushed after the atmosphere is fixed, introduce a **small Aria-specific ambient/bounced-light floor** in the diffuse lighting stage.

That would be a separate carefully bounded change.

Conceptually:

```glsl
#ifdef WORLD_ARIA
    lighting += small_aria_ambient * ao * directional_lighting;
#endif
```

But only after proving it is needed.

### Acceptance criteria

At noon:

```text
island top      bright
island side     moderate
island underside dark but readable
background sky atmospheric and bright
```

At night:

```text
everything appropriately darker
no artificial fullbright underside
```

### Commit if necessary

```text
Tune Aria floating-island underside lighting
```

Push and **STOP**.

---

# Phase P9.6 — Exposure and color-grading regression

Fixing the sky can expose another problem: Photon's exposure adapts based on the screen.

Under an island you can easily have:

```text
90% dark terrain
10% very bright sky
```

which is a nasty auto-exposure case.

### Test

With auto exposure enabled:

```text
walk from sunlight → island shadow
look toward bright horizon
look straight into underside
turn 180°
leave the shadow
```

Slow and rapid camera movements.

Look for:

```text
black crush
white sky blowout
exposure pumping
1–2 second adaptation lag
vignette becoming excessive
```

### Policy

Do not globally alter Photon's exposure.

Only add Aria tuning if the previous lighting fixes reveal a reproducible Aria-specific adaptation problem.

### Acceptance criteria

Smooth transitions without:

```text
instant blackout
flashbang horizon
persistent exposure mismatch
```

### Commit if changed

```text
Tune Photon exposure for Aria island shadows
```

Push and **STOP**.

---

# Phase P9.7 — Distant Horizons / Voxy atmospheric consistency

Your screenshot includes a huge distant scene, so this matters.

### Goal

Make sure:

```text
vanilla/Iris terrain
Voxy terrain
Distant Horizons terrain
actual sky
fogged horizon
```

all agree about the illumination underneath islands.

### Test

From under a large island:

```text
near terrain
mid-distance terrain
LOD transition band
far island silhouettes
sky behind islands
```

Check with whichever of Voxy/DH are present in the Lampas client.

### Look for

```text
near atmosphere blue, far atmosphere black
LOD terrain black while vanilla terrain readable
hard lighting seam at LOD boundary
different fog response for DH/Voxy
```

Do not patch DH/Voxy paths unless a discrepancy is actually reproduced.

### Acceptance criteria

No distance-dependent return of the giant black void.

### Commit if needed

```text
Align Aria LOD atmosphere under floating islands
```

Push and **STOP**.

---

# Phase P9.8 — Full visual matrix

Once all implementation phases are done, run the proper torture test.

### Altitudes

Use approximately:

```text
Y -40
Y 0
Y 60
Y 66
Y 80
Y 100
Y 150
Y 220
Y 330
Y 375
Y 400
```

The dimension contract places the cloud deck at Y64–68 and the production island strata much higher.

### Positions

At each useful island altitude:

```text
open atmosphere
island edge
under small island
under huge island
between overlapping islands
inside real cavity
```

### Time

```text
sunrise
noon
sunset
midnight
```

### Weather

```text
clear
rain
thunder
```

### Shader profiles

At least:

```text
medium
high
ultra
```

And check major toggles that affect this problem:

```text
SH_SKYLIGHT
GTAO
VL
BLOOMY_FOG
AUTO_EXPOSURE
CAVE_FOG
SHADOW
CLOUD_SHADOWS
```

### Required visual invariants

```text
✓ daytime horizon does not become pure black under an island
✓ distant sky remains visible beneath floating terrain
✓ island underside remains convincingly shadowed
✓ actual enclosed caves remain dark
✓ no horizon seam
✓ no fog wall
✓ no exposure flash
✓ no profile-specific regression
✓ no Overworld behavior change
```

### Commit

```text
Validate Aria atmosphere beneath floating islands
```

Push and **STOP**.

---

# Phase P9.9 — Automated regression protection

The shader validator cannot judge screenshots, but it can prevent architectural regressions.

### Extend repository validation

Add assertions such as:

```text
WORLD_ARIA still exists in all Aria wrappers

Overworld wrappers do NOT gain WORLD_ARIA

the cave-sky blackening code has an Aria exclusion

the analytic atmosphere contains its intentional Aria branch

stock Overworld expressions remain available in the non-Aria path

no global changes to:
    SEA_LEVEL
    SKYLIGHT_I
    CAVE_LIGHTING_I
    ambient values
```

If P9.3 introduces a helper such as:

```glsl
aria_atmosphere_skylight(...)
```

test its presence and isolation.

### Acceptance criteria

```text
python tools/validate_wrappers.py
```

and the eventual consolidated validator pass.

`git diff --check` clean.

### Commit

```text
Add Aria atmosphere regression validation
```

Push and **STOP**.

---

# Phase P9.10 — Documentation

Update:

```text
README.md
PLAN.md
PROGRESS.md
```

And possibly Aria's existing Photon compatibility documentation if it is intended to remain the cross-repo technical spec.

Explain the design distinction:

```text
Minecraft skylight:
    local block-space illumination

Photon atmospheric illumination:
    large-scale sky/air scattering

Aria:
    a floating island may occlude the former without extinguishing the latter
```

Document that this is deliberately **not** implemented via:

```text
ambient_light > 0
fullbright
global cave-light increase
disabled shadows
```

### Commit

```text
Document Aria floating-island atmosphere behavior
```

Push and **STOP**.

---

## What I expect the actual code diff to converge to

The minimal correct production fix will probably be surprisingly small:

```text
include/fog/overworld/analytic.glsl
    → prevent local eye skylight from zeroing Aria's global atmosphere

include/sky/sky.glsl
    → don't use Photon's cave sky-to-black hack in WORLD_ARIA
```

Then possibly:

```text
include/fog/simple_fog.glsl
program/d4_deferred_shading.fsh
include/fog/overworld/raymarched.glsl
```

if live testing shows secondary cave assumptions still leaking through.

I would **not touch `lampas-aria`'s `ambient_light: 0.0`** during this effort. The shader is currently taking perfectly valid local darkness underneath an island and incorrectly promoting it to **“the whole surrounding atmosphere is underground.”** That's the semantic bug we want the agent to eliminate.
