# Photon Shader for Lampas Aria

Dedicated Photon v1.3b shaderpack compatibility derivative for **Lampas Aria** (\lampas:aria\).

## Purpose

Unpatched Photon v1.3b under Iris treats \lampas:aria\ as generic \world0\ (Overworld), placing its primary volumetric cumulus cloud deck at =183\text{--}303$, which directly submerges Aria's floating islands (=150\text{--}375$).

This repository houses the dedicated Iris dimension specialization:
- Maps \lampas:aria\ to its own Iris shader dimension (\shaders/dimension.properties\).
- Provides clean program wrappers under \shaders/aria/\ defining \WORLD_ARIA\ while retaining \WORLD_OVERWORLD\.
- Anchors the volumetric cumulus cloud deck to Aria's configured \cloud_height = 64.0\ (=64\text{--}68$), leaving open, clear atmosphere beneath the island archipelagos.
- Preserves 100% of Overworld, Nether, and End rendering pipelines untouched.
