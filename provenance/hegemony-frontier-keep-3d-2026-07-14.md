# Hegemony Frontier Keep and Main Castle 3D provenance

- **Deposit date:** 2026-07-14
- **Repository:** `ael-dev3/Warpkeep-Assets`
- **Release:** `hegemony-frontier-keep-3d-2026-07-14`
- **Authorization:** Ael explicitly requested this deposit.
- **Public package:** [`hegemony-frontier-keep-3d-sources-v1.zip`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-frontier-keep-3d-2026-07-14)

## Supplied material

The supplied set contained `Warpkeep_Hegemony_Frontier_Keep_High.blend`, `Warpkeep_Hegemony_Frontier_Keep_High.blend1`, `Warpkeep_Hegemony_Frontier_Keep_High.glb`, and `HegemonyMainCastle.glb`. The two GLBs were preserved byte-for-byte. The two Blender containers were retained privately in their supplied form and published as sanitized derivatives.

## Inspection

Both Blender containers were opened with official Blender 5.2.0 LTS using `--background --factory-startup --disable-autoexec`. Each contained one scene, one mesh object, one mesh, 55,704 vertices, 56,466 triangles, one material, four packed 2048x2048 images, no armatures, actions, drivers, linked libraries, executable text blocks, or missing unpacked dependencies. The `.blend1` backup matched the main Blend on scene, object, mesh, material, packed-image, bounds, and topology records.

The Frontier Keep GLB has one mesh, 55,704 vertices, 56,466 triangles, four embedded WebP images, and no animations. Its scene bounds matched the Blend. `HegemonyMainCastle.glb` is a separate larger one-mesh asset with 173,299 vertices, 73,070 triangles, and two embedded WebP atlases; its node metadata identifies a Hegemony hero-castle asset.

Both GLBs passed pinned `@gltf-transform/cli@4.4.1` inspection and the pinned Khronos validator with zero errors and zero warnings. The only informational validator notice was unsupported `EXT_meshopt_compression`.

## Visual QA

Local-only Blender renders showed the Frontier Keep GLB and Blend as the same coherent textured castle/keep with intact walls, towers, roofs, banners, and gate. The Main Castle rendered as a distinct larger coherent textured castle with intact towers, roofs, gate, walls, and heraldic banners. One initial generic-rig Main Castle render was underlit because of the asset scale; a scale-adjusted bright rig confirmed the visible materials and geometry. No gross clipping, missing core geometry, or corruption was observed. Temporary QA renders are not part of the release.

## Sanitization

The serialized Blender Shading screen contained an absolute local file-browser directory; its value is intentionally omitted from public metadata. The sanitizer rewrote only that UI directory to `//source-history/`. All four packed image resources remained packed. Reopened public derivatives matched their originals on counts, bounds, objects, meshes, materials, images, armatures, actions, modifiers, text blocks, drivers, and missing-dependency records. Decompressed public-byte scans found zero user-home paths, Hermes cache markers, Discord, Telegram, or CDN markers.

## Distribution boundary

Ael authorized public archival and release distribution of this named package. No separate open-license grant is asserted. This archive does not grant rights in third-party tools or services, trademarks, third-party content, Warpkeep trademarks or canonical identity, or unrelated Warpkeep material.
