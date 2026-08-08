from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_core_watcher_integration_profile",
    ROOT / "scripts" / "verify_core_watcher_integration_profile.py",
)
assert SPEC is not None and SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)


REQUIRED_FILES = (
    verify.PROFILE_PATH,
    verify.RUNTIME_PATH,
    verify.RELEASE_MANIFEST_PATH,
    verify.CHECKSUM_SIDECAR_PATH,
    verify.GALLERY_PATH,
    Path("manifests/core-watcher-level1-2026-08-03.source.json"),
    verify.PACKAGE_VERIFIER_PATH,
    Path("previews/core-watcher-level1-2026-08-03/00-core-watcher-presentation.jpg"),
    Path("previews/core-watcher-level1-2026-08-03/01-core-watcher-lod-lineup.jpg"),
    Path("previews/core-watcher-level1-2026-08-03/02-core-watcher-map-preview.png"),
)


def copy_fixture(destination: Path) -> None:
    for relative in REQUIRED_FILES:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def rewrite_profile(root: Path, mutate) -> str:
    path = root / verify.PROFILE_PATH
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    document["contractDigest"]["sha256"] = verify.ZERO_DIGEST
    zeroed = (
        json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(zeroed).hexdigest()
    document["contractDigest"]["sha256"] = digest
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return digest


class IntegrationProfileHappyPathTests(unittest.TestCase):
    def test_tracked_profile_and_cli(self) -> None:
        self.assertEqual(
            verify.verify(ROOT),
            "0a34614dfb42f754fd2524b23ef213c2db502768ad9230bd6a27a9198a8251c0",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "verify_core_watcher_integration_profile.py"),
                "--root",
                str(ROOT),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no runtime, gameplay, release, or activation authority", result.stdout)


class IntegrationProfileMutationTests(unittest.TestCase):
    def _mutated(self, mutate, pattern: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            digest = rewrite_profile(root, mutate)
            original = verify.EXPECTED_PROFILE_DIGEST
            verify.EXPECTED_PROFILE_DIGEST = digest
            try:
                with self.assertRaisesRegex(ValueError, pattern):
                    verify.verify(root)
            finally:
                verify.EXPECTED_PROFILE_DIGEST = original

    def test_digest_and_duplicate_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            path = root / verify.PROFILE_PATH
            raw = path.read_bytes().replace(b'"reviewOnly": true', b'"reviewOnly": false')
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                verify.verify(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            path = root / verify.PROFILE_PATH
            raw = path.read_bytes().replace(
                b'  "assetBinding": {',
                b'  "assetBinding": {},\n  "assetBinding": {',
                1,
            )
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                verify.verify(root)

    def test_digest_canonicalization_targets_only_the_declared_json_path(self) -> None:
        declared = "a" * 64
        raw = (
            b'{"echo":"'
            + declared.encode("ascii")
            + b'","contractDigest":{"sha256":"'
            + declared.encode("ascii")
            + b'"}}'
        )
        zeroed = verify._zeroed_contract_digest_bytes(raw, declared)
        self.assertIn(b'"echo":"' + declared.encode("ascii") + b'"', zeroed)
        self.assertIn(b'"sha256":"' + verify.ZERO_DIGEST.encode("ascii") + b'"', zeroed)

        escaped_value = raw.replace(
            b'"sha256":"' + declared.encode("ascii"),
            b'"sha256":"\\u0061' + declared[1:].encode("ascii"),
        )
        with self.assertRaisesRegex(ValueError, "64 literal lowercase"):
            verify._zeroed_contract_digest_bytes(escaped_value, declared)

    def test_deep_json_fails_closed_without_recursion_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            profile = root / verify.PROFILE_PATH
            depth = verify.MAX_JSON_DEPTH + 1
            profile.write_text(
                '{"nested":' + "[" * depth + "null" + "]" * depth + "}",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "JSON exceeds nesting limit"):
                verify.verify(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            profile = root / verify.PROFILE_PATH
            depth = 2000
            profile.write_text(
                '{"nested":' + "[" * depth + "null" + "]" * depth + "}",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "verify_core_watcher_integration_profile.py"),
                    "--root",
                    str(root),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("JSON exceeds nesting limit", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_oversized_numeric_tokens_fail_before_conversion(self) -> None:
        for token, pattern in (
            ("1" * (verify.MAX_JSON_NUMBER_CHARS + 1), "integer token exceeds"),
            (
                "1." + "0" * verify.MAX_JSON_NUMBER_CHARS,
                "floating-point token exceeds",
            ),
        ):
            with self.subTest(pattern=pattern):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    copy_fixture(root)
                    profile = root / verify.PROFILE_PATH
                    profile.write_text('{"number":' + token + "}", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, pattern):
                        verify.verify(root)

    def test_self_consistent_reformat_still_requires_pinned_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            path = root / verify.PROFILE_PATH
            document = json.loads(path.read_text(encoding="utf-8"))
            document["contractDigest"]["sha256"] = verify.ZERO_DIGEST
            zeroed = (
                json.dumps(document, indent=4, sort_keys=True, ensure_ascii=False) + "\n"
            ).encode("utf-8")
            digest = hashlib.sha256(zeroed).hexdigest()
            document["contractDigest"]["sha256"] = digest
            path.write_text(
                json.dumps(document, indent=4, sort_keys=True, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "production-pinned digest"):
                verify.verify(root)

    def test_tracked_runtime_and_preview_bytes_are_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            runtime = root / verify.RUNTIME_PATH
            runtime.write_bytes(runtime.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "tracked byte count mismatch: runtime manifest"):
                verify.verify(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            preview = root / REQUIRED_FILES[-1]
            payload = bytearray(preview.read_bytes())
            payload[-1] ^= 1
            preview.write_bytes(payload)
            with self.assertRaisesRegex(ValueError, "preview bytes or SHA-256 mismatch"):
                verify.verify(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            source = root / "manifests/core-watcher-level1-2026-08-03.source.json"
            document = json.loads(source.read_text(encoding="utf-8"))
            document["sanitization"]["sourceSemanticFingerprintSha256"] = "0" * 64
            source.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "tracked (byte count|SHA-256) mismatch"):
                verify.verify(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            sidecar = root / verify.CHECKSUM_SIDECAR_PATH
            sidecar.write_text(
                "0" * 64
                + "  warpkeep-core-watcher-level1-game-ready-2026-08-03-v1.zip\n",
                encoding="ascii",
            )
            with self.assertRaisesRegex(ValueError, "checksum sidecar"):
                verify.verify(root)

    def test_preview_paths_must_be_canonical_and_contained(self) -> None:
        cases = (
            "../00-core-watcher-presentation.jpg",
            "previews//core-watcher-level1-2026-08-03/00-core-watcher-presentation.jpg",
            "C:/outside/00-core-watcher-presentation.jpg",
            "previews/core-watcher-level1-2026-08-03/00-core-watcher\npresentation.jpg",
            "/".join("component" for _ in range(verify.MAX_TRACKED_PATH_COMPONENTS + 1)),
            "x" * (verify.MAX_TRACKED_PATH_CHARS + 1),
        )
        for path in cases:
            with self.subTest(path=path):
                self._mutated(
                    lambda value, path=path: value["presentation"]["previews"][0].__setitem__(
                        "path", path
                    ),
                    "unsafe tracked path",
                )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_tracked_files_reject_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            preview = root / REQUIRED_FILES[-1]
            other = root / REQUIRED_FILES[-2]
            preview.unlink()
            preview.symlink_to(other)
            with self.assertRaisesRegex(ValueError, "regular non-symlink"):
                verify.verify(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            profile = root / verify.PROFILE_PATH
            target = root / verify.RUNTIME_PATH
            profile.unlink()
            profile.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "regular non-symlink"):
                verify.verify(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            preview_directory = root / REQUIRED_FILES[-1].parent
            moved_directory = preview_directory.with_name("moved-preview-directory")
            preview_directory.rename(moved_directory)
            preview_directory.symlink_to(moved_directory, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "no symlink directories"):
                verify.verify(root)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_untrusted_root_symlink_loop_fails_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            loop = Path(directory) / "loop"
            loop.symlink_to(loop)
            with self.assertRaisesRegex(ValueError, "cannot be resolved safely"):
                verify.verify(loop)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "verify_core_watcher_integration_profile.py"),
                    "--root",
                    str(loop),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("cannot be resolved safely", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs unavailable")
    def test_tracked_special_file_fails_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            profile = root / verify.PROFILE_PATH
            profile.unlink()
            os.mkfifo(profile)
            with self.assertRaisesRegex(ValueError, "regular non-symlink"):
                verify.verify(root)

    def test_untrusted_root_cannot_supply_executable_helper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            helper = root / verify.PACKAGE_VERIFIER_PATH
            helper.write_text("raise AssertionError('untrusted helper executed')\n", encoding="utf-8")
            self.assertEqual(verify.verify(root), verify.EXPECTED_PROFILE_DIGEST)

    def test_oversized_inputs_fail_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            profile = root / verify.PROFILE_PATH
            profile.write_bytes(b" " * (verify.MAX_PROFILE_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "pre-read size limit"):
                verify.verify(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_fixture(root)
            preview = root / REQUIRED_FILES[-1]
            preview.write_bytes(b"x" * (verify.MAX_PREVIEW_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "pre-read size limit"):
                verify.verify(root)

    def test_authority_status_loading_and_unknown_fields_are_rejected(self) -> None:
        cases = (
            (lambda value: value["authorityBoundary"].__setitem__("combat", True), "authority boundary"),
            (lambda value: value["status"].__setitem__("activationAuthorized", True), "status gates"),
            (lambda value: value["loading"].__setitem__("redirectsAllowed", True), "loading policy"),
            (lambda value: value.__setitem__("privateAtlas", {}), "field set"),
        )
        for mutate, pattern in cases:
            with self.subTest(pattern=pattern):
                self._mutated(mutate, pattern)

    def test_profile_bounds_nodes_and_capacity_math_are_rejected(self) -> None:
        cases = (
            (lambda value: value["profiles"][0]["boundsGltfMeters"]["max"].__setitem__(0, 99.0), "emitted bounds"),
            (lambda value: value["profiles"][3]["partNodes"].__setitem__(0, "Renamed"), "part nodes"),
            (lambda value: value["instancing"]["capacityEvidence"].__setitem__("mapProfileVisibleTriangles", 1), "math mismatch"),
        )
        for mutate, pattern in cases:
            with self.subTest(pattern=pattern):
                self._mutated(mutate, pattern)

    def test_modern_quality_motion_mobile_and_slice_guards_are_rejected(self) -> None:
        cases = (
            (lambda value: value["qualityCamera"]["policies"]["reduced"].__setitem__("optionalAssetFetch", True), "quality/camera policy"),
            (lambda value: value["motion"]["targets"][0].__setitem__("node", "Missing_Node"), "motion policy"),
            (lambda value: value["fallbackAndAccessibility"]["testMatrix"]["safariIphone"].__setitem__("pageScroll", False), "fallback/accessibility policy"),
            (lambda value: value["futureGameplaySlices"][0].__setitem__("implementedHere", True), "future gameplay slices"),
        )
        for mutate, pattern in cases:
            with self.subTest(pattern=pattern):
                self._mutated(mutate, pattern)


if __name__ == "__main__":
    unittest.main()
