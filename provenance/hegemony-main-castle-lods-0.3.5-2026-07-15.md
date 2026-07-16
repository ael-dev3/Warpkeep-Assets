# Hegemony Main Castle LOD provenance

- **Deposit date:** 2026-07-15
- **Repository:** `ael-dev3/Warpkeep-Assets`
- **Release:** `hegemony-main-castle-lods-0.3.5-2026-07-15`
- **Authorization:** Ael explicitly requested this deposit.
- **Public package:** [`hegemony-main-castle-lods-0.3.5-sources-v1.zip`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-main-castle-lods-0.3.5-2026-07-15)

## Supply and intent

The supplied set contains `hegemony-main-castle-high.glb`, `hegemony-main-castle-balanced.glb`, and `hegemony-main-castle-compact.glb`. These are the freshest modeled Hegemony Main Castle variants supplied for the project and are explicitly documented as aimed at the Warpkeep Alpha 0.3.5 patch. This is a source/reference deposit; no runtime integration is asserted by the archive itself.

## Validation

Each file is a self-contained GLB v2 with a valid declared length, no external URI, one scene, one node, one mesh, one material, two embedded images, no animations, and the required `EXT_meshopt_compression`, `EXT_texture_webp`, and `KHR_mesh_quantization` extensions. Pinned Khronos validation returned zero errors and zero warnings for all three variants.

Measured geometry decreases across the LOD family:

- High / LOD0: 171,554 vertices and 72,850 triangles.
- Balanced / LOD1: 67,687 vertices and 32,550 triangles.
- Compact / LOD2: 34,800 vertices and 17,232 triangles.

Bright Blender QA renders showed the same castle identity across all three variants, including the central keep, Hegemony banner, gate, towers, roofs, and embedded materials. No gross clipping, missing core geometry, corruption, or obvious LOD artifact was observed.

## Distribution boundary

Ael authorized public archival and release distribution of this named package. No separate open-license grant is asserted. The archive does not grant third-party tool/service rights, trademarks, canonical-identity rights, or unrelated Warpkeep material.
