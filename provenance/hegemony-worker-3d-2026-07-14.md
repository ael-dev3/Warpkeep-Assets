# Hegemony Worker 3D Source Set

## Coordinate

- Archive release tag: `hegemony-worker-3d-2026-07-14`
- Archive date: 2026-07-14
- Release attachment: `hegemony-worker-3d-sources-v1.zip`
- Related 3D release: [`hegemony-supply-wagon-3d-2026-07-14`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-supply-wagon-3d-2026-07-14)
- Label status: retains the supplied game-unit filename `WorkerHegemony.glb`; internal scene `WK_Hegemony_Draft_Wagon` identifies a horse-drawn wagon-family unit, not a humanoid worker
- Runtime integration: none asserted by this archive deposit

## Source and authority

Ael supplied `WorkerHegemony.glb` and `Hegemony_Worker_1.blend`, explicitly requested that the GLB basename be retained, and authorized this public deposit in Warpkeep-Assets. Private communication-platform coordinates, attachment identifiers, source-machine account names, and absolute production paths are intentionally omitted.

`WorkerHegemony.glb` is archived byte-for-byte. The supplied Blend is retained privately but is not uploaded byte-for-byte because its compressed container embedded absolute local production paths. Its original byte count and SHA-256 remain recorded. The published Blend retains the supplied basename and is a Blender 5.2.0 LTS copy with path metadata only normalized.

No separate open-license grant is asserted. This deposit grants no rights in third-party tools or services, Warpkeep trademarks or canonical identity, or unrelated Warpkeep material.

## Package inventory

- Attachment bytes: 3,382,725
- Attachment SHA-256: `c11909b92934868bf18a70462dfa76fae2f33010a5bfe91d4ca3ed47c1d53c91`
- Package root: `hegemony-worker-3d-sources-v1/`
- Entries: exact `WorkerHegemony.glb`, sanitized `Hegemony_Worker_1.blend`, README, internal manifest, and SHA-256 list

### Exact runtime GLB

- Filename: `WorkerHegemony.glb`
- Bytes: 1,637,452
- SHA-256: `4a0f762b9dadeaddd8b2d528a7e165eaa98a8dd4134eb924604922524e7bbc5d`
- 64 nodes, 17 meshes, 18 primitives, 2 materials, 3 embedded WebP textures, 1 skin
- 40,650 triangles, 51,726 upload vertices, 121,950 rendered vertices
- Six clips: `Idle`, `Start`, `Stop`, `Turn_Left`, `Turn_Right`, and `Walk`
- Required extensions: `EXT_meshopt_compression`, `EXT_texture_webp`, and `KHR_mesh_quantization`
- External URIs: none

Pinned `@gltf-transform/cli@4.4.1` reported zero errors and zero warnings. Its 19 information notices comprise one unsupported-validator notice for meshopt compression, one unused tangent, and 17 unused exported accessors.

### Public editable Blend

- Filename: `Hegemony_Worker_1.blend`
- Public bytes: 2,145,454
- Public SHA-256: `936b4a0f420d8b6af069fd9040597b8cf328893e6ff2b382ed6c31cf0c4e6482`
- Supplied original bytes: 2,145,945
- Supplied original SHA-256: `0c0249b3fdbee3435ba16b73a712c7f02e59e0046cd7f245fe050f0afd7730eb`
- Format: Blender 5.2 variable-length file format (`BLENDER17-01v0502`), Zstandard-compressed
- 1 scene, 23 collections, 14 objects, 13 meshes, 2 materials, 3 packed images, 1 armature with 47 bones
- 19,250 editable vertices and 37,412 triangles; stored actions: none
- Nine documentation text blocks; linked libraries, drivers, executable text blocks, and missing unpacked dependencies: none

Blender normalized 13 library weak-reference paths, three packed-image paths, one render path, and four path mentions across two documentation blocks. The public copy matches the original on scenes, objects, meshes, topology, materials, packed images, armature, actions, modifiers, and bounds. A full 6,201,424-byte decompressed scan found zero user paths, staging/cache markers, emails, communication-platform markers, URLs, or long identifiers.

## Model correspondence and visual QA

All 13 Blend mesh names occur in the GLB with exactly matching per-mesh triangle counts. The GLB adds banner cloth, banner pole, collar/breastplate, and saddle/blanket strap meshes. It also carries six animation clips while the editable Blend retains the matching 47-bone rig with no stored actions.

Local-only front and side renders show coherent variants of the same black draft horse and wooden supply wagon with purple cargo and a lit lantern. Both omit the telescope; the Blend's lighter tack and absent banner are intentional differences rather than broken geometry. No missing textures, clipping, corruption, or missing core geometry was observed. QA renders are not part of the public archive.

`WorkerHegemony.glb` is byte-identical to the two no-telescope GLB aliases in the related supply-wagon 3D release. The duplicate content is intentional because Ael supplied and requested retention of this distinct basename.
