# Warpkeep Hegemony Unit Corps

- **Release tag:** `hegemony-unit-corps-2026-08-03`
- **Snapshot date:** 2026-08-03
- **Supplied by:** Ael
- **Deposit authority:** Ael explicitly authorized publishing all current Hegemony infantry, ranged, and cavalry packages in `ael-dev3/Warpkeep-Assets`.
- **Designation:** game-ready production asset archive and runtime handoff; this deposit does not by itself assert current live-game integration.

## Scope

The release contains three separately downloadable packages with twelve units:

- **Shieldwall infantry:** Bulwark, Legionary, Vanguard, and Honor Guard;
- **Astral ranged:** Longbow Warden, Dusk Ranger, Astral Magister, and Rift Battlemage; and
- **Astral cavalry:** Dusk Outrider, Astral Lancer, Horseguard, and Imperial Cataphract.

Together they provide 48 runtime GLBs, four mobile-first LODs per unit, 15
editable Blender sources, 39 PNGs, runtime manifests, individual and lineup
previews, QA reports, and checksum sidecars. LOD0 and LOD1 are rigged; LOD2
and LOD3 are static placement and map-distance variants. Infantry uses a
21-joint rig with Idle, Walk, and Attack actions. Ranged uses a 21-joint rig,
and cavalry uses a combined 49-joint horse-and-rider rig; both add a Special
action.

## Production history and references

The geometry, materials, rigs, actions, LODs, renders, and package metadata
were substantially authored, prepared, or refined with Codex under Ael's
direction and review. Supplied historical-strategy comparison sheets were
used only for broad role, equipment, and silhouette study. Those sheets are
not included in this release, and the package manifests identify the geometry
as original project-authored work.

The unit art direction uses Warpkeep's blackened-steel, deep-purple, and
antique-gold Hegemony palette. Official crest artwork is retained in each
package as the exact source texture plus a mobile runtime derivative and is
placed on restrained equipment fields according to each family manifest.

## Public-copy preparation

The 48 runtime GLBs remain byte-identical to the validated source packages.
Each of the 15 Blender sources stored an absolute local render-output path;
the public copies normalize those paths to package-relative `Previews/`
locations and neutralize serialized local-path fragments. Every public Blend
then reopened in Blender 5.2 with the same path-insensitive semantic
fingerprint as its private source.

Extended attributes were removed, files and directories were normalized to
portable modes, all 39 PNGs and 18 JSON documents parsed successfully, all 48
GLBs retained valid embedded glTF 2.0 payloads with no external URI, and all
126 package checksum entries passed after sanitization. No credential,
private path, symlink, executable, or hidden operating-system metadata remains
in the public packages. The detailed audit is recorded in
[`reports/hegemony-unit-corps-2026-08-03/public-sanitization.json`](../reports/hegemony-unit-corps-2026-08-03/public-sanitization.json).

The supplied runtime QA reports record 173 of 173 checks passed. The ranged
GLBs retain a harmless source metadata label that says “infantry runtime
asset”; the validated bytes were deliberately preserved rather than silently
rewritten. The 256px runtime crest also retains inherited 1254px XMP source
dimensions while its decoded image dimensions are correctly 256×256.

## Distribution shape

The binary hierarchy is published as three deterministic GitHub Release ZIPs,
one each for infantry, ranged, and cavalry. Lightweight optimized gallery
images, manifests, provenance, license boundaries, sanitization results, and
verification metadata are tracked directly in Git. Large Blend and GLB files
are intentionally excluded from normal Git history under this repository's
archive policy.

Each detached ZIP also carries `PACKAGE-NOTICE.md` at its package root. The
notice preserves the no-separate-open-license, trademark, and runtime-status
boundaries when an archive is downloaded without the surrounding repository.

## License boundary

Public archival and GitHub Release distribution of this named unit set were
authorized by Ael. No separate open-license grant is asserted or inferred.
Repository presence does not license third-party tools or services,
third-party reference material, Warpkeep or Hegemony trademarks and canonical
identity, or unrelated Warpkeep material.
