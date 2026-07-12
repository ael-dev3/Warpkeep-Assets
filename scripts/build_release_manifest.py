#!/usr/bin/env python3
"""Build the deterministic public manifest for the stone-letter release."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
from zipfile import ZipFile

TAG = "title-stone-letters-2026-07-12"
SOURCE_HEAD = "4d16e66ca973aa82e320b9e4850c5e92ff936718"
ATTACHMENTS = (
    "warpkeep-stone-letter-sources-v1.zip",
    "warpkeep-title-assemblies-v1.zip",
)


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


def archive_record(path: Path) -> dict:
    entries = []
    with ZipFile(path) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            mode = info.external_attr >> 16
            if info.is_dir() or stat.S_ISLNK(mode):
                raise ValueError(f"unsupported ZIP entry: {info.filename}")
            with archive.open(info) as stream:
                entry_hash = sha256_stream(stream)
            entries.append(
                {
                    "path": info.filename,
                    "bytes": info.file_size,
                    "sha256": entry_hash,
                }
            )
    return {
        "name": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_path(path),
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
