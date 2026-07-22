from __future__ import annotations

from io import BytesIO
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_release", ROOT / "scripts" / "verify_release.py")
assert SPEC is not None and SPEC.loader is not None
verify_release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_release)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


VALID_BLEND = b"BLENDER17-01v0502" + b"\x00" * 16
VALID_ZSTD_BLEND = bytes.fromhex(
    "28b52ffd0458c5000090424c454e44455231372d303176303530320001003a1006b6038fcb"
)


class BlendVerificationTests(unittest.TestCase):
    def test_zstd_blend_frame_and_header(self) -> None:
        verify_release.verify_blend(
            BytesIO(VALID_ZSTD_BLEND),
            {
                "bytes": len(VALID_ZSTD_BLEND),
                "container": {
                    "compression": "zstd",
                    "uncompressedHeader": "BLENDER17-01v0502",
                    "uncompressedBytes": len(VALID_BLEND),
                }
            },
            "model.blend",
        )

    def test_zstd_blend_rejects_truncated_frame(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid Zstandard Blend frame"):
            verify_release.verify_blend(
                BytesIO(b"\x28\xb5\x2f\xfd" + b"X" * 28),
                {
                    "bytes": 32,
                    "container": {
                        "compression": "zstd",
                        "uncompressedHeader": "BLENDER17-01v0502",
                        "uncompressedBytes": len(VALID_BLEND),
                    }
                },
                "model.blend",
            )

    def test_zstd_blend_rejects_compressed_size_overflow(self) -> None:
        with self.assertRaisesRegex(ValueError, "compressed Blend byte-count mismatch"):
            verify_release.verify_blend(
                BytesIO(VALID_ZSTD_BLEND + b"untrusted trailing bytes"),
                {
                    "bytes": len(VALID_ZSTD_BLEND),
                    "container": {
                        "compression": "zstd",
                        "uncompressedHeader": "BLENDER17-01v0502",
                        "uncompressedBytes": len(VALID_BLEND),
                    },
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

    def test_zstd_blend_rejects_actual_header_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "decompressed Blend header mismatch"):
            verify_release.verify_blend(
                BytesIO(VALID_ZSTD_BLEND),
                {
                    "bytes": len(VALID_ZSTD_BLEND),
                    "container": {
                        "compression": "zstd",
                        "uncompressedHeader": "BLENDER17-01v0503",
                        "uncompressedBytes": len(VALID_BLEND),
                    }
                },
                "model.blend",
            )

    def test_zstd_blend_rejects_uncompressed_size_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "decompressed Blend byte-count mismatch"):
            verify_release.verify_blend(
                BytesIO(VALID_ZSTD_BLEND),
                {
                    "bytes": len(VALID_ZSTD_BLEND),
                    "container": {
                        "compression": "zstd",
                        "uncompressedHeader": "BLENDER17-01v0502",
                        "uncompressedBytes": len(VALID_BLEND) - 1,
                    }
                },
                "model.blend",
            )

    def test_zstd_blend_fails_closed_without_verifier(self) -> None:
        with patch.object(verify_release.shutil, "which", return_value=None):
            with self.assertRaisesRegex(ValueError, "Zstandard verifier unavailable"):
                verify_release.verify_blend(
                    BytesIO(VALID_ZSTD_BLEND),
                    {
                        "bytes": len(VALID_ZSTD_BLEND),
                        "container": {
                            "compression": "zstd",
                            "uncompressedHeader": "BLENDER17-01v0502",
                            "uncompressedBytes": len(VALID_BLEND),
                        }
                    },
                    "model.blend",
                )

    def test_uncompressed_legacy_and_variable_headers(self) -> None:
        verify_release.verify_blend(BytesIO(b"BLENDER-v502" + b"\x00" * 8), {}, "legacy.blend")
        verify_release.verify_blend(BytesIO(b"BLENDER17-01v0502" + b"\x00"), {}, "variable.blend")

    def test_archive_with_glb_and_blend(self) -> None:
        glb = struct.pack("<4sII", b"glTF", 2, 12)
        blend = VALID_ZSTD_BLEND
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "models.zip"
            with ZipFile(archive_path, "w") as archive:
                archive.writestr("package/model.glb", glb)
                archive.writestr("package/model.blend", blend)
                archive.writestr("package/model.blend1", blend)
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
                            "uncompressedBytes": len(VALID_BLEND),
                        },
                    },
                    {
                        "path": "package/model.blend1",
                        "bytes": len(blend),
                        "sha256": sha256(blend),
                        "container": {
                            "compression": "zstd",
                            "uncompressedHeader": "BLENDER17-01v0502",
                            "uncompressedBytes": len(VALID_BLEND),
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

    def test_release_checksum_sidecar_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            with self.assertRaisesRegex(ValueError, "pinned regular file"):
                verify_release.verify_checksum_sidecar(
                    manifest_path,
                    [{"name": "models.zip", "sha256": "a" * 64}],
                )


class ManifestAndFilesystemSafetyTests(unittest.TestCase):
    def write_manifest(self, root: Path, document: dict) -> Path:
        path = root / "manifest.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def valid_attachment(self, name: str = "models.zip") -> dict:
        empty_archive = BytesIO()
        with ZipFile(empty_archive, "w"):
            pass
        payload = empty_archive.getvalue()
        return {
            "name": name,
            "bytes": len(payload),
            "sha256": sha256(payload),
            "mediaType": "application/zip",
            "entries": [],
        }

    def test_manifest_rejects_traversal_absolute_and_windows_attachment_names(self) -> None:
        for name in ("../outside.zip", "/outside.zip", "C:/outside.zip", "folder/models.zip"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "unsafe attachment name"):
                    verify_release.validate_attachment_record(self.valid_attachment(name), 0)

    def test_zip_member_names_must_be_canonical(self) -> None:
        for name in ("pkg//file.txt", "pkg/./file.txt", "pkg/../file.txt"):
            with self.subTest(name=name):
                self.assertFalse(verify_release.safe_entry(name))
        self.assertTrue(verify_release.safe_entry("pkg/file.txt"))

    def test_hash_rejects_truncation_and_growth(self) -> None:
        with self.assertRaisesRegex(ValueError, "ended before"):
            verify_release.sha256_stream(BytesIO(b"short"), 6, "fixture")
        with self.assertRaisesRegex(ValueError, "exceeded"):
            verify_release.sha256_stream(BytesIO(b"growing"), 4, "fixture")
        self.assertEqual(
            verify_release.sha256_stream(BytesIO(b"exact"), 5, "fixture"),
            sha256(b"exact"),
        )

    def test_manifest_rejects_empty_duplicate_and_oversized_attachment_sets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            empty = self.write_manifest(root, {"tag": "test", "attachments": []})
            with self.assertRaisesRegex(ValueError, "non-empty attachment"):
                verify_release.load_manifest(empty)

            duplicate = self.write_manifest(
                root,
                {
                    "tag": "test",
                    "attachments": [self.valid_attachment(), self.valid_attachment()],
                },
            )
            with self.assertRaisesRegex(ValueError, "duplicate release attachment"):
                verify_release.load_manifest(duplicate)

            oversized = self.valid_attachment()
            oversized["bytes"] = verify_release.MAX_ATTACHMENT_BYTES + 1
            with self.assertRaisesRegex(ValueError, "invalid attachment byte count"):
                verify_release.validate_attachment_record(oversized, 0)

    def test_manifest_rejects_control_characters_and_untrusted_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unsafe_tag = self.write_manifest(
                root,
                {"tag": "bad\u001b]8;;url", "attachments": [self.valid_attachment()]},
            )
            with self.assertRaisesRegex(ValueError, "invalid release tag"):
                verify_release.load_manifest(unsafe_tag)

            trusted = self.write_manifest(
                root,
                {"tag": "test", "attachments": [self.valid_attachment()]},
            )
            with self.assertRaisesRegex(ValueError, "trusted manifest SHA-256 mismatch"):
                verify_release.load_manifest(trusted, "0" * 64)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_attachment_reader_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.zip"
            target.write_bytes(b"not an archive")
            link = root / "models.zip"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "pinned regular file"):
                verify_release.read_bounded_regular_file(
                    link, verify_release.MAX_ATTACHMENT_BYTES, "attachment"
                )

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs unavailable")
    def test_attachment_reader_rejects_fifo_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fifo = Path(directory) / "models.zip"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError, "pinned regular file"):
                verify_release.read_bounded_regular_file(
                    fifo, verify_release.MAX_ATTACHMENT_BYTES, "attachment"
                )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_asset_directory_reader_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            link = root / "assets"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "pinned real directory"):
                with verify_release.open_pinned_directory(link):
                    self.fail("symlinked asset directory was accepted")

    def test_cli_rejects_attachment_escape_before_reading_outside_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "assets"
            assets.mkdir()
            outside = root / "outside.zip"
            with ZipFile(outside, "w"):
                pass
            payload = outside.read_bytes()
            manifest = self.write_manifest(
                root,
                {
                    "tag": "test",
                    "attachments": [{
                        "name": "../outside.zip",
                        "bytes": len(payload),
                        "sha256": sha256(payload),
                        "mediaType": "application/zip",
                        "entries": [],
                    }],
                },
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "verify_release.py"),
                    "--manifest",
                    str(manifest),
                    "--asset-dir",
                    str(assets),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe attachment name", result.stderr)


class ArchiveResourceSafetyTests(unittest.TestCase):
    def test_archive_rejects_excessive_compression_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "models.zip"
            payload = b"0" * (1024 * 1024)
            with ZipFile(archive_path, "w", compression=8) as archive:
                archive.writestr("payload.bin", payload)
            archive_bytes = archive_path.read_bytes()
            expected = {
                "bytes": len(archive_bytes),
                "sha256": sha256(archive_bytes),
                "entries": [{
                    "path": "payload.bin",
                    "bytes": len(payload),
                    "sha256": sha256(payload),
                }],
            }
            with self.assertRaisesRegex(ValueError, "compression-ratio limit"):
                verify_release.verify_archive(archive_path, expected)

    def test_archive_rejects_actual_entry_count_above_the_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "models.zip"
            with ZipFile(archive_path, "w") as archive:
                archive.writestr("one.txt", b"one")
                archive.writestr("two.txt", b"two")
            archive_bytes = archive_path.read_bytes()
            expected = {
                "bytes": len(archive_bytes),
                "sha256": sha256(archive_bytes),
                "entries": [
                    {"path": "one.txt", "bytes": 3, "sha256": sha256(b"one")}
                ],
            }
            with patch.object(verify_release, "MAX_ARCHIVE_ENTRIES", 1):
                with self.assertRaisesRegex(ValueError, "entry-count limit"):
                    verify_release.verify_archive(archive_path, expected)

    def test_archive_rejects_duplicate_actual_paths_with_set_accounting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "models.zip"
            with ZipFile(archive_path, "w") as archive:
                archive.writestr("same.txt", b"one")
                with self.assertWarns(UserWarning):
                    archive.writestr("same.txt", b"two")
            archive_bytes = archive_path.read_bytes()
            expected = {
                "bytes": len(archive_bytes),
                "sha256": sha256(archive_bytes),
                "entries": [
                    {"path": "same.txt", "bytes": 3, "sha256": sha256(b"one")}
                ],
            }
            with self.assertRaisesRegex(ValueError, "duplicate ZIP path"):
                verify_release.verify_archive(archive_path, expected)

    def test_archive_rejects_actual_total_bytes_above_the_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "models.zip"
            with ZipFile(archive_path, "w") as archive:
                archive.writestr("one.txt", b"one")
                archive.writestr("two.txt", b"two")
            archive_bytes = archive_path.read_bytes()
            expected = {
                "bytes": len(archive_bytes),
                "sha256": sha256(archive_bytes),
                "entries": [
                    {"path": "one.txt", "bytes": 3, "sha256": sha256(b"one")},
                    {"path": "two.txt", "bytes": 3, "sha256": sha256(b"two")},
                ],
            }
            with patch.object(verify_release, "MAX_ARCHIVE_UNCOMPRESSED_BYTES", 5):
                with self.assertRaisesRegex(ValueError, "total size limit"):
                    verify_release.verify_archive(archive_path, expected)

    def test_zstd_secondary_bytes_and_time_share_invocation_budgets(self) -> None:
        expected = {
            "bytes": len(VALID_ZSTD_BLEND),
            "container": {
                "compression": "zstd",
                "uncompressedHeader": "BLENDER17-01v0502",
                "uncompressedBytes": len(VALID_BLEND),
            },
        }
        byte_budget = verify_release.VerificationBudget(
            secondary_bytes=len(VALID_BLEND) - 1,
            seconds=5,
        )
        with self.assertRaisesRegex(ValueError, "secondary decompression budget"):
            verify_release.verify_blend(
                BytesIO(VALID_ZSTD_BLEND), expected, "model.blend", byte_budget
            )

        time_budget = verify_release.VerificationBudget(secondary_bytes=1024, seconds=0)
        with self.assertRaisesRegex(ValueError, "time budget exhausted"):
            verify_release.verify_blend(
                BytesIO(VALID_ZSTD_BLEND), expected, "model.blend", time_budget
            )


class ManifestBuilderSafetyTests(unittest.TestCase):
    def test_builder_rejects_traversal_member_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in (
                "warpkeep-stone-letter-sources-v1.zip",
                "warpkeep-title-assemblies-v1.zip",
            ):
                with ZipFile(root / name, "w") as archive:
                    archive.writestr(
                        "../../outside.txt" if name.startswith("warpkeep-stone") else "safe.txt",
                        b"payload",
                    )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_release_manifest.py"),
                    "--asset-dir",
                    str(root),
                    "--output",
                    str(root / "manifest.json"),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsafe ZIP path", result.stderr)


if __name__ == "__main__":
    unittest.main()
