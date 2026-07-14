#!/usr/bin/env python3
"""Verify local copies of Warpkeep-Assets release attachments."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import subprocess
import tempfile
from zipfile import ZipFile


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_stream(stream) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def safe_entry(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and not name.startswith("/")
        and "\\" not in name
        and path.parts
        and all(part not in ("", ".", "..") for part in path.parts)
    )


def verify_glb(stream, expected_size: int, label: str) -> None:
    header = stream.read(12)
    if len(header) != 12:
        raise ValueError(f"truncated GLB header: {label}")
    magic, version, declared_length = struct.unpack("<4sII", header)
    if magic != b"glTF" or version != 2 or declared_length != expected_size:
        raise ValueError(f"invalid GLB header: {label}")


def valid_blend_header(header: bytes) -> bool:
    legacy = (
        len(header) >= 12
        and header[:7] == b"BLENDER"
        and header[7:8] in (b"_", b"-")
        and header[8:9] in (b"v", b"V")
        and header[9:12].isdigit()
    )
    variable = (
        len(header) >= 17
        and header[:7] == b"BLENDER"
        and header[7:9].isdigit()
        and header[9:10] == b"-"
        and header[10:12].isdigit()
        and header[12:13] == b"v"
        and header[13:17].isdigit()
    )
    return legacy or variable


def verify_zstd_blend(stream, expected_compressed_bytes: object, container: dict, label: str) -> None:
    executable = shutil.which("zstd")
    if executable is None:
        raise ValueError(f"Zstandard verifier unavailable: {label}")

    if (
        not isinstance(expected_compressed_bytes, int)
        or isinstance(expected_compressed_bytes, bool)
        or expected_compressed_bytes <= 0
    ):
        raise ValueError(f"invalid declared compressed Blend byte count: {label}")
    expected_bytes = container.get("uncompressedBytes")
    if not isinstance(expected_bytes, int) or isinstance(expected_bytes, bool) or expected_bytes <= 0:
        raise ValueError(f"invalid declared Blend byte count: {label}")
    declared_header = container.get("uncompressedHeader", "")
    if not isinstance(declared_header, str):
        raise ValueError(f"invalid declared Blend header: {label}")
    declared_header_bytes = declared_header.encode("ascii", errors="strict")
    if not valid_blend_header(declared_header_bytes):
        raise ValueError(f"invalid declared Blend header: {label}")

    with tempfile.TemporaryDirectory(prefix="warpkeep-zstd-") as directory:
        compressed_path = Path(directory) / "source.blend.zst"
        with compressed_path.open("wb") as compressed:
            copied = 0
            while True:
                chunk = stream.read(min(1024 * 1024, expected_compressed_bytes - copied + 1))
                if not chunk:
                    break
                if copied + len(chunk) > expected_compressed_bytes:
                    raise ValueError(f"compressed Blend byte-count mismatch: {label}")
                compressed.write(chunk)
                copied += len(chunk)
            if copied != expected_compressed_bytes:
                raise ValueError(f"compressed Blend byte-count mismatch: {label}")

        try:
            process = subprocess.Popen(
                [executable, "--quiet", "--decompress", "--stdout", str(compressed_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise ValueError(f"Zstandard verifier unavailable: {label}") from exc

        total = 0
        actual_header = bytearray()
        try:
            assert process.stdout is not None
            while True:
                chunk = process.stdout.read(1024 * 1024)
                if not chunk:
                    break
                if len(actual_header) < 18:
                    actual_header.extend(chunk[: 18 - len(actual_header)])
                total += len(chunk)
                if total > expected_bytes:
                    process.kill()
                    process.wait()
                    raise ValueError(f"decompressed Blend byte-count mismatch: {label}")
            return_code = process.wait()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if process.stdout is not None:
                process.stdout.close()

    if return_code != 0:
        raise ValueError(f"invalid Zstandard Blend frame: {label}")
    if total != expected_bytes:
        raise ValueError(f"decompressed Blend byte-count mismatch: {label}")
    if not bytes(actual_header).startswith(declared_header_bytes) or not valid_blend_header(bytes(actual_header)):
        raise ValueError(f"decompressed Blend header mismatch: {label}")


def verify_blend(stream, expected: dict, label: str) -> None:
    header = stream.read(18)
    container = expected.get("container", {})
    compression = container.get("compression")
    if compression == "zstd":
        if header[:4] != b"\x28\xb5\x2f\xfd":
            raise ValueError(f"invalid Zstandard Blend signature: {label}")
        stream.seek(0)
        verify_zstd_blend(stream, expected.get("bytes"), container, label)
        return
    if compression is not None:
        raise ValueError(f"unsupported Blend compression: {label}")
    if not valid_blend_header(header):
        raise ValueError(f"invalid uncompressed Blend header: {label}")


def verify_file(path: Path, expected: dict) -> None:
    if path.stat().st_size != expected["bytes"]:
        raise ValueError(f"byte-count mismatch: {path.name}")
    if sha256_path(path) != expected["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {path.name}")


def verify_png(path: Path, expected: dict) -> None:
    verify_file(path, expected)
    with path.open("rb") as stream:
        header = stream.read(33)
    if len(header) != 33 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"invalid PNG signature: {path.name}")
    chunk_length, chunk_type = struct.unpack(">I4s", header[8:16])
    if chunk_length != 13 or chunk_type != b"IHDR":
        raise ValueError(f"invalid PNG IHDR: {path.name}")
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", header[16:29]
    )
    if compression != 0 or filtering != 0 or interlace not in (0, 1):
        raise ValueError(f"unsupported PNG encoding: {path.name}")
    color_types = {0: "grayscale", 2: "RGB", 3: "indexed", 4: "grayscale-alpha", 6: "RGBA"}
    actual = {
        "width": width,
        "height": height,
        "bitDepth": bit_depth,
        "colorType": color_types.get(color_type, f"unknown-{color_type}"),
        "alpha": color_type in (4, 6),
        "interlaced": interlace == 1,
    }
    expected_image = expected.get("image")
    if expected_image is None or actual != expected_image:
        raise ValueError(f"PNG metadata mismatch: {path.name}")


def verify_archive(path: Path, expected: dict) -> None:
    verify_file(path, expected)

    expected_entries = {entry["path"]: entry for entry in expected["entries"]}
    actual_names: list[str] = []
    with ZipFile(path) as archive:
        for info in archive.infolist():
            if not safe_entry(info.filename):
                raise ValueError(f"unsafe ZIP path: {info.filename}")
            mode = info.external_attr >> 16
            if info.is_dir() or stat.S_ISLNK(mode):
                raise ValueError(f"unsupported ZIP entry: {info.filename}")
            if info.filename in actual_names:
                raise ValueError(f"duplicate ZIP path: {info.filename}")
            actual_names.append(info.filename)
            record = expected_entries.get(info.filename)
            if record is None:
                raise ValueError(f"unexpected ZIP entry: {info.filename}")
            if info.file_size != record["bytes"]:
                raise ValueError(f"entry byte-count mismatch: {info.filename}")
            with archive.open(info) as stream:
                if info.filename.endswith(".glb"):
                    verify_glb(stream, info.file_size, info.filename)
                elif info.filename.endswith((".blend", ".blend1")):
                    verify_blend(stream, record, info.filename)
                stream.seek(0)
                if sha256_stream(stream) != record["sha256"]:
                    raise ValueError(f"entry SHA-256 mismatch: {info.filename}")

    if set(actual_names) != set(expected_entries):
        missing = sorted(set(expected_entries) - set(actual_names))
        raise ValueError(f"missing ZIP entries: {missing}")


def verify_checksum_sidecar(manifest_path: Path, attachments: list[dict]) -> None:
    sidecar = manifest_path.with_name("SHA256SUMS.txt")
    if not sidecar.exists():
        return

    expected = {attachment["name"]: attachment["sha256"] for attachment in attachments}
    if len(expected) != len(attachments):
        raise ValueError("duplicate release attachment name")
    actual: dict[str, str] = {}
    for line_number, line in enumerate(sidecar.read_text(encoding="utf-8").splitlines(), 1):
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise ValueError(f"invalid release checksum line {line_number}: {sidecar.name}")
        digest, name = parts
        if (
            len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or not safe_entry(name)
            or PurePosixPath(name).name != name
        ):
            raise ValueError(f"invalid release checksum line {line_number}: {sidecar.name}")
        if name in actual:
            raise ValueError(f"duplicate release checksum name: {name}")
        actual[name] = digest

    expected_with_optional_manifest = dict(expected)
    if "manifest.json" in actual:
        expected_with_optional_manifest["manifest.json"] = sha256_path(manifest_path)

    if actual != expected_with_optional_manifest:
        raise ValueError(f"release checksum sidecar mismatch: {sidecar.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--asset-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for attachment in manifest["attachments"]:
        path = args.asset_dir / attachment["name"]
        media_type = attachment["mediaType"]
        if media_type == "application/zip":
            verify_archive(path, attachment)
        elif media_type == "image/png":
            verify_png(path, attachment)
        else:
            raise ValueError(f"unsupported media type: {media_type}")
    verify_checksum_sidecar(args.manifest, manifest["attachments"])
    print(f"Verified {len(manifest['attachments'])} release attachments for {manifest['tag']}.")


if __name__ == "__main__":
    main()
