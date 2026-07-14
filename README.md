# Warpkeep Assets

Public, checksum-addressed source and archive material for [Warpkeep](https://warpkeep.com/).

Large masters do not live in normal Git history. They are published as immutable, tag-specific GitHub Release attachments with exact byte counts, SHA-256 checksums, safe-path manifests, provenance, and license boundaries. Warpkeep commits the optimized files required at runtime; players never depend on GitHub Release downloads while using the game.

## Asset releases

- [`title-stone-letters-2026-07-12`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/title-stone-letters-2026-07-12) — six source stone-letter GLBs and the optimized high/compact WARPKEEP title assemblies
- [`hegemony-mark-2026-07-13`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-mark-2026-07-13) — **A Mark — the Hegemony’s main in-game currency.** Includes presentation and transparent source PNGs, Git-tracked previews, checksums, [public provenance](provenance/hegemony-mark-2026-07-13.md), and CC BY 4.0 licensing effective from Warpkeep v0.3.0.

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

The verifier rejects unsupported attachment media types, wrong bytes, malformed PNG signatures or IHDR metadata, unexpected or missing ZIP entries, absolute/traversal paths, symlinks, duplicate paths, and malformed GLB headers. Full glTF semantic validation is recorded in the manifest and should be rerun with pinned `@gltf-transform/cli@4.4.1` before deriving new runtime assets.

## Boundaries

- Never add large source/master binaries to this repository's Git history.
- Never use release attachments as a runtime CDN.
- Do not infer ownership from repository presence, filenames, generation tools, or supplied attachments.
- Keep unresolved and externally governed material under its existing terms; do not sweep it into the title set's license.
- Preserve exact tag, attachment name, byte count, and SHA-256 in every downstream preparation script.

See [`ASSET-LICENSES.md`](ASSET-LICENSES.md) for the per-set license scope.
