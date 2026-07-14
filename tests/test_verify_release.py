from __future__ import annotations

from io import BytesIO
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_release", ROOT / "scripts" / "verify_release.py")
assert SPEC is not None and SPEC.loader is not None
verify_release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_release)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BlendVerificationTests(unittest.TestCase):
    def test_zstd_blend_signature(self) -> None:
        verify_release.verify_blend(
            BytesIO(b"\x28\xb5\x2f\xfd" + b"\x00" * 32),
            {
                "container": {
                    "compression": "zstd",
                    "uncompressedHeader": "BLENDER17-01v0502",
                }
            },
            "model.blend",
        )

    def test_zstd_blend_rejects_wrong_signature(self) -> None:
        with self.assertRaisesRegex(ValueError, "Zstandard Blend signature"):
            verify_release.verify_blend(
                BytesIO(b"not-zstd" + b"\x00" * 32),
                {
                    "container": {
                        "compression": "zstd",
                        "uncompressedHeader": "BLENDER17-01v0502",
                    }
                },
                "model.blend",
            )

    def test_uncompressed_legacy_and_variable_headers(self) -> None:
        verify_release.verify_blend(BytesIO(b"BLENDER-v502" + b"\x00" * 8), {}, "legacy.blend")
        verify_release.verify_blend(BytesIO(b"BLENDER17-01v0502" + b"\x00"), {}, "variable.blend")

    def test_archive_with_glb_and_blend(self) -> None:
        glb = struct.pack("<4sII", b"glTF", 2, 12)
        blend = b"\x28\xb5\x2f\xfd" + b"\x00" * 28
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "models.zip"
            with ZipFile(archive_path, "w") as archive:
                archive.writestr("package/model.glb", glb)
                archive.writestr("package/model.blend", blend)
            archive_bytes = archive_path.read_bytes()
            expected = {
                "bytes": len(archive_bytes),
                "sha256": sha256(archive_bytes),
                "entries": [
                    {
                        "path": "package/model.glb",
                        "bytes": len(glb),
                        "sha256": sha256(glb),
                    },
                    {
                        "path": "package/model.blend",
                        "bytes": len(blend),
                        "sha256": sha256(blend),
                        "container": {
                            "compression": "zstd",
                            "uncompressedHeader": "BLENDER17-01v0502",
                        },
                    },
                ],
            }
            verify_release.verify_archive(archive_path, expected)


class ChecksumSidecarTests(unittest.TestCase):
    def test_cli_enforces_release_checksum_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "models.zip"
            with ZipFile(archive_path, "w"):
                pass
            archive_bytes = archive_path.read_bytes()
            manifest_path = root / "manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "tag": "test-release",
                        "attachments": [
                            {
                                "name": archive_path.name,
                                "bytes": len(archive_bytes),
                                "sha256": sha256(archive_bytes),
                                "mediaType": "application/zip",
                                "entries": [],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (root / "SHA256SUMS.txt").write_text(
                f"{'b' * 64}  {archive_path.name}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "verify_release.py"),
                    "--manifest",
                    str(manifest_path),
                    "--asset-dir",
                    str(root),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("release checksum sidecar mismatch", result.stderr)

    def test_release_checksum_sidecar_matches_attachments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            (manifest_path.parent / "SHA256SUMS.txt").write_text(
                f"{'a' * 64}  models.zip\n",
                encoding="utf-8",
            )
            verify_release.verify_checksum_sidecar(
                manifest_path,
                [{"name": "models.zip", "sha256": "a" * 64}],
            )

    def test_release_checksum_sidecar_accepts_verified_manifest_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text('{"tag": "test"}\n', encoding="utf-8")
            (manifest_path.parent / "SHA256SUMS.txt").write_text(
                f"{sha256(manifest_path.read_bytes())}  manifest.json\n"
                f"{'a' * 64}  models.zip\n",
                encoding="utf-8",
            )
            verify_release.verify_checksum_sidecar(
                manifest_path,
                [{"name": "models.zip", "sha256": "a" * 64}],
            )

    def test_release_checksum_sidecar_rejects_stale_manifest_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text('{"tag": "test"}\n', encoding="utf-8")
            (manifest_path.parent / "SHA256SUMS.txt").write_text(
                f"{'b' * 64}  manifest.json\n"
                f"{'a' * 64}  models.zip\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "release checksum sidecar mismatch"):
                verify_release.verify_checksum_sidecar(
                    manifest_path,
                    [{"name": "models.zip", "sha256": "a" * 64}],
                )

    def test_release_checksum_sidecar_rejects_unknown_extra_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text('{"tag": "test"}\n', encoding="utf-8")
            (manifest_path.parent / "SHA256SUMS.txt").write_text(
                f"{'a' * 64}  models.zip\n"
                f"{'c' * 64}  notes.txt\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "release checksum sidecar mismatch"):
                verify_release.verify_checksum_sidecar(
                    manifest_path,
                    [{"name": "models.zip", "sha256": "a" * 64}],
                )

    def test_release_checksum_sidecar_rejects_stale_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            (manifest_path.parent / "SHA256SUMS.txt").write_text(
                f"{'b' * 64}  models.zip\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "release checksum sidecar mismatch"):
                verify_release.verify_checksum_sidecar(
                    manifest_path,
                    [{"name": "models.zip", "sha256": "a" * 64}],
                )

    def test_release_checksum_sidecar_rejects_duplicate_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            (manifest_path.parent / "SHA256SUMS.txt").write_text(
                f"{'a' * 64}  models.zip\n{'a' * 64}  models.zip\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate release checksum name"):
                verify_release.verify_checksum_sidecar(
                    manifest_path,
                    [{"name": "models.zip", "sha256": "a" * 64}],
                )


if __name__ == "__main__":
    unittest.main()
