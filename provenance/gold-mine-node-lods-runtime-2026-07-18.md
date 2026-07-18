# Warpkeep Gold Mine Gathering Node runtime LOD provenance

- **Deposit date:** 2026-07-18
- **Repository:** `ael-dev3/Warpkeep-Assets`
- **Release:** `gold-mine-node-lods-runtime-2026-07-18`
- **Authorization**: Ael explicitly authorized this public deposit.
- **Public package:** [`gold-mine-node-lods-runtime-2026-07-18-v1.zip`](https://github.com/ael-dev3/Warpkeep-Assets/releases/download/gold-mine-node-lods-runtime-2026-07-18/gold-mine-node-lods-runtime-2026-07-18-v1.zip)

## Designation and intended use

The supplied files are the `warpkeep.gold-mine-node` Gold Mine Gathering Node runtime LOD family for `GatheringNodes/Gold`, version 1.4.0 with the supplied revision `user-edited-2026-07-18`. The package is intended as a runtime gathering-node asset family; this deposit does not by itself prove current in-game integration.

## Supplied family

- `Warpkeep_GoldMine_LOD0_High_Runtime.glb`: 263,528 bytes, 11,097 vertices, 4,233 triangles, 1024 texture resolution.
- `Warpkeep_GoldMine_LOD1_Balanced_Runtime.glb`: 154,388 bytes, 9,297 vertices, 3,553 triangles, 512 texture resolution.
- `Warpkeep_GoldMine_LOD2_Compact_Runtime.glb`: 95,024 bytes, 7,195 vertices, 2,681 triangles, 256 texture resolution.

All three supplied basenames and GLB payloads are preserved byte-for-byte. Each is a self-contained GLB v2 with one scene, one node, one mesh, one material, three embedded textures, no animations, no external URIs, and the declared mesh/texture compression extensions. Pinned Khronos validation returned zero errors and zero warnings for every variant. Bright Blender QA renders showed a coherent mine entrance, ore vein, gold fragments, ore cart, timber supports, and base platform with expected LOD detail reduction; no visible clipping or corruption was observed.

The supplied runtime contract records `+Y` glTF up, `+Z` front-facing, a zero ground plane, and a footprint-center interaction pivot. The supplied manifest declares `Warpkeep_T1_Gold_Nodes_10000_Cell_Genesis001_Prompt.txt` under `preservedFiles`; that prompt file was not supplied in this deposit and is not included in the package.

## Distribution boundary

Ael authorized public archival and release distribution of this named runtime package. No separate open-license grant is asserted. The archive does not grant third-party tool/service rights, trademarks, canonical-identity rights, or unrelated Warpkeep material.
