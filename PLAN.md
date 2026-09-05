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

# P5 — Apply Aria geometry to the primary cloud renderer

Now make sure the visible cloud pass actually uses the centralized shell correctly.

Photon's `d1_clouds.fsh` currently constructs the cloud-space camera origin using:

```glsl
CLOUDS_SCALE * (eyeAltitude - SEA_LEVEL) + planet_radius
```

and then feeds that into `draw_clouds()`. 

That camera mapping itself is correct and should generally **remain unchanged**.

The thing we're moving is the cloud shell relative to that coordinate system.

### Validate at these eye altitudes

```text
Y -40
Y 0
Y 60
Y 64
Y 68
Y 100
Y 150
Y 200
Y 330
```

Expected:

```text
Below 64:
    cloud ocean visible above player

64–68:
    player traverses cloud volume

Above 68:
    cloud ocean below player

150–375:
    islands remain clear of primary cumulus
```

### Check terrain intersection

Specifically reproduce the screenshot location/scene that originally exposed the problem.

Required result:

```text
NO dense Photon cumulus inside main/high islands.
```

### Commit

```text
Render Aria cumulus below the floating islands
```

Push and **STOP**.

---

# P6 — Fix temporal cloud reprojection

This needs its own phase because Photon duplicates some cloud-radius assumptions inside temporal upscaling.

In `d2_clouds_upscaling.fsh`, Photon currently redeclares:

```glsl
const float clouds_cumulus_radius =
    planet_radius + CLOUDS_CUMULUS_ALTITUDE;
```

and independently reconstructs camera altitude using `eyeAltitude - SEA_LEVEL`. 

That duplicated radius is now a compatibility hazard.

### Goal

Make temporal reprojection use the same canonical cloud geometry as the renderer.

### Implementation

Remove/rework the local duplicate where practical and consume the shared Aria-aware constants.

Do not create two slightly different Aria formulas.

### Test

Fly rapidly:

- vertically through Y64;
- horizontally above the deck;
- Elytra boost while looking backward;
- rapid camera rotation;
- dimension transition then immediately fly.

Look for:

```text
ghost clouds at Y183
smearing
history trails
popping
wrong wind layer classification
stale old-altitude cloud frames
```

### Required invariant

Renderer and reprojection must both agree that primary Aria cumulus occupies:

```text
Y 64–68
```

### Commit

```text
Use Aria cloud geometry for temporal reprojection
```

Push and **STOP**.

---

# P7 — Fix cloud shadows

Photon already includes the shared cloud constants inside:

```text
include/lighting/cloud_shadows.glsl
```

and uses `clouds_cumulus_radius` / `clouds_cumulus_top_radius` to fade shadows based on whether terrain is above the layer. 

That means part of this may already become correct automatically after P4 — but it must be verified rather than assumed.

### Goal

No phantom cloud shadows from the old Y183–303 volume.

### Validate

At:

```text
terrain Y 50
terrain Y 64
terrain Y 80
terrain Y 150
terrain Y 220
terrain Y 330
```

Expected:

- cloud shadows apply below the cloud layer;
- island surfaces above Y68 should not behave as though embedded inside the cumulus shell;
- shadow map samples correspond to the visible cloud deck;
- no dark floating bands at the former Photon altitude.

### Implementation rule

Only modify `cloud_shadows.glsl` if shared constants alone are insufficient.

Its current ray construction still includes:

```glsl
eyeAltitude - SEA_LEVEL
```

which is expected and consistent with the cloud coordinate system. 

Don't replace that simply because Aria's worldgen sea level is -64.

### Commit

If changes were necessary:

```text
Align Aria cloud shadows with relocated cumulus
```

If no code change is necessary, record validation in `PROGRESS.md`; don't manufacture a meaningless code change.

Push documentation commit if appropriate and **STOP**.

---

# P8 — Audit all other cloud layers

Photon source contains:

```text
cumulus
cumulus congestus
altocumulus
cirrus
noctilucent
blocky clouds
weather clouds
```

in its shared shader tree. 

The original screenshot proves the primary cumulus is wrong, but other layers could independently intersect the islands.

### Policy

Classify each layer as one of:

```text
A. Dense layer — must not intersect Y150–375
B. Thin/high decorative layer — may remain above islands
C. Replacement/variant of primary cumulus — must inherit Aria geometry
D. Not active under current Photon preset — still verify code path
```

Particularly inspect:

```text
CLOUDS_ALTOCUMULUS_ALTITUDE
CLOUDS_CIRRUS_ALTITUDE
cumulus_congestus
BLOCKY_CLOUDS
weather/clouds.glsl
```

### Do not

Do not blindly force every layer to Y64.

Aria can still have high wispy clouds if they look intentional.

Only **dense terrain-obscuring volumes** must be kept out of the island strata.

### Commit

```text
Harden Photon cloud layers for Aria
```

Push and **STOP**.

---

# P9 — Aria atmosphere and fog audit

Only now inspect the rest of the Overworld inheritance.

Since Aria wrappers retain:

```glsl
WORLD_OVERWORLD
```

Photon will continue using:

```text
Overworld atmosphere
sky scattering
sun/moon
stars
weather
ambient lighting
```

This is desirable.

### Test matrix

Inspect:

```text
Y -40   arrival corridor
Y 0     lower atmosphere
Y 64    cloud deck
Y 100   clear sky
Y 200   main islands
Y 330   high islands
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

Look for:

- black void below the islands;
- horizon darkening;
- excessive atmosphere near Y=-64;
- strange exposure below cloud level;
- wrong celestial rendering;
- fog discontinuities.

### Rule

Only introduce `WORLD_ARIA` atmospheric overrides for **observed defects**.

Do not turn this phase into an artistic rewrite of Photon.

### Commit

If fixes are needed:

```text
Tune Photon atmosphere for Lampas Aria
```

Push and **STOP**.

---

# P10 — Dimension transition hardening

This matters a lot for Lampas because Aria is not entered through a conventional portal.

Run actual:

```text
Overworld -> Aria
Aria -> Overworld
```

sky-seam transitions.

Repeat at least 10 cycles.

### Verify

```text
world0 -> aria shader switch
aria -> world0 shader switch

no stale temporal cloud history
no stale shadow data
no flashing old cloud altitude
no black frame
no frozen exposure
no program compilation error
no shader state leakage
```

Also test:

```text
/teleport or /lampas goto
actual ascent seam
actual descent seam
Elytra momentum transition
```

Photon must remain visually stable even during fast camera motion immediately after the dimension switch.

### Commit

Any required fixes:

```text
Harden Photon state across Aria transitions
```

Push and **STOP**.

---

# P11 — Automated structural regression suite

Now add repository-native validation.

A simple Python or shell validation tool is enough; this does not require a heavyweight build system.

Suggested:

```text
tools/validate.py
```

### Tests

Validate:

```text
dimension.properties maps lampas:aria

aria wrapper inventory == world0 wrapper inventory

every Aria Overworld wrapper contains:
    WORLD_OVERWORLD
    WORLD_ARIA

Aria wrappers retain identical /program/... include targets

world0 contains no WORLD_ARIA

world-1 contains no WORLD_ARIA

world1 contains no WORLD_ARIA
```

Add cloud math regression:

```text
base:
63 + 10 / 10 = 64

top:
63 + (10 + 40) / 10 = 68
```

And preserve the bug calculation as documentation/test:

```text
old:
63 + 1200 / 10 = 183
63 + 2400 / 10 = 303
```

That makes it obvious why someone must not casually replace the Aria constants with upstream defaults later.

### Optional CI

Add GitHub Actions to run this validator on push/PR.

It should be fast and dependency-light.

### Commit

```text
Add Aria shader compatibility regression checks
```

Push and **STOP**.

---

# P12 — Cross-dimension visual regression

Before release, verify the derivative hasn't broken Photon elsewhere.

Compare stock imported Photon v1.3b against current derivative in:

```text
Overworld
Nether
End
Aria
```

### Hard requirement

For:

```text
Overworld
Nether
End
```

the shader behavior should be unchanged.

Ideally the only functional additions are reachable through:

```glsl
#ifdef WORLD_ARIA
```

or the new Aria wrapper directory.

### Performance

Compare Aria before/after:

```text
FPS
GPU frame time
cloud rendering
cloud shadow pass
VRAM
```

The relocation itself should have essentially zero meaningful runtime cost.

### Commit

Only if test-driven fixes are required.

Then push and **STOP**.

---

# P13 — Packaging and release

Because this repo contains the complete shader source, **drop the old plan's patch-installer/version-fingerprint system**.

The repository itself pins the upstream baseline. That is much cleaner.

Build:

```text
Photon-v1.3b-Lampas-Aria.zip
```

with:

```text
ZIP ROOT
├── LICENSE
└── shaders/
    ├── dimension.properties
    ├── shaders.properties
    ├── aria/
    ├── world0/
    ├── world-1/
    ├── world1/
    ├── include/
    └── program/
```

Do not generate:

```text
Photon-v1.3b-Lampas-Aria.zip/
    lampas-photon-aria-shader/
        shaders/
```

unless Iris explicitly supports that nesting.

### Provenance

Record:

```text
Based on Photon v1.3b
Upstream baseline commit/hash
Tested Minecraft: 26.2
Tested Iris: 1.11.2+mc26.2
Target dimension: lampas:aria
```

The repo already records that it is a v1.3b derivative and that its imported source matches the original artifact. 

### Suggested tag

```text
v1.3b-lampas-aria.1
```

### Commit

```text
Prepare Photon v1.3b Lampas Aria release
```

Push and **STOP before tagging/releasing** unless the user explicitly authorized release publication.

---

# P14 — Documentation and maintenance contract

Update README with:

```text
Installation
Supported Iris version
Supported Minecraft version
Required Lampas Aria version/contract
Why upstream Photon fails
Aria cloud geometry
Known limitations
Upstream Photon attribution
```

Document explicitly:

```text
Lampas Aria dimension contract

id:           lampas:aria
cloud base:   Y64
cloud top:    Y68 in this Photon derivative
terrain:      primarily Y150–375
```

And explain that future upstream Photon updates are **manual rebases**, not blind upgrades.

For Photon v1.3c or v1.4:

```text
1. Import/compare new upstream
2. Re-run cloud consumer audit
3. Port WORLD_ARIA specialization
4. Run validator
5. Run visual matrix
6. Run transition tests
7. Release new derivative version
```

Do not assume the P4 constants or P6 reprojection layout remain unchanged upstream.

---

## One optional preliminary cleanup

Your current `PROGRESS.md` appears to contain some malformed escaping/control-character-looking text in GitHub's returned content. The important data is there, but some values render oddly. 

Before P2, the agent should first inspect the raw local file. **If the corruption actually exists on disk**, do a tiny docs-only phase:

```text
P1.1 — Normalize PROGRESS.md formatting
```

with no shader changes, then commit/push/STOP.

If the raw file is fine and this is only connector rendering, skip it.

---

# Revised responsibility split

This is the big architectural simplification:

```text
lampas-aria
│
├── owns the dimension
├── owns Y ranges/worldgen
├── owns vanilla no-shader rendering fixes
└── does NOT know Photon exists

lampas-photon-aria-shader
│
├── owns Iris dimension.properties
├── owns shaders/aria/
├── owns WORLD_ARIA
├── owns Photon cloud relocation
├── owns Photon-specific atmosphere fixes
└── ships as the Lampas-compatible Photon derivative
```

I would **not modify `lampas-aria` at all for the initial Photon work**. Its existing Y64 cloud contract is already correct. The shader derivative should adapt to the dimension, not the other way around.

And with the source now available, the most important implementation rule for the agent is:

> **Keep Photon's coordinate system and `SEA_LEVEL=63` intact. Move only the Aria cumulus shell to `planet_radius + 10` with thickness `40`, selected at compile time by `WORLD_ARIA`. Then make every dependent Photon subsystem consume that same geometry.**

That is much smaller and safer than the earlier uniform/sea-level approaches.

# Refs:
- C:\Users\markj\source\repos\lampas-aria