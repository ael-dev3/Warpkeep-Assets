from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from zipfile import ZIP_STORED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_core_watcher_level1",
    ROOT / "scripts" / "verify_core_watcher_level1.py",
)
assert SPEC is not None and SPEC.loader is not None
verify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)


def glb_document(triangle_count: int) -> tuple[dict, bytes]:
    positions: list[float] = []
    indices: list[int] = []
    for triangle in range(triangle_count):
        x = float(triangle * 2)
        base = triangle * 3
        positions.extend((x, 0.0, 0.0, x + 1.0, 0.0, 0.0, x, 1.0, 0.0))
        indices.extend((base, base + 1, base + 2))
    position_bytes = struct.pack("<" + "f" * len(positions), *positions)
    normal_values = [0.0, 0.0, 1.0] * (triangle_count * 3)
    normal_bytes = struct.pack("<" + "f" * len(normal_values), *normal_values)
    index_bytes = struct.pack("<" + "H" * len(indices), *indices)
    binary = position_bytes + normal_bytes + index_bytes
    document = {
        "asset": {"version": "2.0", "generator": "Warpkeep verifier test"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "CoreWatcher_Test"}],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0, "NORMAL": 1},
                        "indices": 2,
                        "material": 0,
                        "mode": 4,
                    }
                ]
            }
        ],
        "materials": [
            {"name": "WK_Core_Obsidian"},
            {"name": "WK_Core_BlackenedMetal"},
            {
                "name": "WK_Core_Ultraviolet",
                "extensions": {
                    "KHR_materials_emissive_strength": {"emissiveStrength": 3.5}
                },
            },
        ],
        "extensionsUsed": ["KHR_materials_emissive_strength"],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len(position_bytes),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": len(position_bytes),
                "byteLength": len(normal_bytes),
                "target": 34962,
            },
            {
                "buffer": 0,
                "byteOffset": len(position_bytes) + len(normal_bytes),
                "byteLength": len(index_bytes),
                "target": 34963,
            },
        ],
        "accessors": [
            {
                "bufferView": 0,
                "componentType": 5126,
                "count": triangle_count * 3,
                "type": "VEC3",
                "min": [0.0, 0.0, 0.0],
                "max": [float((triangle_count - 1) * 2 + 1), 1.0, 0.0],
            },
            {
                "bufferView": 1,
                "componentType": 5126,
                "count": triangle_count * 3,
                "type": "VEC3",
            },
            {
                "bufferView": 2,
                "componentType": 5123,
                "count": triangle_count * 3,
                "type": "SCALAR",
            },
        ],
    }
    return document, binary


def encode_glb(document: dict, binary: bytes) -> bytes:
    json_payload = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    json_payload += b" " * (-len(json_payload) % 4)
    binary += b"\x00" * (-len(binary) % 4)
    length = 12 + 8 + len(json_payload) + 8 + len(binary)
    return b"".join(
        (
            struct.pack("<4sII", b"glTF", 2, length),
            struct.pack("<II", len(json_payload), 0x4E4F534A),
            json_payload,
            struct.pack("<II", len(binary), 0x004E4942),
            binary,
        )
    )


def make_glb(triangle_count: int) -> bytes:
    document, binary = glb_document(triangle_count)
    return encode_glb(document, binary)


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + chunk_type
        + data
        + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
    )


def png_image(
    width: int, height: int, metadata: tuple[tuple[bytes, bytes], ...] = ()
) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return b"".join(
        (
            b"\x89PNG\r\n\x1a\n",
            png_chunk(b"IHDR", ihdr),
            *(png_chunk(chunk_type, data) for chunk_type, data in metadata),
            png_chunk(b"IDAT", zlib.compress(b"")),
            png_chunk(b"IEND", b""),
        )
    )


def jpeg_frame(width: int, height: int) -> bytes:
    frame = struct.pack(">BHHB", 8, height, width, 1) + b"\x01\x11\x00"
    scan = b"\x01\x01\x00\x00\x3f\x00"
    return b"".join(
        (
            b"\xff\xd8",
            b"\xff\xc0" + struct.pack(">H", len(frame) + 2) + frame,
            b"\xff\xda" + struct.pack(">H", len(scan) + 2) + scan,
            b"\xff\xd9",
        )
    )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def refresh_checksums(package: Path) -> None:
    paths = sorted(
        path
        for path in package.rglob("*")
        if path.is_file() and path.relative_to(package).as_posix() != verify.CHECKSUMS
    )
    lines = [
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
        f"{path.relative_to(package).as_posix()}\n"
        for path in paths
    ]
    (package / verify.CHECKSUMS).write_text("".join(lines), encoding="utf-8")


def make_package(parent: Path) -> Path:
    package = parent / verify.PACKAGE_NAME
    package.mkdir()
    (package / "PACKAGE-NOTICE.md").write_text("# Core Watcher notice\n", encoding="utf-8")
    (package / "README.md").write_text("# Core Watcher Level 1\n", encoding="utf-8")

    source = package / verify.SOURCE_BLEND
    source.parent.mkdir(parents=True)
    source.write_bytes(b"BLENDER17-01v0502" + b"\x00" * 32)

    previews = {
        name: (png_image(*dimensions) if name.endswith(".png") else jpeg_frame(*dimensions))
        for name, dimensions in verify.PREVIEW_DIMENSIONS.items()
    }
    for name, payload in previews.items():
        path = package / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    runtime_lods: list[dict] = []
    metrics = []
    for triangle_count, (tier, filename, _, _) in zip(
        (4, 3, 2, 1), verify.LOD_CONTRACT
    ):
        payload = make_glb(triangle_count)
        path = package / verify.RUNTIME_DIRECTORY / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        metric = verify.inspect_glb(payload, filename)
        metrics.append(metric)
        runtime_lods.append(
            {
                "tier": tier,
                "file": filename,
                "bytes": metric.bytes,
                "sha256": metric.sha256,
                "triangles": metric.triangles,
                "uploadedVertices": metric.uploaded_vertices,
                "embeddedBufferBytes": metric.embedded_buffer_bytes,
                "scenes": metric.scenes,
                "nodes": metric.nodes,
                "meshes": metric.meshes,
                "primitives": metric.primitives,
                "materials": metric.materials,
                "images": metric.images,
                "textures": metric.textures,
                "samplers": metric.samplers,
                "cameras": metric.cameras,
                "skins": metric.skins,
                "animations": [],
                "rigged": False,
                "externalUris": [],
                "extensionsUsed": list(metric.extensions_used),
            }
        )

    runtime_manifest = {
        "schema": "warpkeep.runtime-encounter-asset.v1",
        "version": "1.0.0",
        "revision": verify.REVISION,
        "assetId": verify.ASSET_ID,
        "category": "Encounters/Core/WatcherLevel1",
        "faction": "The Core",
        "name": "Core Watcher",
        "enemyKind": "core-watcher",
        "encounterLevel": 1,
        "combatEnabled": False,
        "authorityBoundary": verify.AUTHORITY_BOUNDARY,
        "lods": runtime_lods,
        "materialContract": {
            "alphaBlendMaterials": 0,
            "authoringNote": {
                "note": (
                    "Blender glTF export normalizes emissive color and strength; "
                    "the material records above are the emitted runtime values."
                ),
                "runtimeValuesDerivedFromExportedGlbs": True,
                "ultravioletNodeEmissionStrength": 3.5,
            },
            "heraldry": "none",
            "images": 0,
            "materials": [
                {
                    "name": material.name,
                    "alphaMode": material.alpha_mode,
                    "opaque": material.opaque,
                    "doubleSided": material.double_sided,
                    "baseColorFactor": list(material.base_color_factor),
                    "metallic": material.metallic,
                    "roughness": material.roughness,
                    "emissiveFactor": list(material.emissive_factor),
                    "emissiveStrength": material.emissive_strength,
                }
                for material in metrics[0].runtime_materials
            ],
            "textures": 0,
        },
    }
    write_json(package / verify.RUNTIME_MANIFEST, runtime_manifest)

    asset_manifest = {
        "schema": "warpkeep.authoring-package.v1",
        "version": "1.0.0",
        "revision": verify.REVISION,
        "category": "Encounters/Core/WatcherLevel1",
        "faction": "The Core",
        "canonicalEditableSource": verify.SOURCE_BLEND,
        "heroPreview": "Previews/Warpkeep_CoreWatcher_Level1_Presentation_1920.jpg",
        "lodLineupPreview": "Previews/Warpkeep_CoreWatcher_Level1_LOD_Lineup_2400.jpg",
        "transparentPreview": "Previews/Warpkeep_CoreWatcher_Level1_Transparent_1600.png",
        "mobilePreview": "Previews/Mobile/Warpkeep_CoreWatcher_Level1_Map_512.png",
        "qaReport": verify.QA_REPORT,
        "sourceSemanticFingerprintSha256": "a" * 64,
        "watcher": {
            "assetId": verify.ASSET_ID,
            "name": "Core Watcher",
            "enemyKind": "core-watcher",
            "encounterLevel": 1,
            "combatEnabled": False,
            "runtimeManifest": verify.RUNTIME_MANIFEST,
            "source": verify.SOURCE_BLEND,
            "triangles": {
                contract[0]: metric.triangles
                for contract, metric in zip(verify.LOD_CONTRACT, metrics)
            },
        },
    }
    write_json(package / verify.ASSET_MANIFEST, asset_manifest)

    checks = [
        {"check": name, "passed": True} for name in verify.EXPECTED_QA_CHECKS
    ]
    qa = {
        "schema": "warpkeep.runtime-qa.v1",
        "revision": verify.REVISION,
        "status": "passed",
        "budgets": {
            tier: {"triangles": triangle_ceiling, "bytes": byte_ceiling}
            for tier, _, triangle_ceiling, byte_ceiling in verify.LOD_CONTRACT
        },
        "checks": checks,
        "checksTotal": len(checks),
        "checksPassed": len(checks),
    }
    write_json(package / verify.QA_REPORT, qa)
    refresh_checksums(package)
    return package


def write_archive(package: Path, archive_path: Path, *, executable: str | None = None) -> None:
    with ZipFile(archive_path, "w", compression=ZIP_STORED) as archive:
        for path in sorted(item for item in package.rglob("*") if item.is_file()):
            relative = path.relative_to(package).as_posix()
            info = ZipInfo(f"{verify.PACKAGE_NAME}/{relative}")
            info.compress_type = ZIP_STORED
            mode = 0o755 if relative == executable else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(info, path.read_bytes())


def update_runtime_lod(package: Path, tier: str, payload: bytes) -> None:
    runtime_path = package / verify.RUNTIME_MANIFEST
    manifest = json.loads(runtime_path.read_text(encoding="utf-8"))
    record = next(item for item in manifest["lods"] if item["tier"] == tier)
    target = package / verify.RUNTIME_DIRECTORY / record["file"]
    target.write_bytes(payload)
    metric = verify.inspect_glb(payload, record["file"])
    record.update(
        {
            "bytes": metric.bytes,
            "sha256": metric.sha256,
            "triangles": metric.triangles,
            "uploadedVertices": metric.uploaded_vertices,
            "embeddedBufferBytes": metric.embedded_buffer_bytes,
            "scenes": metric.scenes,
            "nodes": metric.nodes,
            "meshes": metric.meshes,
            "primitives": metric.primitives,
            "materials": metric.materials,
            "images": metric.images,
            "textures": metric.textures,
            "samplers": metric.samplers,
            "cameras": metric.cameras,
            "skins": metric.skins,
            "animations": [],
            "rigged": False,
            "externalUris": [],
            "extensionsUsed": list(metric.extensions_used),
        }
    )
    write_json(runtime_path, manifest)
    asset_path = package / verify.ASSET_MANIFEST
    asset_manifest = json.loads(asset_path.read_text(encoding="utf-8"))
    asset_manifest["watcher"]["triangles"][tier] = metric.triangles
    write_json(asset_path, asset_manifest)
    refresh_checksums(package)


class CoreWatcherHappyPathTests(unittest.TestCase):
    def test_extracted_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = make_package(Path(directory))
            result = verify.verify_package(package)
            self.assertEqual(result.files, 15)
            self.assertEqual(result.triangles, (4, 3, 2, 1))

    def test_zip_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = make_package(root)
            archive = root / "core-watcher.zip"
            write_archive(package, archive)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "verify_core_watcher_level1.py"),
                    str(archive),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "Structurally verified Warpkeep_CoreWatcher_Level1_GameReady",
                result.stdout,
            )


class PackageSafetyTests(unittest.TestCase):
    def test_zip_rejects_traversal_and_duplicate_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            traversal = root / "traversal.zip"
            with ZipFile(traversal, "w") as archive:
                archive.writestr(f"{verify.PACKAGE_NAME}/../escape.txt", b"escape")
            with self.assertRaisesRegex(ValueError, "unsafe ZIP path"):
                verify.verify_package(traversal)

            duplicate = root / "duplicate.zip"
            with ZipFile(duplicate, "w") as archive:
                archive.writestr(f"{verify.PACKAGE_NAME}/README.md", b"one")
                with self.assertWarns(UserWarning):
                    archive.writestr(f"{verify.PACKAGE_NAME}/README.md", b"two")
            with self.assertRaisesRegex(ValueError, "duplicate ZIP entry"):
                verify.verify_package(duplicate)

    def test_zip_rejects_executable_member(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = make_package(root)
            archive = root / "executable.zip"
            write_archive(package, archive, executable="README.md")
            with self.assertRaisesRegex(ValueError, "executable ZIP entry"):
                verify.verify_package(archive)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_extracted_package_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = make_package(Path(directory))
            readme = package / "README.md"
            readme.unlink()
            readme.symlink_to(package / "PACKAGE-NOTICE.md")
            with self.assertRaisesRegex(ValueError, "regular file"):
                verify.verify_package(package)

    def test_nested_checksums_require_exact_coverage_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = make_package(Path(directory))
            checksum_path = package / verify.CHECKSUMS
            lines = checksum_path.read_text(encoding="utf-8").splitlines()
            checksum_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "coverage"):
                verify.verify_package(package)

            refresh_checksums(package)
            (package / "README.md").write_text("changed after hashing\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                verify.verify_package(package)

    def test_private_paths_and_credentials_are_rejected(self) -> None:
        for leaked in (
            "/Users/alice/project",
            "/private/var/folders/zz/transient-build",
            "github_pat_abcdefghijklmnopqrstuvwxyz",
        ):
            with self.subTest(leaked=leaked), tempfile.TemporaryDirectory() as directory:
                package = make_package(Path(directory))
                (package / "README.md").write_text(leaked + "\n", encoding="utf-8")
                refresh_checksums(package)
                with self.assertRaisesRegex(ValueError, "found in package file"):
                    verify.verify_package(package)


class RuntimeContractTests(unittest.TestCase):
    def test_runtime_identity_and_visual_only_authority_are_exact(self) -> None:
        for key, value in (
            ("enemyKind", "other"),
            ("combatEnabled", True),
            ("encounterLevel", True),
        ):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                package = make_package(Path(directory))
                path = package / verify.RUNTIME_MANIFEST
                manifest = json.loads(path.read_text(encoding="utf-8"))
                manifest[key] = value
                write_json(path, manifest)
                refresh_checksums(package)
                with self.assertRaisesRegex(ValueError, f"unexpected {key}"):
                    verify.verify_package(package)

        with tempfile.TemporaryDirectory() as directory:
            package = make_package(Path(directory))
            path = package / verify.RUNTIME_MANIFEST
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["authorityBoundary"]["health"] = True
            write_json(path, manifest)
            refresh_checksums(package)
            with self.assertRaisesRegex(ValueError, "authorityBoundary"):
                verify.verify_package(package)

    def test_lod_triangle_and_byte_counts_must_strictly_descend(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = make_package(Path(directory))
            high = (
                package
                / verify.RUNTIME_DIRECTORY
                / verify.LOD_CONTRACT[0][1]
            ).read_bytes()
            update_runtime_lod(package, "LOD1_Balanced", high)
            with self.assertRaisesRegex(ValueError, "strictly descending"):
                verify.verify_package(package)

    def test_manifest_metrics_are_recomputed_from_glb(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = make_package(Path(directory))
            path = package / verify.RUNTIME_MANIFEST
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["lods"][0]["triangles"] += 1
            write_json(path, manifest)
            refresh_checksums(package)
            with self.assertRaisesRegex(ValueError, "unexpected triangles"):
                verify.verify_package(package)

    def test_qa_requires_exact_unique_58_of_58_check_contract(self) -> None:
        for mutation in ("one-check", "duplicate-name"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                package = make_package(Path(directory))
                path = package / verify.QA_REPORT
                qa = json.loads(path.read_text(encoding="utf-8"))
                if mutation == "one-check":
                    qa["checks"] = qa["checks"][:1]
                    qa["checksTotal"] = 1
                    qa["checksPassed"] = 1
                else:
                    qa["checks"][1]["check"] = qa["checks"][0]["check"]
                write_json(path, qa)
                refresh_checksums(package)
                with self.assertRaisesRegex(ValueError, "exact 58 unique passed checks"):
                    verify.verify_package(package)

    def test_runtime_material_values_must_match_emitted_glbs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = make_package(Path(directory))
            path = package / verify.RUNTIME_MANIFEST
            manifest = json.loads(path.read_text(encoding="utf-8"))
            ultraviolet = next(
                material
                for material in manifest["materialContract"]["materials"]
                if material["name"] == "WK_Core_Ultraviolet"
            )
            ultraviolet["emissiveStrength"] += 0.25
            write_json(path, manifest)
            refresh_checksums(package)
            with self.assertRaisesRegex(ValueError, "differs from LOD0_High emitted"):
                verify.verify_package(package)


class PreviewStructureTests(unittest.TestCase):
    def test_png_rejects_metadata_chunks_and_bad_crc(self) -> None:
        for chunk_type in (b"eXIf", b"tEXt", b"zTXt", b"iTXt", b"tIME"):
            with self.subTest(chunk_type=chunk_type):
                payload = png_image(512, 512, ((chunk_type, b"metadata"),))
                with self.assertRaisesRegex(ValueError, "forbidden PNG metadata chunk"):
                    verify._png_dimensions(payload, "preview.png")

        corrupt = bytearray(png_image(512, 512))
        corrupt[29] ^= 0x01
        with self.assertRaisesRegex(ValueError, "CRC mismatch"):
            verify._png_dimensions(bytes(corrupt), "preview.png")

    def test_jpeg_rejects_comment_and_application_metadata(self) -> None:
        clean = jpeg_frame(1920, 1080)
        for marker in (0xFE, 0xE1, 0xE2, 0xED):
            with self.subTest(marker=marker):
                metadata = b"private metadata"
                segment = (
                    b"\xff"
                    + bytes((marker,))
                    + struct.pack(">H", len(metadata) + 2)
                    + metadata
                )
                # Insert after SOF to ensure the verifier scans past dimensions.
                scan_offset = clean.index(b"\xff\xda")
                payload = clean[:scan_offset] + segment + clean[scan_offset:]
                with self.assertRaisesRegex(ValueError, "forbidden JPEG metadata marker"):
                    verify._jpeg_dimensions(payload, "preview.jpg")


class DeepGlbTests(unittest.TestCase):
    def test_rejects_external_uri_and_unsupported_extension(self) -> None:
        document, binary = glb_document(1)
        document["buffers"][0]["uri"] = "mesh.bin"
        with self.assertRaisesRegex(ValueError, "URI"):
            verify.inspect_glb(encode_glb(document, binary))

        document, binary = glb_document(1)
        document["extensionsUsed"].append("KHR_draco_mesh_compression")
        with self.assertRaisesRegex(ValueError, "extension declaration"):
            verify.inspect_glb(encode_glb(document, binary))

    def test_rejects_wrong_material_contract(self) -> None:
        document, binary = glb_document(1)
        document["materials"][0]["name"] = "Borrowed_Hegemony_Material"
        with self.assertRaisesRegex(ValueError, "material names"):
            verify.inspect_glb(encode_glb(document, binary))

    def test_rejects_out_of_range_and_degenerate_indices(self) -> None:
        document, binary = glb_document(1)
        index_offset = document["bufferViews"][2]["byteOffset"]
        malformed = bytearray(binary)
        struct.pack_into("<H", malformed, index_offset + 4, 99)
        with self.assertRaisesRegex(ValueError, "out-of-range triangle index"):
            verify.inspect_glb(encode_glb(document, bytes(malformed)))

        malformed = bytearray(binary)
        struct.pack_into("<HHH", malformed, index_offset, 0, 0, 2)
        with self.assertRaisesRegex(ValueError, "degenerate triangle index"):
            verify.inspect_glb(encode_glb(document, bytes(malformed)))

        malformed = bytearray(binary)
        # Keep distinct indices and declared bounds, but place all points on a line.
        struct.pack_into("<fff", malformed, 12, 0.5, 0.5, 0.0)
        struct.pack_into("<fff", malformed, 24, 1.0, 1.0, 0.0)
        with self.assertRaisesRegex(ValueError, "zero-area or collinear triangle"):
            verify.inspect_glb(encode_glb(document, bytes(malformed)))

    def test_rejects_unexpected_vertex_attribute(self) -> None:
        document, binary = glb_document(1)
        document["meshes"][0]["primitives"][0]["attributes"]["TEXCOORD_0"] = 1
        with self.assertRaisesRegex(ValueError, "exactly POSITION and NORMAL"):
            verify.inspect_glb(encode_glb(document, binary))

    def test_rejects_nonfinite_positions_and_accessor_overrun(self) -> None:
        document, binary = glb_document(1)
        malformed = bytearray(binary)
        struct.pack_into("<f", malformed, 0, float("nan"))
        with self.assertRaisesRegex(ValueError, "non-finite accessor"):
            verify.inspect_glb(encode_glb(document, bytes(malformed)))

        document, binary = glb_document(1)
        document["accessors"][0]["count"] = 1000
        with self.assertRaisesRegex(ValueError, "accessor exceeds"):
            verify.inspect_glb(encode_glb(document, binary))


if __name__ == "__main__":
    unittest.main()
