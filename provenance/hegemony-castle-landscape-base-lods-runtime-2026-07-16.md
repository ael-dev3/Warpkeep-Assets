# Warpkeep Castle LandscapeBase runtime LOD provenance

- **Deposit date:** 2026-07-16
- **Repository:** `ael-dev3/Warpkeep-Assets`
- **Release:** `hegemony-castle-landscape-base-lods-runtime-2026-07-16`
- **Authorization:** Ael explicitly requested this deposit.
- **Public package:** [`hegemony-castle-landscape-base-lods-runtime-2026-07-16-v1.zip`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-castle-landscape-base-lods-runtime-2026-07-16)

## Intended shared-base use

The supplied files are runtime-designated Castle LandscapeBase LOD variants. This set is intended to be used as the shared landscape/base layer under each castle. That is the intended-use note for this deposit; it does not by itself prove current runtime integration or a shipped patch.

## Supplied family

- `Warpkeep_Castle_LandscapeBase_LOD0_High_Runtime.glb`: 214,372 bytes, 10,681 vertices, 3,954 triangles.
- `Warpkeep_Castle_LandscapeBase_LOD1_Balanced_Runtime.glb`: 92,792 bytes, 5,611 vertices, 2,138 triangles.
- `Warpkeep_Castle_LandscapeBase_LOD2_Compact_Runtime.glb`: 27,336 bytes, 1,780 vertices, 714 triangles.

All three supplied basenames and GLB payloads are preserved byte-for-byte. Each is a self-contained GLB v2 with one scene, one node, one mesh, one material, two embedded images, no animations, no external URIs, and required `EXT_meshopt_compression`, `EXT_texture_webp`, and `KHR_mesh_quantization` extensions. Pinned Khronos validation returned zero errors and zero warnings for every variant. Bright Blender 5.2 QA renders showed a coherent terrain island/base with grass, trees, rocks, flowers, and a path, with expected detail reduction across the LOD family.

## Distribution boundary

Ael authorized public archival and release distribution of this named runtime-base package. No separate open-license grant is asserted. The archive does not grant third-party tool/service rights, trademarks, canonical-identity rights, or unrelated Warpkeep material.
