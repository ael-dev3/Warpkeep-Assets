# Warpkeep Hegemony Citizens — Keep Services & Orders

- **Release tag:** `hegemony-citizens-keep-services-2026-08-03`
- **Snapshot date:** 2026-08-03
- **Supplied by:** Ael
- **Deposit authority:** Ael explicitly authorized publishing the complete Hegemony keep-citizens package in `ael-dev3/Warpkeep-Assets`.
- **Designation:** game-ready production asset archive and runtime handoff; this deposit does not by itself assert current live-game integration.

## Scope

The release contains eight distinct non-military and civic-order characters:

- Ember Lamplighter;
- Cistern Warden;
- Chirurgeon-Apothecary;
- Bell Herald;
- Ward Peacekeeper;
- Basilica Warden;
- Emberfoot Courier on a giant jackrabbit; and
- Shellback Shrine Tender on a giant tortoise.

Together they provide 32 runtime GLBs, four mobile-first LODs per citizen,
nine editable Blender sources, 21 PNGs, eight runtime manifests, an authoring
manifest, a QA report, exact and runtime Hegemony crest textures, individual
portraits, map-scale previews, transparent and presentation lineups, and a
nested checksum sidecar. LOD0 and LOD1 are rigged; LOD2 and LOD3 are static
crowd and map-distance variants. Walking citizens use a 21-joint rig and the
two exotic mounts use a combined 29-joint rider-and-mount rig. Both contracts
provide Idle, Walk, Work, and Greet actions.

## Production history and references

The geometry, materials, rigs, actions, LODs, renders, and package metadata
were substantially authored, prepared, or refined with Codex under Ael's
direction and review. Supplied historical-strategy character sheets informed
broad role, profession, clothing, and silhouette study only. Those reference
sheets are not included in this release, and the package geometry is original
project-authored work.

The art direction uses a restrained Hegemony palette across practical keep
workers, a ward peacekeeper, a basilica order, and two readable exotic mounts.
The exact official crest is limited to the Ward Peacekeeper's shield at close
LODs; other characters rely on palette and silhouette rather than repeated
heraldry.

## Public-copy preparation

The 32 runtime GLBs remain byte-identical to the validated source package.
The nine Blender sources were audited for external and serialized local paths,
had 18 private render-path fragments neutralized in their public copies, and
then reopened in Blender 5.2 with matching path-insensitive semantic
fingerprints.

Extended attributes were removed, files and directories were normalized to
portable modes, all 21 PNGs decoded, all 10 JSON documents parsed, all 32 GLBs
retained valid embedded glTF 2.0 payloads with no external URI, and all 74
nested package checksums passed after sanitization. No credential, private
path, symlink, executable, unsafe archive path, or hidden operating-system
metadata remains in the public package. The detailed audit is recorded in
[`reports/hegemony-citizens-keep-services-2026-08-03/public-sanitization.json`](../reports/hegemony-citizens-keep-services-2026-08-03/public-sanitization.json).

The supplied runtime QA report records 73 of 73 checks passed. A second full
archive build produced the same SHA-256, confirming deterministic packaging.

## Distribution shape

The binary hierarchy is published as one deterministic GitHub Release ZIP.
The package preserves editable sources, runtime LODs, textures, manifests,
previews, QA, the nested checksum sidecar, and an archive-only package notice.
The 2400×960 category overview and 2600×1700 all-citizen lineup, release
manifest, provenance, license boundary, and sanitization result are tracked
directly in Git. Both review images composite the exact supplied citizen
renders without generative alteration. Large Blend, GLB, and source PNG files
are intentionally excluded from normal Git history under this repository's
archive policy.

## License boundary

Public archival and GitHub Release distribution of this named citizen set were
authorized by Ael. No separate open-license grant is asserted or inferred.
Repository presence does not license third-party tools or services, supplied
reference material, Warpkeep or Hegemony trademarks and canonical identity,
or unrelated Warpkeep material.
