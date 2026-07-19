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

Large masters do not live in normal Git history. They are published as immutable, tag-specific GitHub Release attachments with exact byte counts, SHA-256 checksums, safe-path manifests, provenance, and license boundaries. Warpkeep commits the optimized files required at runtime; players never depend on GitHub Release downloads while using the game.

## Asset releases

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

The verifier rejects unsupported attachment media types, wrong bytes, malformed PNG signatures or IHDR metadata, unexpected or missing ZIP entries, absolute/traversal paths, symlinks, duplicate paths, malformed GLB headers, and malformed Blender containers. Verification of Zstandard-compressed `.blend` and `.blend1` entries requires the `zstd` CLI; compressed input and decompressed output are exact-size bounded and the actual decompressed Blender header is checked, with verification failing closed if the tool is unavailable. Full glTF semantic validation is recorded in the manifest and should be rerun with pinned `@gltf-transform/cli@4.4.1` before deriving new runtime assets.

## Boundaries

- Never add large source/master binaries to this repository's Git history.
- Never use release attachments as a runtime CDN.
- Do not infer ownership from repository presence, filenames, generation tools, or supplied attachments.
- Keep unresolved and externally governed material under its existing terms; do not sweep it into the title set's license.
- Preserve exact tag, attachment name, byte count, and SHA-256 in every downstream preparation script.

See [`ASSET-LICENSES.md`](ASSET-LICENSES.md) for the per-set license scope.

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
