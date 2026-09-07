# Working on Warpkeep Assets

Preserve useful, traceable creative work for Warpkeep. This repository owns
asset history, catalogs, release manifests and verification tools. The
[game repository](https://github.com/ael-dev3/Warpkeep) owns gameplay and runtime
integration. Current user instructions take precedence over historical plans.

## Read the material before changing it

- Read [README.md](README.md), [LICENSE](LICENSE), [ASSET-LICENSES.md](ASSET-LICENSES.md)
  and the affected set's manifest and dated provenance. Some collections permit
  public archival distribution without granting general reuse rights.
- Preserve supplier attribution, creation disclosures, licenses and history.
  A new composition, conversion or AI-assisted edit does not make its source
  newly authored or expand the permission to use it.
- Distinguish source deposits, runtime candidates, supplied QA and verified
  integration. Confirm actual game callers before describing an asset as live.
- Keep existing release URLs, attachment names and catalog anchors functional.
  Do not silently rewrite a published manifest to describe different bytes.

## Keep the archive reviewable

Keep lightweight previews, provenance, manifests and reports in Git. Large
source packages belong in the established release-attachment workflow. Read the
affected release's boundary before preparing new material; never publish private
source paths, credentials or unrelated supplied content.

Record a release's exact tag, attachment basename, byte size and SHA-256. Obtain
manifests through a trusted repository revision or independently pinned digest.
Checksums establish byte integrity, not supplier identity, ownership or license.
Follow [the existing verification procedure](README.md#verification); do not
weaken archive bounds or disable checks to admit a failing package.

Runtime derivatives should retain their source release and transformation
history. Release attachments are downloads, not a production runtime CDN. Keep
the 0.4 Verdant Citadel direction coherent without rewriting earlier releases
as new 0.4 work or claiming unimplemented gameplay.

## Verify the affected work

For documentation, inspect links, anchors, dated claims and the scoped diff. For
verifier or manifest changes, inspect the actual schema and callers, then run
the repository's CI checks from the root with its Python version:

```sh
python -m compileall -q -f scripts tests
python -m unittest discover -s tests -v
```

The workflow pins Python 3.13. Compressed Blender verification also requires
the `zstd` CLI; document platform limits rather than claiming an unexecuted
validation. Follow [SECURITY.md](SECURITY.md) for sensitive findings.

Stage only reviewed changes. Report what changed, its provenance, what actually
ran and any remaining limitation. Source publication, attachment publication and
game integration are separate outcomes.
