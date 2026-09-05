Yes. Now that Photon itself lives in a dedicated repo, the plan gets much cleaner. We no longer need a runtime patcher, ZIP fingerprint patch application, or changes in `lampas-aria` just to accommodate Photon. `lampas-photon-aria-shader` becomes the **actual maintained Photon v1.3b derivative for Aria**. That is already how the repo README describes its purpose.

Also, P0 and P1 are already completed: the upstream v1.3b baseline is imported byte-for-byte, the conflict math was audited, and the repo is ready for the dimension mapping work.

One important correction from the earlier plan: now that we have the exact Photon source, the cloud math is clearer. Photon constructs its ray origin as `CLOUDS_SCALE * (eyeAltitude - SEA_LEVEL) + planet_radius`, while the cumulus shell is `planet_radius + CLOUDS_CUMULUS_ALTITUDE`.   Therefore for Aria Y=64 with `SEA_LEVEL=63` and `CLOUDS_SCALE=10`, the correct shader-space cumulus base is **10**, not 1280:

```text
CLOUDS_SCALE × (64 - 63)
= 10 × 1
= 10
```

For a 4-block deck:

```text
10 × 4 = 40
```

So the intended Aria shell is:

```text
radius    = planet_radius + 10
thickness = 40

world Y   = 64 → 68
```

That should be the implementation target.

# Updated Agent Plan — `lampas-photon-aria-shader`

## Agent execution contract

The agent must obey the repository's `AGENTS.md` exactly: material progress goes into `PROGRESS.md`; substantial work gets scope + acceptance criteria before implementation; after **each completed phase**, commit and push; then **STOP for code review**. It must not continue automatically into the next phase.

For every phase, the execution pattern is:

```text
1. Read current repo + PROGRESS.md
2. Define phase scope and acceptance criteria in PROGRESS.md
3. Implement only that phase
4. Validate
5. Record results/evidence in PROGRESS.md
6. git diff / status review
7. commit
8. push
9. STOP
```

Do not batch P2 + P3 + P4 into one run.

---

# P2 — Iris custom-dimension routing

### Goal

Stop Iris from treating `lampas:aria` as generic `world0`.

### Implementation

Add:

```text
shaders/dimension.properties
```

with an explicit Aria mapping.

Before committing, verify the exact syntax against the Iris version actually used by Lampas (`1.11.2+mc26.2`, already recorded in P0).

Expected mapping conceptually:

```properties
dimension.aria = lampas:aria

dimension.world0 = minecraft:overworld *
dimension.world-1 = minecraft:the_nether
dimension.world1 = minecraft:the_end
```

The wildcard must not swallow `lampas:aria`.

### Validation

Confirm:

```text
minecraft:overworld   -> world0
lampas:aria           -> aria
minecraft:the_nether  -> world-1
minecraft:the_end     -> world1
```

Do not create `shaders/aria/` yet.

### Commit

```text
Add Iris dimension mapping for Lampas Aria
```

Push and **STOP**.

---

# P3 — Create the Aria shader program wrappers

This is now especially straightforward because Photon already uses extremely thin dimension wrappers. For example, `world0/deferred1.fsh` is only:

```glsl
#version 400 compatibility
#define WORLD_OVERWORLD
#define PROGRAM_DEFERRED1
#define fsh
#include "/program/d1_clouds.fsh"
```



### Goal

Create an Aria dimension pipeline that behaves like the Overworld while exposing a compile-time specialization flag.

### Implementation

Mirror:

```text
shaders/world0/
```

to:

```text
shaders/aria/
```

Maintain the same wrapper file set.

For every relevant wrapper, retain:

```glsl
#define WORLD_OVERWORLD
```

and add:

```glsl
#define WORLD_ARIA
```

Example:

```glsl
#version 400 compatibility
#define WORLD_OVERWORLD
#define WORLD_ARIA
#define PROGRAM_DEFERRED1
#define fsh
#include "/program/d1_clouds.fsh"
```

Do not copy the contents of `/program/*` into the Aria directory.

### Structural validation

Compare the file inventories:

```text
world0/*  == aria/*
```

except for intentional cases discovered during inspection.

Verify:

- same program include targets;
- same `PROGRAM_*` defines;
- same stage defines (`fsh`, `vsh`, `csh`);
- Aria contains `WORLD_OVERWORLD`;
- Aria additionally contains `WORLD_ARIA`;
- `world0` itself remains byte-for-byte unchanged.

Make sure uncommon wrappers are not forgotten, including things like:

```text
prepare.*
deferred4_a.csh
shadowcomp.csh
voxy*
dh_*
setup.csh
```

### Runtime proof

Enter Aria and ensure Photon compiles the `aria` shader directory successfully before doing any cloud modification.

At this point the visual bug should still exist. That's expected. This phase only proves routing.

### Commit

```text
Add Photon shader wrappers for Lampas Aria
```

Push and **STOP**.

---

# P4 — Centralize Aria cloud geometry

This phase should contain the architectural change, but **not yet every dependent subsystem**.

Photon currently declares the primary cloud shell centrally in:

```text
shaders/include/sky/clouds/constants.glsl
```

as:

```glsl
const float clouds_cumulus_radius =
    planet_radius + CLOUDS_CUMULUS_ALTITUDE;

const float clouds_cumulus_thickness =
    CLOUDS_CUMULUS_ALTITUDE * CLOUDS_CUMULUS_THICKNESS;
```



That's the right place to specialize the geometry.

### Goal

Give Aria a canonical cloud geometry definition without changing Photon's normal Overworld values.

### Implementation

Introduce compile-time Aria constants, preferably adjacent to the cloud geometry or in one small new include such as:

```text
shaders/include/sky/clouds/aria.glsl
```

Conceptually:

```glsl
#ifdef WORLD_ARIA

const float aria_cloud_base_y = 64.0;
const float aria_cloud_thickness = 4.0;

const float clouds_cumulus_radius =
    planet_radius
    + CLOUDS_SCALE * (aria_cloud_base_y - SEA_LEVEL);

const float clouds_cumulus_thickness =
    CLOUDS_SCALE * aria_cloud_thickness;

#else

const float clouds_cumulus_radius =
    planet_radius + CLOUDS_CUMULUS_ALTITUDE;

const float clouds_cumulus_thickness =
    CLOUDS_CUMULUS_ALTITUDE * CLOUDS_CUMULUS_THICKNESS;

#endif
```

The existing:

```glsl
clouds_cumulus_top_radius
```

should remain derived from those values.

### Why hardcode 64 here?

The previous plan suggested using Iris's `cloudHeight` uniform. With the actual Photon source available, that is no longer the best first implementation.

Photon's cloud radii are intentionally declared as compile-time `const float`s.  Turning them into runtime-uniform-dependent values would spread a much larger refactor through the cloud system.

This repo exists specifically for `lampas:aria`, whose cloud contract is Y=64. Therefore:

```text
compile-time WORLD_ARIA constant = safer
runtime cloudHeight refactor     = unnecessary for v1
```

We can revisit dynamic `cloudHeight` only if Aria's cloud height ever becomes configurable.

### Assertions

With:

```text
SEA_LEVEL     = 63
CLOUDS_SCALE  = 10
ARIA_BASE     = 64
ARIA_THICKNESS= 4
```

assert:

```text
radius offset = 10
world base    = 64

thickness     = 40
world top     = 68
```

### Critical non-goals

Do **not**:

```text
change SEA_LEVEL globally
change CLOUDS_SCALE
change CLOUDS_CUMULUS_ALTITUDE globally
modify world0 behavior
move Aria worldgen
```

### Commit

```text
Add Aria-specific Photon cloud geometry
```

Push and **STOP**.

---

### P5 — Close primary cumulus renderer validation

**Goal:** Prove the visible primary renderer is correct and requires no code changes.

Most of this is already demonstrated:

- old Y183–303 cumulus intersection is gone;
- Y150–375 island space is clear of the primary layer;
- Temporal Upscaling `Off/1` removes the checkerboard artifact;
- therefore `d1_clouds.fsh` itself is not the source of that artifact.

Do one final boundary test with Temporal Upscaling **Off**:

```text
Y60 → cloud deck above
Y66 → inside Y64–68 cloud volume
Y80 → cloud deck below
```

No shader modifications unless those three fail.

Record the previous Y151/Y180/Y237/Y350/Y583 tests and the temporal-off comparison in `PROGRESS.md`.

**Commit:**

```text
Validate Aria primary cumulus renderer
```

Push and **STOP**.

---

# P6 — Fix Aria temporal cloud reconstruction

This phase needs a slight redesign from the old plan.

The old plan focused on this stale-looking declaration in `d2_clouds_upscaling.fsh`:

```glsl
const float clouds_cumulus_radius =
    planet_radius + CLOUDS_CUMULUS_ALTITUDE;
```

But the function's actual wind-layer selection does not use it; it selects using the altocumulus and cirrus radii. So replacing that variable with the Aria radius alone would accomplish essentially nothing.

### Actual goal

Fix the **4×4 temporal/checkerboard history rejection** when cloud occupancy changes across a pixel or layer boundary.

The current reconstruction can replace 15/16 pixels with reprojected history:

```glsl
if (offset_0 != offset_1 && !disocclusion) {
    current = history;
    apparent_distance =
        min(apparent_distance, apparent_distance_history);
    ambient_scattering = history_data.z;
}
```

Yet history is currently invalidated mainly for screen/terrain disocclusion, hand rendering, NaNs, and world-age changes—not because the current cloud sample and historical cloud sample fundamentally disagree.

### P6 investigation

Do **not** rely on exact apparent-distance sentinel equality. Photon isn't completely uniform:

```text
clouds_not_hit.apparent_distance = 1e5
some zero-density raymarch results = 1e6
```



The better signals are probably:

```text
current.a                  cloud transmittance
history.a                  historical transmittance
apparent_distance
apparent_distance_history
pixel_age
disocclusion
```

Prototype an Aria-only rejection rule around **cloud-presence disagreement and/or major apparent-distance discontinuity**.

Conceptually:

```glsl
#ifdef WORLD_ARIA

bool current_has_cloud = /* transmittance/visibility test */;
bool history_has_cloud = /* corresponding history test */;

bool cloud_history_invalid =
    current_has_cloud != history_has_cloud;

cloud_history_invalid |=
    /* meaningful distance discontinuity if both contain cloud */;

disocclusion |= cloud_history_invalid;

#endif
```

Don't pick arbitrary thresholds and ship them immediately. Test them.

Also remove the unused local `clouds_cumulus_radius` while here if static analysis confirms it is truly dead, but treat that as cleanup—not the fix.

### P6 test matrix

Test Temporal Upscaling:

```text
Off / 1
4× / 2
9× / 3
16× / 4
```

At least test:

```text
clear
rain
thunder

stationary
fast horizontal flight
fast vertical flight
rapid camera spin
Elytra boost looking backward
```

And specifically revisit approximately:

```text
Y64–68
Y383–431
Y663–753
Y726 screenshot scene
```

The Y726 range matters because that is actually around Photon's current cirrus altitude, so the temporal bug may be a generic layer-boundary problem rather than something uniquely caused by the tiny Y64–68 cumulus shell.

**Acceptance:**

```text
16× temporal upscaling clean
no bright checkerboard squares
no persistent ghost clouds
no excessive shimmer caused by over-invalidating history
no large FPS/GPU regression
Overworld behavior unchanged
```

**Commit:**

```text
Fix Aria cloud temporal history reconstruction
```

Push and **STOP**.

---

# P7 — Audit and harden every remaining cloud layer

This is the old P8, moved ahead of shadows.

We now have live evidence that this phase is necessary.

### Current Photon geometry

The current relevant geometry is roughly:

| Layer | Current effective world range | Problem |
|---|---:|---|
| Primary cumulus | **Y64–68 in Aria** | Fixed |
| Cumulus congestus | approx **Y103–1383** | Huge volume; must audit |
| Altocumulus / altostratus | approx **Y383–431** | Only ~8 blocks above high-island envelope |
| Cirrus | approx **Y663–753** | Safely above islands, but directly relevant around Y726 |
| Noctilucent | ~Y8063 | Irrelevant to island intersection |

The alarming one is **cumulus congestus**. Stock Photon defines:

```text
CLOUDS_CUMULUS_CONGESTUS_ALTITUDE = 400
CLOUDS_CUMULUS_CONGESTUS_THICKNESS = 32
```

and constructs its own independent spherical shell.

That translates to approximately:

```text
base = 63 + 400 / 10
     = Y103

thickness = (400 × 32) / 10
          = 1280 blocks

top = Y1383
```

It is distance-limited and weather/blend-dependent, so that does **not** mean the entire world is constantly buried in it—but its geometry absolutely crosses the entire Aria island band.

Altocumulus remains at `3200` shader units with `0.15` thickness, i.e. roughly Y383–431.

Cirrus is currently based around `6000`, putting it near Y663; with the existing thickness formula its band extends roughly to Y753.

### Weather explains your thunder screenshot

Photon explicitly turns layer 1 toward **altostratus** under high wind/humidity, and cirrus amount also increases with `rainStrength`.

That's why `/weather thunder` is such a useful torture test.

### P7 policy

Classify every cloud path:

```text
A — dense volume that must stay out of Y150–375
B — thin/high decorative cloud that may remain
C — primary-cloud variant that should inherit Aria geometry
D — inactive/optional path that still needs a safe Aria behavior
```

Audit:

```text
primary cumulus
cumulus congestus
altocumulus
altostratus weather state
cirrus
cirrocumulus
noctilucent
BLOCKY_CLOUDS
weather-generated cloud parameters
```

### Likely decisions

**Altocumulus/altostratus:** probably needs adjustment. Y383 is simply too close to high islands ending around Y375, especially when thunder turns it into a dense sheet. Either lift it clearly above the dimension's island/build space or reduce the dense altostratus component specifically for `WORLD_ARIA`.

**Congestus:** definitely deserves special treatment. Don't blindly attach its current 1280-block vertical tower to the new Y64 deck. Good options are to suppress congestus in Aria, redesign it as distant horizon weather, or give it an Aria-specific shell that cannot consume the island stratum.

**Cirrus:** probably leave it high. It provides useful high-cloud structure and is well above the islands. Only change it if the Y663–753 live tests reveal an actual problem.

**Noctilucent:** almost certainly leave alone.

**Blocky clouds:** when enabled, make sure their Aria path honors the intended deck rather than resurrecting an unrelated Overworld altitude.

Test clear/rain/thunder at:

```text
Y100
Y150
Y220
Y330
Y375
Y400
Y494
Y583
Y663
Y726
Y760
```

**Acceptance:** no dense weather layer materially obscures the Y150–375 islands.

**Commit:**

```text
Harden Photon cloud layers for Aria
```

Push and **STOP**.

---

# P8 — Validate cloud shadows against final cloud geometry

This is the old P7, intentionally moved after P7.

That ordering matters because `cloud_shadows.glsl` renders cumulus, congestus, altocumulus and cirrus. Validating shadows and *then* moving those layers would make the shadow validation stale.

The good news is that the shadow code already consumes the shared cloud constants, including the Aria-aware primary cumulus radii.

### Validate

Terrain around:

```text
Y50
Y64
Y80
Y150
Y220
Y330
Y375
Y400
```

Under:

```text
clear
rain
thunder
morning
noon
sunset
```

Look for:

```text
phantom shadows at old Y183–303
dark horizontal bands
upper-cloud shadows projected from wrong altitude
islands treated as if inside cloud volume
mismatch between visible cloud and its ground shadow
```

Only change `cloud_shadows.glsl` if the final shared geometry isn't sufficient.

Do **not** change:

```glsl
eyeAltitude - SEA_LEVEL
```

merely because Aria worldgen uses `sea_level = -64`.

If no shader change is needed, record a validation-only commit.

**Commit if code changes:**

```text
Align Aria cloud shadows with final cloud geometry
```

Push and **STOP**.

---

# P9 — Atmosphere, horizon and fog audit

By this point cloud geometry should be finished.

This phase now has some actual evidence already: several of your lower-altitude screenshots show a very dark/black lower hemisphere underneath the floating islands. That may or may not be desirable, but it belongs here—not in the cloud phases.

Test:

```text
Y-40
Y0
Y64
Y100
Y150
Y220
Y330
Y400
```

At:

```text
sunrise
noon
sunset
midnight
rain
thunder
```

Inspect:

```text
black void beneath islands
horizon seam
sky-ground treatment
fog below islands
exposure changes crossing the cloud deck
sun/moon
stars
rain/thunder atmosphere
distant Voxy terrain blending
```

Keep `WORLD_OVERWORLD` inheritance. Add `WORLD_ARIA` atmosphere branches **only for defects you can reproduce**.

**Commit if needed:**

```text
Tune Photon atmosphere for Lampas Aria
```

Push and **STOP**.

---

# P10 — Dimension-transition hardening

Now hammer the actual Lampas transition behavior.

At least ten cycles:

```text
Overworld → Aria
Aria → Overworld
```

Also:

```text
commands
actual ascent seam
actual descent seam
Elytra crossing at speed
crossing while raining
crossing while thunder
crossing then immediately spinning camera
```

Verify:

```text
correct world0 ↔ aria program switch
no old cloud history
no old weather layer history
no stale shadow map
no exposure flash
no black frame
no old Y183–303 clouds for one frame
no Voxy/Iris pipeline corruption
```

Any history-clearing fix discovered here should be narrowly tied to dimension/pipeline transitions.

**Commit:**

```text
Harden Photon state across Aria transitions
```

Push and **STOP**.

---

# P11 — Consolidated automated regression validator

Turn the ad-hoc phase validators into one repository-native suite.

For example:

```text
tools/validate.py
```

It should cover:

```text
dimension.properties routing

world0 ↔ aria wrapper inventory parity
WORLD_ARIA macro placement
program include existence
program.world0 ↔ program.aria toggle parity

Aria primary cloud math:
  base 64
  top 68

stock Photon math:
  base 183
  top 303

final P7 layer contracts

no accidental WORLD_ARIA in vanilla wrappers

known non-Aria formulas remain unchanged

P6 temporal invariants / forbidden stale patterns
```

Keep `validate_wrappers.py` if useful, or have the new top-level validator invoke it.

Optional GitHub Actions:

```text
python tools/validate.py
```

on pushes/PRs.

**Commit:**

```text
Add Aria shader regression validator
```

Push and **STOP**.

---

# P12 — Cross-dimension visual and performance regression

Compare the derivative against pristine Photon v1.3b.

Dimensions:

```text
Overworld
Nether
End
Aria
```

Overworld/Nether/End should remain visually equivalent except for unavoidable implementation-neutral differences.

For Aria compare:

```text
Temporal Upscaling 1 vs 4
clear vs rain vs thunder
low deck vs islands vs high atmosphere
Voxy near/far terrain
```

Track:

```text
FPS
GPU/frame time if available
obvious cloud cost
shader reload time
memory/VRAM anomalies
```

P6 must not “fix” the checkerboard problem by accidentally destroying temporal reuse and making clouds 16× more expensive.

If no code change is necessary, make this validation-only.

Push and **STOP**.

---

# P13 — Package and release

No runtime patcher.

Ship this repository as the actual derivative shaderpack.

Build something like:

```text
Photon-v1.3b-Lampas-Aria.zip
```

Zip structure:

```text
shaders/
LICENSE
README.md    optional/useful
```

Not:

```text
Photon-v1.3b-Lampas-Aria/
    shaders/
```

if that extra nesting prevents Iris recognizing the pack.

Then install the **ZIP itself** into `.minecraft-lampas` and run a final smoke test. Don't rely only on the development junction.

Record:

```text
Photon base: v1.3b
Iris tested: 1.11.2+mc26.2
Minecraft: 26.2
Aria dimension: lampas:aria
SHA-256 of release ZIP
```

Suggested tag:

```text
v1.3b-lampas-aria.1
```

Push/review before actually tagging if you want to preserve the current review discipline.

---

# P14 — Documentation and upstream-maintenance contract

Finish README/docs with:

```text
what this fork is
why stock Photon breaks Aria
Iris dimension routing
WORLD_ARIA architecture
primary cloud Y64–68 contract
upper-cloud decisions
weather behavior
installation
supported versions
known limitations
known stock Photon preprocessor diagnostic
attribution/license
release process
```

Document future Photon upgrades as:

```text
import/rebase new upstream Photon
re-audit changed cloud implementation
recreate/check aria wrappers
run validator
run temporal tests
run clear/rain/thunder matrix
run transition tests
run cross-dimension regression
```

Do **not** promise that a future Photon version is compatible just because the wrapper tree still applies.

---

## New dependency chain

So from **right now**, I'd run:

```text
P5  finish primary-renderer validation
 ↓
P6  fix temporal/checkerboard reconstruction
 ↓
P7  finalize ALL cloud-layer geometry + weather behavior
 ↓
P8  validate shadows against that final geometry
 ↓
P9  atmosphere/fog/horizon
 ↓
P10 dimension transitions
 ↓
P11 automated regression suite
 ↓
P12 visual/performance regression
 ↓
P13 packaging/release
 ↓
P14 docs/upstream maintenance
```

# Refs:
- C:\Users\markj\source\repos\lampas-aria
