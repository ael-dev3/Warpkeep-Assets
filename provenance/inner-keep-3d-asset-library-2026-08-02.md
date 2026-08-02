# Warpkeep Inner-Keep 3D Asset Library

- **Release tag:** `inner-keep-3d-asset-library-2026-08-02`
- **Snapshot date:** 2026-08-02
- **Supplied by:** Ael
- **Deposit authority:** Ael explicitly authorized packaging the complete Warpkeep Desktop `3d` production folder and publishing it in `ael-dev3/Warpkeep-Assets`.
- **Designation:** production asset archive and runtime handoff snapshot; this deposit does not by itself assert that every item is integrated into the live game.

## Scope

The release preserves 152 distinct assets across 11 game-ready packages:

- city barracks, mill, goldworks, stoneworks, and lumber camp;
- Grand Covenant Cathedral;
- 22 inner-keep trees and 20 fantasy tree variants;
- 24 stone ruins and monuments;
- 28 wooden palisade modules; and
- the 52-prop town-items environment kit, including flora, fixtures, Hegemony banner stands, and hardscape.

The public archive contains 604 production GLBs, six inspection/catalogue GLBs, 73 current editable Blender files, one supplied Blender backup, 364 PNGs, runtime manifests, rebuild tools, previews, QA reports, and checksum sidecars. Combined catalogue GLBs remain inspection aids rather than routine runtime-placement assets.

## Public-copy preparation

The public distribution copy excludes three macOS `.DS_Store` files because they are filesystem metadata rather than game assets. No modeled object, runtime GLB, editable Blender source, texture, preview, manifest, or authoring tool was omitted.

Private local authoring paths were removed before publication:

- all 610 GLBs remain byte-identical to the supplied snapshot;
- decoded pixels remain identical for every PNG whose local-path metadata was stripped;
- one Blender source contained an absolute authoring path, which was neutralized without changing its scene semantics and then reopened successfully in Blender 5.2;
- package checksum sidecars were regenerated; and
- no credential, private key, temporary cache path, symlink, or control-character path was found.

The detailed audit is recorded in [`reports/inner-keep-3d-asset-library-2026-08-02/public-sanitization.json`](../reports/inner-keep-3d-asset-library-2026-08-02/public-sanitization.json).

## Distribution shape

The complete binary hierarchy is published as the checksummed GitHub Release attachment `inner-keep-3d-asset-library-2026-08-02-v1.zip`. Lightweight optimized gallery images, manifests, provenance, license boundaries, and verification metadata are tracked directly in Git. Large Blend/GLB masters are intentionally not committed to normal Git history, consistent with this repository's established archive policy.

## License boundary

Public archival and GitHub Release distribution of this named package were authorized by Ael. No separate open-license grant is asserted or inferred. Repository presence does not license third-party tools or services, Warpkeep trademarks or canonical identity, or unrelated Warpkeep material.
