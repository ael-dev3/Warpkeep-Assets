# Warpkeep Stone-Letter Title Provenance

## Coordinate

- Warpkeep source PR: `ael-dev3/Warpkeep#19`
- Exact preserved PR head: `4d16e66ca973aa82e320b9e4850c5e92ff936718`
- Archive release tag: `title-stone-letters-2026-07-12`
- Archive date: 2026-07-12

## Source and authority

Ael supplied six original glyph files and the optimized title package and explicitly authorized this named set for the Warpkeep v0.3 licensing policy. The original glyph filenames identify Meshy AI as the generation service. Private communication and attachment metadata is intentionally omitted.

The source basenames and bytes are preserved exactly. Repeated `P` and `E` characters reuse their corresponding meshes in each optimized eight-letter assembly.

## Source glyphs

| Glyph | Bytes | Triangles | POSITION vertices | SHA-256 |
| --- | ---: | ---: | ---: | --- |
| W | 52,968,424 | 636,046 | 328,333 | `61b887ddcc2e025b3d9b0b4e67fc51b30e0d6a4b11d474758c412d08b2330814` |
| A | 40,650,392 | 282,732 | 146,750 | `498031fb8b94520e6e3cf58e8451dce7791f59acd31fcd3e6eb86dbe3090eb6e` |
| R | 50,589,156 | 574,388 | 298,455 | `8bb7ad7410cec4404765723a2dafd9e617a8454e39714a2391671941c51c4556` |
| P | 38,240,900 | 221,106 | 114,342 | `0a1dae8ec89c26bfdda3fed489955bcd621206b5e3df40d03cca507b690df2fd` |
| K | 43,528,656 | 436,726 | 226,890 | `15f1471a96f7050b9cf373550abac8b5af918806da047a832927fabba7ab6ae4` |
| E | 38,881,292 | 251,822 | 131,541 | `2038848ba8f2de6c328f6e53106adf6bd172197db716c457b02489bddee2de36` |

Aggregate: 264,858,820 bytes, 2,402,820 triangles, and 1,246,311 POSITION vertices.

Each source is a self-contained glTF 2.0 GLB with one mesh/material and four embedded JPEG PBR textures. None has an external URI.

## Optimized assemblies

| Profile | Bytes | Unique / rendered triangles | POSITION vertices | Textures | SHA-256 |
| --- | ---: | ---: | ---: | --- | --- |
| High | 3,844,364 | 288,328 / 345,078 | 186,285 | 20 embedded 1024×1024 WebP | `2354a57d88be80e5568afb5754102c20c9ea0fe9a83aa5ac49c0d8dd67ae9ff5` |
| Compact | 1,714,060 | 132,136 / 158,146 | 95,073 | 20 embedded 512×512 WebP | `d29435dfa3a5fbf5103a825cc00bb3ffcef7694167a7fb7303fa89af242d7af8` |

Both contain one `WarpkeepTitleRoot`, eight named letter nodes, six reusable meshes/materials, no external URI, and normalized bounds of about 13.6554 × 1.9001 × 0.5000. They use `EXT_meshopt_compression`, `EXT_texture_webp`, and `KHR_mesh_quantization`.

Pinned `@gltf-transform/cli@4.4.1` validation reported zero errors on all eight models. The optimized models reported zero warnings; the source glyphs reported only the shared generated-tangent-space warning and default-node-matrix information notice.

## License boundary

This set is `CC-BY-4.0` only to the extent Warpkeep controls the relevant copyright and related rights. The grant is effective for Warpkeep v0.3.0 and later and does not grant trademark rights or rights in Meshy AI, other tools/services, or unrelated third-party material.
