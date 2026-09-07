# Warpkeep Assets

The visual source archive for [Warpkeep](https://warpkeep.com/): buildings,
characters, landscapes, identity and sound, preserved with dated provenance,
release manifests and verification tools.

Find source material here, then follow the
[game repository](https://github.com/ael-dev3/Warpkeep) for runtime selection and
integration. A source deposit, a runtime candidate and a playable feature are
different stages of the work.

<a href="docs/archive/2026-09-08-asset-catalog.md#production-gallery"><img src="previews/inner-keep-3d-library-2026-08-02/10-city-mill.jpg" alt="City Mill source preview with teal roof, pale masonry and timber framing" width="360"></a>

City Mill source preview from the August 2026 library.
[Gallery](docs/archive/2026-09-08-asset-catalog.md#production-gallery) ·
[Provenance](provenance/inner-keep-3d-asset-library-2026-08-02.md).

## Start here

[Collections](#collections) · [Historical galleries](docs/archive/2026-09-08-asset-catalog.md) ·
[Licensing](#license) · [Verification](#verification) ·
[Contributor guide](AGENTS.md) · [Security policy](SECURITY.md)

## Supporting Warpkeep 0.4

Warpkeep 0.4 is being developed around **gather → choose → build → benefit →
return**. The Verdant Citadel direction combines pale masonry, dark timber,
teal roofs and layered natural surroundings in a readable keep diorama.
This archive supplies preserved material for that work; composition, gameplay,
mobile performance and release acceptance belong to the game.

Follow the [0.4 development source](https://github.com/ael-dev3/Warpkeep/tree/codex/prepared-keep-bindings-fix)
for current progress. An asset publication does not mean 0.4 has shipped.
Reused material keeps its original authorship, provenance and terms.

<a name="asset-releases"></a>

## Collections

Choose by purpose. The linked catalog keeps the dated galleries, exact downloads,
package quantities, manifests and provenance together.

| Collection | What to find | Catalog and source records |
| --- | --- | --- |
| <a name="current-3d-production-library"></a><a name="production-gallery"></a>Keep and settlement | Buildings, town props, palisades, ruins, banners and castle foundations. | [Library and gallery](docs/archive/2026-09-08-asset-catalog.md#current-3d-production-library) · [Earlier castle deposits](docs/archive/2026-09-08-asset-catalog.md#asset-releases) |
| <a name="hegemony-keep-citizens"></a><a name="citizen-gallery"></a>Citizens | Keep services, civic orders and mounted inhabitants. | [Citizen collection](docs/archive/2026-09-08-asset-catalog.md#hegemony-keep-citizens) |
| <a name="hegemony-unit-corps"></a><a name="unit-gallery"></a>Unit corps | Infantry, ranged and cavalry models with their recorded rigs and actions. | [Unit collection](docs/archive/2026-09-08-asset-catalog.md#hegemony-unit-corps) |
| <a name="warpkeep-trees-runtime-bundle"></a>Forests | Tree sources and runtime bundles for natural framing. | [Tree bundle](docs/archive/2026-09-08-asset-catalog.md#warpkeep-trees-runtime-bundle) · [Library trees](docs/archive/2026-09-08-asset-catalog.md#production-gallery) |
| <a name="logging-camp-wood-gathering-node-runtime-lods"></a><a name="royal-harvest-windmill-food-gathering-node-runtime-lods"></a><a name="grand-stone-quarry-gathering-node-runtime-lods"></a>Gathering destinations | Windmill, logging camp, quarry and gold-mine deposits. | [Food](docs/archive/2026-09-08-asset-catalog.md#royal-harvest-windmill-food-gathering-node-runtime-lods) · [Wood](docs/archive/2026-09-08-asset-catalog.md#logging-camp-wood-gathering-node-runtime-lods) · [Stone](docs/archive/2026-09-08-asset-catalog.md#grand-stone-quarry-gathering-node-runtime-lods) · [Gold](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/gold-mine-node-lods-runtime-2026-07-18) |
| <a name="lowlands-rabbit-runtime--ui-bundle"></a>Wildlife | Rabbit models, animation and UI material with the recorded validation limits. | [Rabbit bundle](docs/archive/2026-09-08-asset-catalog.md#lowlands-rabbit-runtime--ui-bundle) |
| <a name="the-core-faction-crest"></a>Identity and titles | The Core crest, Hegemony emblem, stone-letter title and historical Mark artwork. | [The Core](docs/archive/2026-09-08-asset-catalog.md#the-core-faction-crest) · [Identity releases](docs/archive/2026-09-08-asset-catalog.md#asset-releases) |
| Workers and supply | Wagon references, modeled supply wagons and the supplied worker source set. | [Source releases](docs/archive/2026-09-08-asset-catalog.md#asset-releases) |
| <a name="hegemony-empire-admission-request-button-sound"></a>Sound | The supplied Hegemony admission-request button sound. | [Audio record](docs/archive/2026-09-08-asset-catalog.md#hegemony-empire-admission-request-button-sound) |

The [historical catalog](docs/archive/2026-09-08-asset-catalog.md) preserves the
publication record, including supplied QA statements and integration limits.
All release manifests remain in [`releases/`](releases/); the
[asset ledger](ASSET-LICENSES.md) links each set to its terms.

## License

This is a **mixed-license archive**. Public download does not itself grant
adaptation or redistribution rights. Read the root [licensing map](LICENSE),
the [per-set ledger](ASSET-LICENSES.md) and the affected provenance record.

Project-authored verification software uses
[Apache 2.0](LICENSES/Apache-2.0.txt). The stone-letter title set and Hegemony Mark
artwork are expressly covered by [CC BY 4.0](LICENSES/CC-BY-4.0.txt). Other deposits
retain their archive-only, original or unresolved terms; these grants do not
extend across the collection. Repository prose follows the scope in the licensing map.

The game's [licensing policy](https://github.com/ael-dev3/Warpkeep/blob/main/LICENSING.md)
and [runtime asset inventory](https://github.com/ael-dev3/Warpkeep/blob/main/ASSETS-LICENSE.md)
record how integrated material is treated.

## Creation disclosure

Most assets in this archive were substantially authored, prepared, or refined
with Codex using OpenAI's GPT-5.6 Sol model at Ultra reasoning effort, under
human direction and review. Some individual assets also use other tools or
generation services; each set's dated provenance record remains the source of
truth for its specific production history. This disclosure describes the
creation process only. It does not change any license, ownership, attribution,
or trademark boundary.

## Verification

From the repository root, download all attachments for the chosen release into
one directory, then verify them against its manifest:

```sh
python3 scripts/verify_release.py \
  --manifest releases/title-stone-letters-2026-07-12/manifest.json \
  --asset-dir /path/to/downloads
```

Use a manifest from a trusted repository commit. If its SHA-256 came through a
separate trusted channel, pin it with `--manifest-sha256`. Checksums establish
byte integrity against that manifest, not supplier identity or permission to reuse.

The verifier requires the release checksum sidecar. It rejects wrong bytes,
unsupported media, non-regular files, malformed PNG/GLB/Blender containers,
unsafe or unexpected archive paths, duplicates and excessive decompression.
Zstandard-compressed `.blend` and `.blend1` verification requires the `zstd` CLI;
input, output and runtime are bounded, and a missing tool fails closed.
Rerun the manifest's pinned glTF semantic validation before deriving new runtime assets.

## Repository map

| Location | Responsibility |
| --- | --- |
| [`releases/`](releases/) | Attachment manifests and checksum sidecars |
| [`manifests/`](manifests/) | Source inventories and preparation records |
| [`provenance/`](provenance/) | Authorization, production history and license boundaries |
| [`previews/`](previews/) | Lightweight visual catalogs |
| [`scripts/`](scripts/) and [`tests/`](tests/) | Release verification and regression checks |
| [Historical catalog](docs/archive/2026-09-08-asset-catalog.md) | Dated showcases, package details and original release links |

## Audit artifacts

The [July 2026 security and quality review](reports/warpkeep-security-qol-audit-2026-07-14/REPORT.md)
has its own [manifest](reports/warpkeep-security-qol-audit-2026-07-14/manifest.json)
and [sanitized provenance](provenance/warpkeep-security-qol-audit-2026-07-14.md).
It is a dated technical snapshot; raw private evidence is excluded.

## Boundaries

- Preserve exact release tags, attachment names, byte counts and SHA-256 values
  in downstream preparation records.
- Keep large masters in the established release-attachment archive and
  lightweight documentation and previews in Git.
- Deliver optimized runtime files through the game; release downloads are not a runtime CDN.
- Preserve source attribution and exact permissions through every derivative.
  Filenames, generation tools and repository presence do not establish ownership.
