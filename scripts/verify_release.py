#!/usr/bin/env python3
"""Verify local copies of Warpkeep-Assets release attachments."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import selectors
import shutil
import stat
import struct
import subprocess
import tempfile
import time
import unicodedata
from zipfile import ZipFile


MEBIBYTE = 1024 * 1024
MAX_MANIFEST_BYTES = 2 * MEBIBYTE
MAX_CHECKSUM_SIDECAR_BYTES = 2 * MEBIBYTE
MAX_ATTACHMENTS = 128
MAX_ATTACHMENT_BYTES = 512 * MEBIBYTE
MAX_ARCHIVE_ENTRIES = 4096
MAX_ARCHIVE_ENTRY_BYTES = 512 * MEBIBYTE
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 1024 * MEBIBYTE
MAX_ARCHIVE_SECONDARY_UNCOMPRESSED_BYTES = 1024 * MEBIBYTE
MAX_VERIFICATION_SECONDARY_UNCOMPRESSED_BYTES = 2 * 1024 * MEBIBYTE
MAX_ARCHIVE_COMPRESSION_RATIO = 200
MAX_ZSTD_SECONDS = 30
MAX_ZSTD_MEMORY_MEBIBYTES = 512
MAX_VERIFICATION_SECONDS = 120
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
TAG_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")


def sha256_path(path: Path, maximum_bytes: int = MAX_ATTACHMENT_BYTES) -> str:
    with open_bounded_regular_file(path, maximum_bytes, path.name) as (stream, opened):
        return sha256_stream(stream, opened.st_size, path.name)


def sha256_stream(stream, expected_bytes: int, label: str) -> str:
    """Hash exactly the declared bytes and reject truncation or concurrent growth."""
    digest = hashlib.sha256()
    remaining = expected_bytes
    while remaining:
        chunk = stream.read(min(1024 * 1024, remaining))
        if not chunk:
            raise ValueError(f"file ended before its declared byte count: {label}")
        if len(chunk) > remaining:
            raise ValueError(f"file exceeded its declared byte count: {label}")
        digest.update(chunk)
        remaining -= len(chunk)
    if stream.read(1):
        raise ValueError(f"file exceeded its declared byte count: {label}")
    return digest.hexdigest()


def safe_entry(name: str) -> bool:
    if not isinstance(name, str) or not name.isprintable():
        return False
    path = PurePosixPath(name)
    windows = PureWindowsPath(name)
    return (
        bool(name)
        and not name.startswith("/")
        and "\\" not in name
        and not windows.drive
        and path.parts
        and all(part not in ("", ".", "..") for part in path.parts)
        and path.as_posix() == name
        and unicodedata.normalize("NFC", name) == name
    )


def safe_attachment_name(name: object) -> bool:
    return (
        isinstance(name, str)
        and safe_entry(name)
        and PurePosixPath(name).name == name
    )


def bounded_int(value: object, *, minimum: int, maximum: int) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and minimum <= value <= maximum
    )


def valid_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


class VerificationBudget:
    def __init__(
        self,
        secondary_bytes: int = MAX_VERIFICATION_SECONDARY_UNCOMPRESSED_BYTES,
        seconds: int = MAX_VERIFICATION_SECONDS,
    ) -> None:
        self.secondary_bytes_remaining = secondary_bytes
        self.deadline = time.monotonic() + seconds

    def claim_secondary_bytes(self, amount: int, label: str) -> None:
        if amount > self.secondary_bytes_remaining:
            raise ValueError(f"secondary decompression budget exceeded: {label}")
        self.secondary_bytes_remaining -= amount

    def entry_deadline(self, label: str) -> float:
        now = time.monotonic()
        if now >= self.deadline:
            raise ValueError(f"verification time budget exhausted: {label}")
        return min(self.deadline, now + MAX_ZSTD_SECONDS)


@contextmanager
def open_pinned_directory(path: Path):
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        linked = os.stat(path, follow_symlinks=False)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or not stat.S_ISDIR(linked.st_mode)
            or opened.st_dev != linked.st_dev
            or opened.st_ino != linked.st_ino
        ):
            raise ValueError("asset directory must be a pinned real directory")
        yield descriptor
        final = os.fstat(descriptor)
        if final.st_dev != opened.st_dev or final.st_ino != opened.st_ino:
            raise ValueError("asset directory changed during verification")
    except OSError as exc:
        raise ValueError("asset directory must be a pinned real directory") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


@contextmanager
def open_bounded_regular_file(
    path: Path,
    maximum_bytes: int,
    label: str,
    directory_fd: int | None = None,
):
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(path, flags, dir_fd=directory_fd)
        opened = os.fstat(descriptor)
        linked = os.stat(path, dir_fd=directory_fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(linked.st_mode)
            or opened.st_dev != linked.st_dev
            or opened.st_ino != linked.st_ino
        ):
            raise ValueError(f"not a pinned regular file: {label}")
        if opened.st_size > maximum_bytes:
            raise ValueError(f"file exceeds the verification size limit: {label}")
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            yield stream, opened
            final = os.fstat(stream.fileno())
            if (
                final.st_dev != opened.st_dev
                or final.st_ino != opened.st_ino
                or final.st_size != opened.st_size
                or final.st_mtime_ns != opened.st_mtime_ns
            ):
                raise ValueError(f"file changed during verification: {label}")
    except OSError as exc:
        raise ValueError(f"unable to open a pinned regular file: {label}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def read_bounded_regular_file(path: Path, maximum_bytes: int, label: str) -> bytes:
    with open_bounded_regular_file(path, maximum_bytes, label) as (stream, opened):
        payload = stream.read(maximum_bytes + 1)
        if len(payload) != opened.st_size:
            raise ValueError(f"file byte-count changed during verification: {label}")
        return payload


def declared_secondary_bytes(record: dict) -> int:
    total = 0
    for entry in record.get("entries", []):
        container = entry.get("container")
        if isinstance(container, dict) and container.get("compression") == "zstd":
            total += container["uncompressedBytes"]
    return total


def validate_attachment_record(record: object, index: int) -> dict:
    if not isinstance(record, dict):
        raise ValueError(f"invalid attachment record at index {index}")
    name = record.get("name")
    if not safe_attachment_name(name):
        raise ValueError(f"unsafe attachment name at index {index}")
    if not bounded_int(record.get("bytes"), minimum=0, maximum=MAX_ATTACHMENT_BYTES):
        raise ValueError(f"invalid attachment byte count: {name!r}")
    if not valid_sha256(record.get("sha256")):
        raise ValueError(f"invalid attachment SHA-256: {name!r}")
    media_type = record.get("mediaType")
    if media_type not in ("application/zip", "image/png"):
        raise ValueError(f"unsupported media type: {media_type!r}")

    if media_type == "application/zip":
        entries = record.get("entries")
        if not isinstance(entries, list) or len(entries) > MAX_ARCHIVE_ENTRIES:
            raise ValueError(f"invalid ZIP entry list: {name!r}")
        seen: set[str] = set()
        total = 0
        for entry_index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"invalid ZIP entry record {entry_index}: {name!r}")
            entry_name = entry.get("path")
            if not safe_entry(entry_name):
                raise ValueError(f"unsafe ZIP entry record {entry_index}: {name!r}")
            if entry_name in seen:
                raise ValueError(f"duplicate ZIP entry record: {entry_name!r}")
            seen.add(entry_name)
            if not bounded_int(
                entry.get("bytes"), minimum=0, maximum=MAX_ARCHIVE_ENTRY_BYTES
            ):
                raise ValueError(f"invalid ZIP entry byte count: {entry_name!r}")
            if not valid_sha256(entry.get("sha256")):
                raise ValueError(f"invalid ZIP entry SHA-256: {entry_name!r}")
            container = entry.get("container")
            if container is not None and not isinstance(container, dict):
                raise ValueError(f"invalid container declaration: {entry_name!r}")
            if isinstance(container, dict) and container.get("compression") == "zstd":
                if not entry_name.endswith((".blend", ".blend1")):
                    raise ValueError(f"unexpected Zstandard container: {entry_name!r}")
                if not bounded_int(
                    container.get("uncompressedBytes"),
                    minimum=1,
                    maximum=MAX_ARCHIVE_ENTRY_BYTES,
                ):
                    raise ValueError(
                        f"invalid secondary decompression byte count: {entry_name!r}"
                    )
            total += entry["bytes"]
            if total > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ValueError(f"ZIP declaration exceeds the total size limit: {name!r}")
        if declared_secondary_bytes(record) > MAX_ARCHIVE_SECONDARY_UNCOMPRESSED_BYTES:
            raise ValueError(f"ZIP declaration exceeds the secondary size limit: {name!r}")
    return record


def load_manifest(path: Path, trusted_sha256: str | None = None) -> tuple[dict, bytes]:
    payload = read_bounded_regular_file(path, MAX_MANIFEST_BYTES, "manifest")
    if trusted_sha256 is not None and hashlib.sha256(payload).hexdigest() != trusted_sha256:
        raise ValueError("trusted manifest SHA-256 mismatch")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8 JSON manifest") from exc
    if not isinstance(document, dict):
        raise ValueError("manifest root must be an object")
    tag = document.get("tag")
    if not isinstance(tag, str) or TAG_PATTERN.fullmatch(tag) is None:
        raise ValueError("invalid release tag")
    attachments = document.get("attachments")
    if (
        not isinstance(attachments, list)
        or not attachments
        or len(attachments) > MAX_ATTACHMENTS
    ):
        raise ValueError("manifest must declare a bounded, non-empty attachment list")
    seen: set[str] = set()
    secondary_total = 0
    for index, attachment in enumerate(attachments):
        validated = validate_attachment_record(attachment, index)
        name = validated["name"]
        if name in seen:
            raise ValueError(f"duplicate release attachment name: {name!r}")
        seen.add(name)
        secondary_total += declared_secondary_bytes(validated)
        if secondary_total > MAX_VERIFICATION_SECONDARY_UNCOMPRESSED_BYTES:
            raise ValueError("manifest exceeds the secondary decompression size limit")
    return document, payload


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


def verify_zstd_blend(
    stream,
    expected_compressed_bytes: object,
    container: dict,
    label: str,
    budget: VerificationBudget,
) -> None:
    executable = shutil.which("zstd")
    if executable is None:
        raise ValueError(f"Zstandard verifier unavailable: {label}")

    if (
        not isinstance(expected_compressed_bytes, int)
        or isinstance(expected_compressed_bytes, bool)
        or expected_compressed_bytes <= 0
        or expected_compressed_bytes > MAX_ATTACHMENT_BYTES
    ):
        raise ValueError(f"invalid declared compressed Blend byte count: {label}")
    expected_bytes = container.get("uncompressedBytes")
    if (
        not isinstance(expected_bytes, int)
        or isinstance(expected_bytes, bool)
        or expected_bytes <= 0
        or expected_bytes > MAX_ARCHIVE_ENTRY_BYTES
    ):
        raise ValueError(f"invalid declared Blend byte count: {label}")
    declared_header = container.get("uncompressedHeader", "")
    if not isinstance(declared_header, str):
        raise ValueError(f"invalid declared Blend header: {label}")
    declared_header_bytes = declared_header.encode("ascii", errors="strict")
    if not valid_blend_header(declared_header_bytes):
        raise ValueError(f"invalid declared Blend header: {label}")
    budget.claim_secondary_bytes(expected_bytes, label)
    deadline = budget.entry_deadline(label)

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
                [
                    executable,
                    "--quiet",
                    "--decompress",
                    "--stdout",
                    f"-M{MAX_ZSTD_MEMORY_MEBIBYTES}MB",
                    str(compressed_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise ValueError(f"Zstandard verifier unavailable: {label}") from exc

        total = 0
        actual_header = bytearray()
        selector = selectors.DefaultSelector()
        try:
            assert process.stdout is not None
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError(f"Zstandard verification timed out: {label}")
                ready = selector.select(timeout=min(1.0, remaining))
                if not ready:
                    if process.poll() is not None:
                        break
                    continue
                chunk = os.read(process.stdout.fileno(), MEBIBYTE)
                if not chunk:
                    break
                if len(actual_header) < 18:
                    actual_header.extend(chunk[: 18 - len(actual_header)])
                total += len(chunk)
                if total > expected_bytes:
                    process.kill()
                    process.wait()
                    raise ValueError(f"decompressed Blend byte-count mismatch: {label}")
            try:
                return_code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as exc:
                raise ValueError(f"Zstandard verification timed out: {label}") from exc
        finally:
            selector.close()
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


def verify_blend(
    stream,
    expected: dict,
    label: str,
    budget: VerificationBudget | None = None,
) -> None:
    if budget is None:
        budget = VerificationBudget()
    header = stream.read(18)
    container = expected.get("container", {})
    compression = container.get("compression")
    if compression == "zstd":
        if header[:4] != b"\x28\xb5\x2f\xfd":
            raise ValueError(f"invalid Zstandard Blend signature: {label}")
        stream.seek(0)
        verify_zstd_blend(stream, expected.get("bytes"), container, label, budget)
        return
    if compression is not None:
        raise ValueError(f"unsupported Blend compression: {label}")
    if not valid_blend_header(header):
        raise ValueError(f"invalid uncompressed Blend header: {label}")


@contextmanager
def open_verified_file(
    path: Path,
    expected: dict,
    directory_fd: int | None = None,
):
    label = path.name
    expected_bytes = expected.get("bytes")
    if not bounded_int(expected_bytes, minimum=0, maximum=MAX_ATTACHMENT_BYTES):
        raise ValueError(f"invalid expected byte count: {label!r}")
    expected_sha256 = expected.get("sha256")
    if not valid_sha256(expected_sha256):
        raise ValueError(f"invalid expected SHA-256: {label!r}")
    with open_bounded_regular_file(
        path,
        MAX_ATTACHMENT_BYTES,
        label,
        directory_fd,
    ) as (stream, opened):
        if opened.st_size != expected_bytes:
            raise ValueError(f"byte-count mismatch: {label!r}")
        if sha256_stream(stream, expected_bytes, label) != expected_sha256:
            raise ValueError(f"SHA-256 mismatch: {label!r}")
        stream.seek(0)
        yield stream


def verify_png(path: Path, expected: dict, directory_fd: int | None = None) -> None:
    with open_verified_file(path, expected, directory_fd) as stream:
        header = stream.read(33)
    if len(header) != 33 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"invalid PNG signature: {path.name!r}")
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


def verify_archive(
    path: Path,
    expected: dict,
    budget: VerificationBudget | None = None,
    directory_fd: int | None = None,
) -> None:
    if budget is None:
        budget = VerificationBudget()
    entries = expected.get("entries")
    if not isinstance(entries, list) or len(entries) > MAX_ARCHIVE_ENTRIES:
        raise ValueError(f"invalid ZIP entry declaration: {path.name!r}")
    expected_entries = {entry["path"]: entry for entry in entries}
    if len(expected_entries) != len(entries):
        raise ValueError(f"duplicate ZIP entry declaration: {path.name!r}")
    actual_names: set[str] = set()
    total_uncompressed = 0
    with open_verified_file(
        path,
        expected,
        directory_fd,
    ) as verified_stream, ZipFile(verified_stream) as archive:
        if len(archive.infolist()) > MAX_ARCHIVE_ENTRIES:
            raise ValueError(f"ZIP exceeds the entry-count limit: {path.name!r}")
        for info in archive.infolist():
            if not safe_entry(info.filename):
                raise ValueError(f"unsafe ZIP path: {info.filename!r}")
            mode = info.external_attr >> 16
            if info.is_dir() or stat.S_ISLNK(mode) or info.flag_bits & 0x1:
                raise ValueError(f"unsupported ZIP entry: {info.filename!r}")
            if info.filename in actual_names:
                raise ValueError(f"duplicate ZIP path: {info.filename!r}")
            actual_names.add(info.filename)
            if info.file_size > MAX_ARCHIVE_ENTRY_BYTES:
                raise ValueError(f"ZIP entry exceeds the size limit: {info.filename!r}")
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ValueError(f"ZIP exceeds the total size limit: {path.name!r}")
            if info.file_size > 0:
                if info.compress_size <= 0:
                    raise ValueError(f"invalid ZIP compression size: {info.filename!r}")
                if info.file_size / info.compress_size > MAX_ARCHIVE_COMPRESSION_RATIO:
                    raise ValueError(f"ZIP entry exceeds the compression-ratio limit: {info.filename!r}")
            record = expected_entries.get(info.filename)
            if record is None:
                raise ValueError(f"unexpected ZIP entry: {info.filename!r}")
            if info.file_size != record["bytes"]:
                raise ValueError(f"entry byte-count mismatch: {info.filename!r}")
            with archive.open(info) as stream:
                if info.filename.endswith(".glb"):
                    verify_glb(stream, info.file_size, info.filename)
                elif info.filename.endswith((".blend", ".blend1")):
                    verify_blend(stream, record, info.filename, budget)
                stream.seek(0)
                if sha256_stream(stream, info.file_size, info.filename) != record["sha256"]:
                    raise ValueError(f"entry SHA-256 mismatch: {info.filename!r}")

    if set(actual_names) != set(expected_entries):
        missing = sorted(set(expected_entries) - set(actual_names))
        raise ValueError(f"missing ZIP entries: {missing!r}")


def verify_checksum_sidecar(
    manifest_path: Path,
    attachments: list[dict],
    manifest_sha256: str | None = None,
) -> None:
    sidecar = manifest_path.with_name("SHA256SUMS.txt")
    payload = read_bounded_regular_file(
        sidecar, MAX_CHECKSUM_SIDECAR_BYTES, "release checksum sidecar"
    )
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("release checksum sidecar is not UTF-8") from exc

    expected = {attachment["name"]: attachment["sha256"] for attachment in attachments}
    if len(expected) != len(attachments):
        raise ValueError("duplicate release attachment name")
    actual: dict[str, str] = {}
    for line_number, line in enumerate(lines, 1):
        parts = line.split("  ", 1)
        if len(parts) != 2:
            raise ValueError(f"invalid release checksum line {line_number}: {sidecar.name}")
        digest, name = parts
        if (
            not valid_sha256(digest)
            or not safe_attachment_name(name)
        ):
            raise ValueError(f"invalid release checksum line {line_number}: {sidecar.name}")
        if name in actual:
            raise ValueError(f"duplicate release checksum name: {name!r}")
        actual[name] = digest

    expected_with_optional_manifest = dict(expected)
    if "manifest.json" in actual:
        expected_with_optional_manifest["manifest.json"] = (
            manifest_sha256 or sha256_path(manifest_path, MAX_MANIFEST_BYTES)
        )

    if actual != expected_with_optional_manifest:
        raise ValueError(f"release checksum sidecar mismatch: {sidecar.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--asset-dir", type=Path, required=True)
    parser.add_argument(
        "--manifest-sha256",
        help="optional trusted out-of-band SHA-256 for the manifest bytes",
    )
    args = parser.parse_args()
    if args.manifest_sha256 is not None and not valid_sha256(args.manifest_sha256):
        parser.error("--manifest-sha256 must be 64 lowercase hexadecimal characters")
    manifest, manifest_payload = load_manifest(args.manifest, args.manifest_sha256)
    budget = VerificationBudget()
    with open_pinned_directory(args.asset_dir) as asset_directory_fd:
        for attachment in manifest["attachments"]:
            path = Path(attachment["name"])
            media_type = attachment["mediaType"]
            if media_type == "application/zip":
                verify_archive(path, attachment, budget, asset_directory_fd)
            elif media_type == "image/png":
                verify_png(path, attachment, asset_directory_fd)
            else:
                raise ValueError(f"unsupported media type: {media_type!r}")
    verify_checksum_sidecar(
        args.manifest,
        manifest["attachments"],
        hashlib.sha256(manifest_payload).hexdigest(),
    )
    print(f"Verified {len(manifest['attachments'])} release attachments for {manifest['tag']}.")


if __name__ == "__main__":
    main()
