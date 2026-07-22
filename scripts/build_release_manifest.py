#!/usr/bin/env python3
"""Build the deterministic public manifest for the stone-letter release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import stat
from zipfile import ZipFile

from verify_release import (
    MAX_ARCHIVE_COMPRESSION_RATIO,
    MAX_ARCHIVE_ENTRIES,
    MAX_ARCHIVE_ENTRY_BYTES,
    MAX_ARCHIVE_UNCOMPRESSED_BYTES,
    MAX_ATTACHMENT_BYTES,
    open_bounded_regular_file,
    safe_entry,
    sha256_stream,
)

TAG = "title-stone-letters-2026-07-12"
SOURCE_HEAD = "4d16e66ca973aa82e320b9e4850c5e92ff936718"
ATTACHMENTS = (
    "warpkeep-stone-letter-sources-v1.zip",
    "warpkeep-title-assemblies-v1.zip",
)


def archive_record(path: Path) -> dict:
    entries = []
    names: set[str] = set()
    total_uncompressed = 0
    with open_bounded_regular_file(path, MAX_ATTACHMENT_BYTES, path.name) as (
        source,
        source_metadata,
    ):
        attachment_sha256 = sha256_stream(source, source_metadata.st_size, path.name)
        source.seek(0)
        with ZipFile(source) as archive:
            if len(archive.infolist()) > MAX_ARCHIVE_ENTRIES:
                raise ValueError(f"ZIP exceeds the entry-count limit: {path.name!r}")
            for info in sorted(archive.infolist(), key=lambda item: item.filename):
                if not safe_entry(info.filename):
                    raise ValueError(f"unsafe ZIP path: {info.filename!r}")
                mode = info.external_attr >> 16
                if info.is_dir() or stat.S_ISLNK(mode) or info.flag_bits & 0x1:
                    raise ValueError(f"unsupported ZIP entry: {info.filename!r}")
                if info.filename in names:
                    raise ValueError(f"duplicate ZIP path: {info.filename!r}")
                names.add(info.filename)
                if info.file_size > MAX_ARCHIVE_ENTRY_BYTES:
                    raise ValueError(f"ZIP entry exceeds the size limit: {info.filename!r}")
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                    raise ValueError(f"ZIP exceeds the total size limit: {path.name!r}")
                if info.file_size > 0:
                    if info.compress_size <= 0:
                        raise ValueError(f"invalid ZIP compression size: {info.filename!r}")
                    if info.file_size / info.compress_size > MAX_ARCHIVE_COMPRESSION_RATIO:
                        raise ValueError(
                            "ZIP entry exceeds the compression-ratio limit: "
                            f"{info.filename!r}"
                        )
                with archive.open(info) as stream:
                    entry_hash = sha256_stream(stream, info.file_size, info.filename)
                entries.append(
                    {
                        "path": info.filename,
                        "bytes": info.file_size,
                        "sha256": entry_hash,
                    }
                )
    return {
        "name": path.name,
        "bytes": source_metadata.st_size,
        "sha256": attachment_sha256,
        "mediaType": "application/zip",
        "url": f"https://github.com/ael-dev3/Warpkeep-Assets/releases/download/{TAG}/{path.name}",
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    document = {
        "schemaVersion": 1,
        "repository": "ael-dev3/Warpkeep-Assets",
        "tag": TAG,
        "source": {
            "repository": "ael-dev3/Warpkeep",
            "pullRequest": 19,
            "head": SOURCE_HEAD,
        },
        "license": {
            "spdx": "CC-BY-4.0",
            "effectiveBoundary": "Warpkeep v0.3.0 and later",
            "scope": "Named stone-letter title set only; copyright and related rights controlled by Warpkeep.",
        },
        "attachments": [archive_record(args.asset_dir / name) for name in ATTACHMENTS],
        "runtimeModels": [
            {
                "profile": "high",
                "filename": "warpkeep-title-high.glb",
                "bytes": 3844364,
                "sha256": "2354a57d88be80e5568afb5754102c20c9ea0fe9a83aa5ac49c0d8dd67ae9ff5",
                "uniqueTriangles": 288328,
                "renderedTriangles": 345078,
                "positionVertices": 186285,
                "textureDimensions": "20 x 1024x1024 WebP",
            },
            {
                "profile": "compact",
                "filename": "warpkeep-title-compact.glb",
                "bytes": 1714060,
                "sha256": "d29435dfa3a5fbf5103a825cc00bb3ffcef7694167a7fb7303fa89af242d7af8",
                "uniqueTriangles": 132136,
                "renderedTriangles": 158146,
                "positionVertices": 95073,
                "textureDimensions": "20 x 512x512 WebP",
            },
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
