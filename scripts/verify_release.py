#!/usr/bin/env python3
"""Verify local copies of Warpkeep-Assets release attachments."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import struct
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


def verify_archive(path: Path, expected: dict) -> None:
    if path.stat().st_size != expected["bytes"]:
        raise ValueError(f"byte-count mismatch: {path.name}")
    if sha256_path(path) != expected["sha256"]:
        raise ValueError(f"SHA-256 mismatch: {path.name}")

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
                stream.seek(0)
                if sha256_stream(stream) != record["sha256"]:
                    raise ValueError(f"entry SHA-256 mismatch: {info.filename}")

    if set(actual_names) != set(expected_entries):
        missing = sorted(set(expected_entries) - set(actual_names))
        raise ValueError(f"missing ZIP entries: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--asset-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for attachment in manifest["attachments"]:
        verify_archive(args.asset_dir / attachment["name"], attachment)
    print(f"Verified {len(manifest['attachments'])} release attachments for {manifest['tag']}.")


if __name__ == "__main__":
    main()
