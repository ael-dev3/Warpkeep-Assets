# Hegemony Main Castle image-reference provenance

- **Deposit date:** 2026-07-16
- **Repository:** `ael-dev3/Warpkeep-Assets`
- **Release:** `hegemony-main-castle-image-references-2026-07-16`
- **Authorization:** Ael explicitly requested this deposit.
- **Public package:** [`hegemony-main-castle-image-references-2026-07-16-v1.zip`](https://github.com/ael-dev3/Warpkeep-Assets/releases/tag/hegemony-main-castle-image-references-2026-07-16)

## Naming and source boundary

The incoming image attachments had internal cache filenames rather than meaningful public basenames. The archive uses descriptive names and preserves each supplied PNG byte-for-byte. This is a visual/reference deposit, not a runtime source or canonical UI contract.

## References

- `hegemony-main-castle-transparent-reference.png` is a 500x500 RGBA transparent render of the castle, with no readable text visible.
- `hegemony-main-castle-presentation-reference.png` is a 1254x1254 RGB presentation render on white, showing the same castle and Hegemony crest/banner, with no readable text visible.
- `hegemony-main-castle-ui-reference.png` is a 1448x1086 RGB game/UI reference showing the castle on a grass map and in a `Core Fortress` inspector. Visible labels include `[WK]`, `Durability 204,000/204,000`, `Status OK`, `DESTROY`, and `Alliance Buildings X:487 Y:270`. No personal name, email, credential, or private operational identifier is visible.

## File and metadata inspection

All three PNG signatures, IHDR fields, chunk CRCs, and IEND markers passed. The presentation and UI images contain a supplied `caBX` ancillary chunk carrying C2PA/Content Credentials metadata; the transparent image does not. The C2PA-bearing bytes were preserved exactly. Public provenance intentionally records only the presence and preservation of that metadata, not embedded certificate, email, UUID, or signing details.

## Distribution boundary

Ael authorized public archival and release distribution of this named reference package. No separate open-license grant is asserted. The archive does not grant third-party tool/service rights, trademarks, canonical-identity rights, or unrelated Warpkeep material.
