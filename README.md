# Warpkeep Assets

Public, checksum-addressed source and archive material for [Warpkeep](https://warpkeep.com/).

This archive traces Genesis 001 from solitary keeps toward a lived-in
frontier: castle foundations, Hegemony Marks, caravans and supply lines, and
the forests, farms, mines, and quarries that may one day sustain the Realm. A
release here means preserved, provenance-tracked, and reviewable—not
necessarily integrated or playable in Warpkeep.

Integration notes below describe what each asset release itself authorized or
asserted when it was published. See the [Warpkeep repository](https://github.com/ael-dev3/Warpkeep)
for the current live runtime.

[![Warpkeep background-video reference pack](previews/background-video-reference-pack-2026-08-03/00-background-video-reference-overview.jpg)](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/background-video-reference-pack-2026-08-03)

## Background-video creation references

The 2026-08-03 reference release preserves **five supplied source files** for
future Warpkeep menu-background and cinematic-video work: a 10.08-second
vertical castle-and-Core concept clip, a low-poly Core spire render, two Core
crest treatments, and the current Warpkeep title-menu castle composition.
Every source is retained byte-for-byte inside one checksum-addressed ZIP; only
its archive path is made descriptive.

| Source | Technical read | Intended reference |
| --- | --- | --- |
| Animated concept | 834×1112, 60 fps H.264, stereo AAC | Castle foreground, sunset realm, distant Core animation |
| Core spire render | 1920×1080 PNG | Low-poly structure and emissive-violet language |
| Core crest treatments | 1600×1600 and 1254×1254 PNG | Dark presentation and green-screen compositing options |
| Warpkeep menu castle | 2548×1474 PNG | Current title/menu layout and atmosphere |

**[Download the background-video reference pack](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/background-video-reference-pack-2026-08-03)** · [manifest](releases/background-video-reference-pack-2026-08-03/manifest.json) · [provenance](provenance/background-video-reference-pack-2026-08-03.md) · [video contact sheet](previews/background-video-reference-pack-2026-08-03/01-source-video-contact-sheet.jpg)

This is a visual-development archive rather than a runtime bundle or final
compositing contract. Current live-game integration is not asserted.

[![Warpkeep — The Core faction crest](previews/the-core-faction-crest-2026-08-03/00-the-core-faction-crest-showcase.jpg)](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/the-core-faction-crest-2026-08-03)

## The Core faction crest

The 2026-08-03 identity release establishes the first visual mark for **The
Core**, Warpkeep's machine-intelligence faction. The supplied
1024×1024 transparent PNG is preserved byte-for-byte as the canonical master.
Safe-padded 1024, 512, and 256px runtime PNGs prevent edge clipping under UI
filtering, while the complete kit also carries 128/64px PNGs, lossless WebP
derivatives, an alpha mask, checksums, and presentation previews.

| Canonical source | Recommended runtime | Mobile variants |
| --- | --- | --- |
| Exact 1024px RGBA master | Safe-padded 512px PNG | 256, 128, and 64px PNGs |

**[Download The Core faction crest](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/the-core-faction-crest-2026-08-03)** · [manifest](releases/the-core-faction-crest-2026-08-03/manifest.json) · [provenance](provenance/the-core-faction-crest-2026-08-03.md) · [transparent preview](previews/the-core-faction-crest-2026-08-03/01-the-core-faction-crest-transparent-512.png)

This asset release records visual identity and runtime candidates; it does not
by itself assert current integration in Warpkeep.

[![Warpkeep Hegemony Citizens — Keep Services & Orders](previews/hegemony-citizens-keep-services-2026-08-03/00-citizens-overview.jpg)](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-citizens-keep-services-2026-08-03)

## Hegemony keep citizens

The 2026-08-03 citizen release adds **eight game-ready keep inhabitants** with
clear professions, civic-order roles, and two exotic mounts. Every citizen
ships with four mobile-first LODs, close-LOD rigging, editable Blender source,
runtime manifests, portraits, map previews, and package checksums. The
supplied QA report records **73/73 checks passed**.

| Keep role | Type | Distinctive read |
| --- | --- | --- |
| Ember Lamplighter | Civilian | Tall lantern pole and ember workwear |
| Cistern Warden | Civilian | Broad water carrier with bucket yoke |
| Chirurgeon-Apothecary | Civilian | Herb frame and practical apron |
| Bell Herald | Civilian | Lean town messenger with handbell |
| Ward Peacekeeper | Civic order | Baton, close-LOD crest shield, and dark armor |
| Basilica Warden | Church order | Mitre, formal robes, and crozier |
| Emberfoot Courier | Mounted civilian | Dispatch rider on a giant jackrabbit |
| Shellback Shrine Tender | Mounted civilian | Shrine keeper on a giant tortoise |

The package contains **32 runtime GLBs**, **9 editable Blender sources**, four
LODs per citizen, Idle/Walk/Work/Greet actions, and 21- or 29-joint rigs for
walking and mounted roles. The official Hegemony crest is deliberately limited
to the Ward Peacekeeper shield at close LODs for visual clarity.

**[Download the Hegemony keep citizens](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-citizens-keep-services-2026-08-03)** · [manifest](releases/hegemony-citizens-keep-services-2026-08-03/manifest.json) · [provenance](provenance/hegemony-citizens-keep-services-2026-08-03.md) · [sanitization audit](reports/hegemony-citizens-keep-services-2026-08-03/public-sanitization.json)

### Citizen gallery

| Release overview | Full high-resolution lineup |
| --- | --- |
| [![Hegemony keep citizens overview](previews/hegemony-citizens-keep-services-2026-08-03/00-citizens-overview.jpg)](previews/hegemony-citizens-keep-services-2026-08-03/00-citizens-overview.jpg) | [![All eight Hegemony keep citizens](previews/hegemony-citizens-keep-services-2026-08-03/00-citizens-set2-lineup-high-res.jpg)](previews/hegemony-citizens-keep-services-2026-08-03/00-citizens-set2-lineup-high-res.jpg) |

*Both exact-render review images are included in this patch: a 2400×960 release overview and a 2600×1700 full lineup.*

The category overview mirrors the Unit Corps presentation while preserving the current citizen renders exactly.

[![Warpkeep Hegemony Unit Corps](previews/hegemony-unit-corps-2026-08-03/00-corps-overview.jpg)](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-unit-corps-2026-08-03)

## Hegemony unit corps

The 2026-08-03 unit release adds a complete first Hegemony field force: **12
game-ready units** across infantry, ranged, and cavalry families. Every unit
ships with four mobile-first LODs, close LOD rigging, editable Blender source,
runtime manifests, previews, and package checksums. The supplied QA reports
record **173/173 checks passed**.

| Corps | Units | Production GLBs | Rig and actions |
| --- | ---: | ---: | --- |
| Infantry — Bulwark, Legionary, Vanguard, Honor Guard | 4 | 16 | 21 joints; Idle, Walk, Attack |
| Ranged — Longbow Warden, Dusk Ranger, Astral Magister, Rift Battlemage | 4 | 16 | 21 joints; Idle, Walk, Attack, Special |
| Cavalry — Dusk Outrider, Astral Lancer, Horseguard, Imperial Cataphract | 4 | 16 | 49 joints; Idle, Walk, Attack, Special |

**[Download the Hegemony unit corps](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-unit-corps-2026-08-03)** · [manifest](releases/hegemony-unit-corps-2026-08-03/manifest.json) · [provenance](provenance/hegemony-unit-corps-2026-08-03.md) · [sanitization audit](reports/hegemony-unit-corps-2026-08-03/public-sanitization.json)

### Unit gallery

| Infantry | Ranged | Cavalry |
| --- | --- | --- |
| ![Hegemony infantry lineup](previews/hegemony-unit-corps-2026-08-03/01-infantry-lineup.jpg) | ![Hegemony ranged lineup](previews/hegemony-unit-corps-2026-08-03/02-ranged-lineup.jpg) | ![Hegemony cavalry lineup](previews/hegemony-unit-corps-2026-08-03/03-cavalry-lineup.jpg) |

[![Warpkeep 3D Asset Library](previews/inner-keep-3d-library-2026-08-02/00-library-overview.jpg)](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/inner-keep-3d-asset-library-2026-08-02)

## Current 3D production library

The 2026-08-02 inner-keep library gathers the current Blender and runtime work
into one verified handoff: **152 distinct assets**, **604 production GLBs**, six
inspection catalogues, **74 Blender containers**, 364 previews, four-level LOD
families, and the exact-texture Hegemony banner collection.

| Collection | Assets | Production GLBs |
| --- | ---: | ---: |
| Town items — flora, fixtures, banners, and hardscape | 52 | 208 |
| Wooden palisade modules | 28 | 112 |
| Stone ruins and monuments | 24 | 96 |
| Inner-keep trees | 22 | 88 |
| Fantasy tree expansion | 20 | 80 |
| Buildings — cathedral, barracks, mill, goldworks, stoneworks, lumber camp | 6 | 20 |

**[Download the complete verified library](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/inner-keep-3d-asset-library-2026-08-02)** · [manifest](releases/inner-keep-3d-asset-library-2026-08-02/manifest.json) · [provenance](provenance/inner-keep-3d-asset-library-2026-08-02.md) · [sanitization audit](reports/inner-keep-3d-asset-library-2026-08-02/public-sanitization.json)

### Production gallery

| | |
| --- | --- |
| ![Town items](previews/inner-keep-3d-library-2026-08-02/01-town-items-overview.jpg) **Town items — 52 props** | ![Hegemony banner stands](previews/inner-keep-3d-library-2026-08-02/02-hegemony-banner-stands.jpg) **Exact-crest Hegemony banner stands** |
| ![Wooden palisades](previews/inner-keep-3d-library-2026-08-02/03-wooden-palisade-kit.jpg) **Wooden palisade kit — 28 modules** | ![Stone ruins and monuments](previews/inner-keep-3d-library-2026-08-02/04-stone-ruins-monuments.jpg) **Stone ruins and monuments — 24 assets** |
| ![Inner-keep trees](previews/inner-keep-3d-library-2026-08-02/05-inner-keep-trees.jpg) **Inner-keep trees — 22 variants** | ![Fantasy trees](previews/inner-keep-3d-library-2026-08-02/06-fantasy-tree-expansion.jpg) **Fantasy tree expansion — 20 variants** |
| ![Grand Covenant Cathedral](previews/inner-keep-3d-library-2026-08-02/07-grand-covenant-cathedral.jpg) **Grand Covenant Cathedral** | ![City barracks](previews/inner-keep-3d-library-2026-08-02/08-city-barracks.jpg) **City barracks** |
| ![Lumber camp](previews/inner-keep-3d-library-2026-08-02/09-lumber-camp.jpg) **Lumber camp** | ![City mill](previews/inner-keep-3d-library-2026-08-02/10-city-mill.jpg) **City mill** |
| ![City goldworks](previews/inner-keep-3d-library-2026-08-02/11-city-goldworks.jpg) **City goldworks** | ![City stoneworks](previews/inner-keep-3d-library-2026-08-02/12-city-stoneworks.jpg) **City stoneworks** |

### Repository map

- [`releases/`](releases/) — trusted attachment manifests and checksum sidecars
- [`manifests/`](manifests/) — source inventories and preparation records
- [`provenance/`](provenance/) — authorization, history, and license boundaries
- [`previews/`](previews/) — lightweight Git-tracked visual catalogues
- [`scripts/`](scripts/) and [`tests/`](tests/) — fail-closed release verification

## Creation disclosure

Most assets in this archive were substantially authored, prepared, or refined
with Codex using OpenAI's GPT-5.6 Sol model at Ultra reasoning effort, under
human direction and review. Some individual assets also use other tools or
generation services; each set's dated provenance record remains the source of
truth for its specific production history. This disclosure describes the
creation process only. It does not change any license, ownership, attribution,
or trademark boundary.

## License

Warpkeep-Assets is a mixed-license archive. The repository's project-authored
verification software uses the same [Apache-2.0 software license](LICENSES/Apache-2.0.txt)
as the main Warpkeep repository. Creative assets are not automatically covered
by Apache-2.0: the stone-letter title set and Hegemony Mark artwork are
expressly licensed under [CC BY 4.0](LICENSES/CC-BY-4.0.txt), while other
deposits keep the archive-only, original, or unresolved terms recorded for
their set.

Read the root [`LICENSE`](LICENSE) for the plain-language map and
[`ASSET-LICENSES.md`](ASSET-LICENSES.md) for exact per-release scope. The main
project's [licensing policy](https://github.com/ael-dev3/Warpkeep/blob/main/LICENSING.md)
and [runtime asset inventory](https://github.com/ael-dev3/Warpkeep/blob/main/ASSETS-LICENSE.md)
explain how these materials are treated when integrated into Warpkeep.

Large masters do not live in normal Git history. They are published as immutable, tag-specific GitHub Release attachments with exact byte counts, SHA-256 checksums, safe-path manifests, provenance, and license boundaries. Warpkeep commits the optimized files required at runtime; players never depend on GitHub Release downloads while using the game.

## Asset releases

- [`background-video-reference-pack-2026-08-03`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/background-video-reference-pack-2026-08-03) — one verified reference ZIP preserving the supplied 10.08-second castle/Core MP4 and four PNG references byte-for-byte, with internal and release-level checksums, [public provenance](provenance/background-video-reference-pack-2026-08-03.md), a visual overview, and a six-frame video contact sheet
- [`the-core-faction-crest-2026-08-03`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/the-core-faction-crest-2026-08-03) — exact supplied 1024px transparent master for The Core faction, three individually downloadable safe-padded runtime PNGs, a complete 15-file source/runtime kit, checksums, [public provenance](provenance/the-core-faction-crest-2026-08-03.md), and a two-image Git-tracked gallery
- [`hegemony-citizens-keep-services-2026-08-03`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-citizens-keep-services-2026-08-03) — eight game-ready Hegemony keep citizens, including two civic orders and two exotic mounted roles, with 32 four-LOD runtime GLBs, 9 privacy-sanitized editable Blender sources, 21 PNGs, 73/73 QA checks, package manifests, nested checksums, [public provenance](provenance/hegemony-citizens-keep-services-2026-08-03.md), and a Git-tracked two-image release gallery
- [`hegemony-unit-corps-2026-08-03`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-unit-corps-2026-08-03) — twelve game-ready Hegemony infantry, ranged, and cavalry units with 48 four-LOD runtime GLBs, 15 privacy-sanitized editable Blender sources, 39 PNGs, package manifests, nested checksums and license notices, [public provenance](provenance/hegemony-unit-corps-2026-08-03.md), and a Git-tracked four-image gallery
- [`inner-keep-3d-asset-library-2026-08-02`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/inner-keep-3d-asset-library-2026-08-02) — complete privacy-sanitized inner-keep production snapshot: 152 assets, 610 total GLBs, 74 Blender containers, 364 PNGs, checksums, [public provenance](provenance/inner-keep-3d-asset-library-2026-08-02.md), and a 12-image Git-tracked production gallery
- [`title-stone-letters-2026-07-12`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/title-stone-letters-2026-07-12) — six source stone-letter GLBs and the optimized high/compact WARPKEEP title assemblies
- [`hegemony-mark-2026-07-13`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-mark-2026-07-13) — **A Mark — the Hegemony’s main in-game currency.** Includes presentation and transparent source PNGs, Git-tracked previews, checksums, [public provenance](provenance/hegemony-mark-2026-07-13.md), and CC BY 4.0 licensing effective from Warpkeep v0.3.0.
- [`hegemony-supply-wagon-2026-07-14`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-supply-wagon-2026-07-14) — descriptively labeled Hegemony horse-drawn field supply wagon reference. Includes the source PNG, Git-tracked preview, checksums, [public provenance](provenance/hegemony-supply-wagon-2026-07-14.md), and explicit public-archive authorization without a separate open-license grant.
- [`hegemony-supply-wagon-3d-2026-07-14`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-supply-wagon-3d-2026-07-14) — expanded Hegemony supply-wagon 3D source set with a polished GLB, two exact no-telescope aliases, and a path-sanitized Blender 5.2 source, packaged with checksums, [public provenance](provenance/hegemony-supply-wagon-3d-2026-07-14.md), and the same no-separate-open-license boundary.
- [`hegemony-worker-3d-2026-07-14`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-worker-3d-2026-07-14) — supplemental Hegemony worker game-unit 3D set retaining exact `WorkerHegemony.glb` naming with a path-sanitized `Hegemony_Worker_1.blend`; internal scene metadata identifies a no-telescope horse-drawn wagon-family unit. Includes checksums, [public provenance](provenance/hegemony-worker-3d-2026-07-14.md), and no separate open-license grant.
- [`hegemony-frontier-keep-3d-2026-07-14`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-frontier-keep-3d-2026-07-14) — supplied Hegemony Frontier Keep and Main Castle 3D source set with byte-exact GLBs, path-sanitized Blender source/backup derivatives, checksums, and [public provenance](provenance/hegemony-frontier-keep-3d-2026-07-14.md); no separate open-license grant.
- [`hegemony-emblem-2026-07-14`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-emblem-2026-07-14) — supplied pixel-art Hegemony emblem PNG with checksums and [public provenance](provenance/hegemony-emblem-2026-07-14.md); no separate open-license grant.
- [`hegemony-main-castle-lods-0.3.5-2026-07-15`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-main-castle-lods-0.3.5-2026-07-15) — freshest supplied modeled Hegemony Main Castle high/balanced/compact LODs, explicitly aimed at the Warpkeep Alpha 0.3.5 patch; the asset release itself made no runtime-integration or separate-open-license claim.
- [`hegemony-main-castle-image-references-2026-07-16`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-main-castle-image-references-2026-07-16) — three supplied Hegemony Main Castle visual references (transparent render, presentation render, and castle UI reference), preserved byte-exact under descriptive names with C2PA metadata retained where supplied.
- [`hegemony-castle-landscape-base-lods-runtime-2026-07-16`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-castle-landscape-base-lods-runtime-2026-07-16) — supplied runtime-designated Castle LandscapeBase high/balanced/compact LODs intended as the shared base beneath each castle; exact basenames preserved. That asset release did not itself assert runtime integration.
- [`gold-mine-node-lods-runtime-2026-07-18`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/gold-mine-node-lods-runtime-2026-07-18) — supplied Gold Mine Gathering Node High/Balanced/Compact runtime LODs for `GatheringNodes/Gold`; exact basenames and manifest preserved. That asset release did not itself assert in-game integration.

The release catalog is in [`releases/`](releases/), detailed source metadata is in [`manifests/`](manifests/), and public provenance is in [`provenance/`](provenance/).

## Audit artifacts

- [`warpkeep-security-qol-audit-2026-07-14`](reports/warpkeep-security-qol-audit-2026-07-14/REPORT.md) — dated, read-only security and quality-of-life audit of Warpkeep's frontend, auth bridge, SpacetimeDB boundary, repositories, deployment and public assets; includes a checksum-addressed report, [manifest](reports/warpkeep-security-qol-audit-2026-07-14/manifest.json), and [sanitized provenance](provenance/warpkeep-security-qol-audit-2026-07-14.md).

Audit reports are Git-tracked technical snapshots rather than runtime assets or Release attachments. Raw private evidence, private communication-platform identifiers, and private attachment metadata are not part of the public archive; public deployment/provenance coordinates remain in the manifest for reproducibility.

## Verification

Download all attachments for a release into one directory, then run:

```sh
python3 scripts/verify_release.py \
  --manifest releases/title-stone-letters-2026-07-12/manifest.json \
  --asset-dir /path/to/downloads
```

Use a manifest from a trusted repository commit. If its SHA-256 was obtained
through a separate trusted channel, pin it with `--manifest-sha256`; checksums
prove integrity against that manifest, not the identity of whoever supplied it.

The verifier requires the release checksum sidecar and rejects unsupported
media types, wrong bytes, non-regular files, malformed PNG metadata,
unexpected ZIP entries, unsafe paths, symlinks, duplicates, control
characters, oversized or excessively compressed archives, malformed GLB
headers, and malformed Blender containers. Zstandard-compressed `.blend` and
`.blend1` verification requires the `zstd` CLI; compressed input, decompressed
output, and verifier runtime are bounded, and verification fails closed if the
tool is unavailable. Rerun the manifest's pinned glTF semantic validation
before deriving new runtime assets.

## Boundaries

- Never add large source/master binaries to this repository's Git history.
- Never use release attachments as a runtime CDN.
- Do not infer ownership from repository presence, filenames, generation tools, or supplied attachments.
- Keep unresolved and externally governed material under its existing terms; do not sweep it into the title set's license.
- Preserve exact tag, attachment name, byte count, and SHA-256 in every downstream preparation script.

See [`LICENSE`](LICENSE) for the repository-wide map and
[`ASSET-LICENSES.md`](ASSET-LICENSES.md) for the per-set license scope.

## Logging Camp Wood Gathering Node runtime LODs

- Release: `logging-camp-node-lods-runtime-2026-07-18`
- Identity: `warpkeep.logging-camp-node` (`GatheringNodes/Wood`)
- Package: three supplied High/Balanced/Compact GLBs plus the exact supplied runtime manifest.
- Status at publication: runtime-designated deposit; the asset release did not itself assert in-game integration.

## Warpkeep Trees runtime bundle

- Release: `trees-runtime-bundle-2026-07-18`
- Package: verifier-compatible outer archive preserving the exact supplied `Warpkeep_Trees_Runtime_Bundle_2026-07-18.zip` as a nested source entry.
- Contents: 22 tree assets, 66 GLBs, 22 runtime manifests, and three LODs per asset.
- Status at publication: runtime handoff deposit; the asset release did not itself assert in-game integration.

## Royal Harvest Windmill Food Gathering Node runtime LODs

- Release: `wheat-farm-node-lods-runtime-2026-07-18`
- Identity: `warpkeep.wheat-farm-node` (`GatheringNodes/Food`)
- Package: three supplied High/Balanced/Compact GLBs plus the exact supplied runtime manifest.
- Status at publication: runtime-designated deposit; intentional ground-embedded field rocks are documented by the supplied contract. The asset release did not itself assert in-game integration.

## Grand Stone Quarry Gathering Node runtime LODs

- Release: `stone-quarry-node-lods-runtime-2026-07-18`
- Identity: `warpkeep.stone-quarry-node` (`GatheringNodes/Stone`)
- Package: three supplied High/Balanced/Compact GLBs plus the exact supplied runtime manifest.
- Status at publication: runtime-designated deposit; visual-clearance contract recorded as passed. The asset release did not itself assert in-game integration.

## Lowlands Rabbit Runtime + UI Bundle

- Release: `rabbit-runtime-ui-bundle-2026-07-30`
- Identity: `warpkeep.environment.wildlife.rabbit` (`Environment/Wildlife`)
- Package: privacy-sanitized distribution copy of the supplied Rabbit runtime/UI ZIP; seven embedded PNG local-path metadata chunks removed while decoded pixels and intended runtime payload bytes were preserved.
- Status: visual-only archive; current in-game integration not asserted. High/Balanced rigged GLBs retain the documented non-root skinned-mesh validator warning.
## Hegemony Empire admission request button sound

- Release: `hegemony-empire-admission-request-button-sound-2026-07-30`
- Asset: `Hegemony_Empire_Admission_Request_Button.mp3`
- Role: sound for the button to request Hegemony Empire admission (`hegemony-empire-admission.request`)
- Format: MP3, 48 kHz stereo, 192 kbps, 2.0 seconds; current in-game integration not asserted.
- The supplied upload had an `.ogg` suffix but contained MP3 bytes; exact audio bytes are preserved under the correct public `.mp3` filename.
