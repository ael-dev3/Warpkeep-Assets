# Warpkeep Core Watcher — Level 1 release candidate

- **Candidate tag:** `core-watcher-level1-2026-08-03`
- **Snapshot date:** 2026-08-03
- **Supplied by:** Ael-directed original Warpkeep production
- **Review authority:** Ael explicitly authorized preparing a new, isolated draft PR in `ael-dev3/Warpkeep-Assets`.
- **Designation:** game-ready asset release candidate; not published, integrated, deployed, activated, or merged

## Scope

The prepared archive contains one original Level 1 Core Watcher with:

- one editable Blender 5.2 source;
- four static runtime GLBs: High, Balanced, Compact, and Map;
- three texture-free materials: obsidian, blackened metal, and restrained cold ultraviolet;
- presentation, transparent, four-LOD, and mobile map renders;
- authoring and runtime manifests, 58-check QA evidence, and nested checksums; and
- an archive-only package notice that preserves the no-separate-open-license boundary.

The Watcher is a narrow bifurcated monolith with a suspended core and
asymmetric floating shards. It has no human face, legs, weapon, gun, wings,
banner, heraldry, walk cycle, attack clip, or death clip. Render geometry is
visual only and does not define placement, picking, collision, combat, health,
damage, rewards, respawn, AI, ownership, routing, or SpacetimeDB authority.

## Production history and originality

The geometry, materials, LODs, renders, manifests, and package tooling were
substantially authored and prepared with Codex under Ael's direction and
review using Blender 5.2. No model, texture, crest, or geometry was imported
from another Warpkeep release or from a third-party reference.

Broad world-map research informed only general presentation goals: low-level
neutral encounters should remain recognizable at map scale, searchable by
level or type, and visually distinct from owned structures. The review set
included [Rise of Kingdoms neutral-unit guidance](https://riseofkingdomsguides.com/rise-of-kingdoms-barbarians-and-barbarian-forts/),
[Call of Dragons neutral-unit guidance](https://cod.guide/darkling-units/), and
the [Game of Thrones: Conquest Map Finder description](https://hbogamessupport.wbgames.com/hc/en-us/articles/360001992207-The-Map-Finder).
Those sources supplied no copied art, names, layout, code, textures, or model
data and are not included in the candidate archive.

The separate Core faction crest release and its earlier branch or PR were
explicitly kept outside this package. No Core crest, Hegemony crest, palette
swap, or Hegemony asset was used. The resulting Watcher geometry and
three-material treatment are original to this candidate.

## Public-copy preparation

The four runtime GLBs are self-contained glTF 2.0 files with embedded buffers,
no external URI, no image or texture, one scene, three named materials, and no
camera, light, skin, animation, or executable content. Export-time UV data was
omitted because the model is texture-free.

All four Blender-rendered preview frames were decoded and re-encoded with
Pillow 11.3.0 without comments, EXIF/XMP, PNG text/time chunks, or other source
metadata. The exact public copies contain no workstation or temporary build
path. No generative alteration was applied during this metadata-only step.

Blender's headless Save As operation serialized one workstation home-directory
string in transient file-browser UI state. The public candidate neutralized
that fixed-size UI string in place, then reopened the source in Blender 5.2 and
confirmed the same topology, transforms, material values, authority metadata,
and semantic fingerprint. No model data was changed by sanitization.

Every nested checksum passed. The generic release verifier accepted the exact
1,405,757-byte candidate ZIP and its 15-entry manifest. The official Khronos
glTF validator reported zero issues for all four GLBs, and each file imported
cleanly into a separate factory Blender session. A second full build produced
byte-identical GLBs and metadata-free previews plus the same editable-source
semantic fingerprint. Exact results are recorded in the [external validation
report](../reports/core-watcher-level1-2026-08-03/external-validation.json).

## Distribution shape and gate

The large `.blend`, `.glb`, transparent master, and ZIP remain outside normal
Git history. This draft PR tracks only the candidate manifest and checksum,
source inventory, provenance, package notice, sanitization/validation evidence,
three exact rendered previews, and focused verification software.

The manifest records the intended immutable release coordinates so reviewers
can audit the complete shape. The ZIP has **not** been uploaded, the intended
tag has **not** been created, and no GitHub Release exists for this candidate.
Publication, integration into the main Warpkeep repository, world placement,
combat behavior, deployment, activation, merging, and all later PR slices
remain separate owner-gated decisions.

## License boundary

Public draft-PR review of this named candidate's lightweight metadata and
previews was authorized by Ael. No separate open-license grant is asserted or
inferred. This review authorization does not license third-party tools or
services, third-party reference material, Warpkeep trademarks or canonical
identity, the separate Core faction crest release, or unrelated Warpkeep
material.
