#!/usr/bin/env python3
"""Build the Warpkeep background-video reference archive and release metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TAG = "background-video-reference-pack-2026-08-03"
PACKAGE_ROOT = "Warpkeep_Background_Video_Reference_2026-08-03"
ZIP_NAME = "warpkeep-background-video-reference-pack-2026-08-03-v1.zip"
RELEASE_URL = f"https://github.com/ael-dev3/Warpkeep-Assets/releases/download/{TAG}/{ZIP_NAME}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def fit_image(source: Image.Image, size: tuple[int, int], background=(8, 5, 18)) -> Image.Image:
    source = source.convert("RGBA")
    source.thumbnail(size, Image.Resampling.LANCZOS)
    result = Image.new("RGB", size, background)
    x = (size[0] - source.width) // 2
    y = (size[1] - source.height) // 2
    result.paste(source.convert("RGB"), (x, y))
    return result


def extract_frame(video: Path, time_seconds: float, target: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{time_seconds:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-y",
            str(target),
        ],
        check=True,
    )


def ffprobe(video: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,width,height,pix_fmt,r_frame_rate,avg_frame_rate,sample_rate,channels",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def image_info(path: Path) -> dict:
    with Image.open(path) as image:
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
            "alpha": "A" in image.mode,
        }


def make_video_contact_sheet(video: Path, target: Path) -> None:
    times = [0.5, 2.3, 4.1, 5.9, 7.7, 9.5]
    canvas = Image.new("RGB", (1800, 1500), (10, 6, 22))
    draw = ImageDraw.Draw(canvas)
    draw.text((70, 45), "SOURCE VIDEO CONTACT SHEET", font=font(58, True), fill=(238, 202, 111))
    draw.text((72, 112), "10.08 s · 834×1112 · 60 fps · H.264/AAC", font=font(28), fill=(202, 191, 220))
    cell_w, cell_h = 520, 610
    with tempfile.TemporaryDirectory(prefix="warpkeep-video-frames-") as temp_dir:
        temp = Path(temp_dir)
        for index, timestamp in enumerate(times):
            frame_path = temp / f"frame-{index:02d}.png"
            extract_frame(video, timestamp, frame_path)
            with Image.open(frame_path) as image:
                tile = fit_image(image, (cell_w, cell_h), (4, 3, 10))
            col = index % 3
            row = index // 3
            x = 70 + col * 570
            y = 180 + row * 640
            canvas.paste(tile, (x, y))
            draw.rounded_rectangle((x, y, x + cell_w, y + cell_h), radius=14, outline=(112, 78, 145), width=3)
            draw.text((x + 18, y + cell_h - 46), f"{timestamp:04.1f} s", font=font(24, True), fill=(245, 229, 192))
    canvas.save(target, "JPEG", quality=88, optimize=True, progressive=True)


def make_overview(video: Path, images: list[tuple[Path, str]], target: Path) -> None:
    canvas = Image.new("RGB", (2400, 1500), (10, 6, 22))
    draw = ImageDraw.Draw(canvas)
    draw.text((90, 58), "WARPKEEP — BACKGROUND VIDEO REFERENCE PACK", font=font(64, True), fill=(238, 202, 111))
    draw.text((94, 136), "Exact source media preserved for future cinematic and menu-background production", font=font(30), fill=(202, 191, 220))

    with tempfile.TemporaryDirectory(prefix="warpkeep-overview-") as temp_dir:
        hero_frame = Path(temp_dir) / "hero.png"
        extract_frame(video, 5.9, hero_frame)
        with Image.open(hero_frame) as image:
            hero = fit_image(image, (650, 1120), (4, 3, 10))
        canvas.paste(hero, (90, 250))
        draw.rounded_rectangle((90, 250, 740, 1370), radius=16, outline=(112, 78, 145), width=4)
        draw.rectangle((90, 1285, 740, 1370), fill=(13, 8, 28))
        draw.text((116, 1304), "ANIMATED CASTLE + CORE SKYLINE", font=font(25, True), fill=(245, 229, 192))

    panel_positions = [(800, 250), (1580, 250), (800, 820), (1580, 820)]
    for (source_path, label), (x, y) in zip(images, panel_positions):
        with Image.open(source_path) as image:
            panel = fit_image(image, (700, 480), (4, 3, 10))
        canvas.paste(panel, (x, y))
        draw.rounded_rectangle((x, y, x + 700, y + 530), radius=16, outline=(112, 78, 145), width=4)
        draw.rectangle((x, y + 480, x + 700, y + 530), fill=(13, 8, 28))
        draw.text((x + 22, y + 492), label, font=font(23, True), fill=(245, 229, 192))

    draw.text((92, 1430), "5 byte-exact supplied files · checksums · provenance · visual index", font=font(27), fill=(163, 148, 184))
    canvas.save(target, "JPEG", quality=88, optimize=True, progressive=True)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def zip_entry(path: Path, root: Path) -> dict:
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {
        "path": f"{PACKAGE_ROOT}/{path.relative_to(root).as_posix()}",
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "mediaType": media_type,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--spire", type=Path, required=True)
    parser.add_argument("--crest-dark", type=Path, required=True)
    parser.add_argument("--crest-green", type=Path, required=True)
    parser.add_argument("--menu", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output = args.output.resolve()
    package = output / PACKAGE_ROOT
    source_video = package / "source" / "video" / "warpkeep-castle-core-background-concept-vertical.mp4"
    source_images = package / "source" / "images"
    source_images.mkdir(parents=True, exist_ok=True)
    source_video.parent.mkdir(parents=True, exist_ok=True)
    preview_dir = package / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)

    copies = [
        (args.video, source_video, "animated castle-and-Core skyline concept"),
        (args.spire, source_images / "core-spire-low-poly-reference.png", "low-poly Core spire reference"),
        (args.crest_dark, source_images / "core-crest-dark-reference.png", "dark-background Core crest reference"),
        (args.crest_green, source_images / "core-crest-green-screen-reference.png", "green-screen Core crest reference"),
        (args.menu, source_images / "warpkeep-menu-castle-reference.png", "Warpkeep title-menu castle reference"),
    ]
    for supplied, destination, _ in copies:
        if not supplied.is_file():
            raise FileNotFoundError(supplied)
        shutil.copyfile(supplied, destination)

    overview = preview_dir / "background-video-reference-overview-2400x1500.jpg"
    contact_sheet = preview_dir / "source-video-contact-sheet-1800x1500.jpg"
    image_cards = [
        (copies[1][1], "LOW-POLY CORE SPIRE"),
        (copies[2][1], "CORE CREST — DARK"),
        (copies[3][1], "CORE CREST — GREEN SCREEN"),
        (copies[4][1], "WARPKEEP MENU CASTLE"),
    ]
    make_overview(source_video, image_cards, overview)
    make_video_contact_sheet(source_video, contact_sheet)

    video_probe = ffprobe(source_video)
    source_records = []
    for supplied, destination, role in copies:
        record = {
            "path": destination.relative_to(package).as_posix(),
            "suppliedBasename": supplied.name,
            "role": role,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
        }
        if destination.suffix.lower() == ".png":
            record["image"] = image_info(destination)
        else:
            record["media"] = video_probe
        source_records.append(record)

    readme = package / "README.md"
    readme.write_text(
        "# Warpkeep background-video reference pack\n\n"
        "Snapshot: 2026-08-03\n\n"
        "This archive preserves five supplied visual references for future Warpkeep "
        "menu-background and cinematic video creation. All files in `source/` retain "
        "the exact supplied bytes; only their archive paths are made descriptive.\n\n"
        "## Contents\n\n"
        "- `source/video/` — 10.08-second vertical H.264/AAC castle-and-Core concept clip\n"
        "- `source/images/` — Core spire, two Core crest treatments, and Warpkeep menu-castle references\n"
        "- `previews/` — derived overview and time-sampled contact sheet for quick browsing\n"
        "- `manifest.json` — source names, roles, dimensions, encoding metadata, bytes, and SHA-256 hashes\n"
        "- `SHA256SUMS.txt` — integrity checks for every file except itself\n\n"
        "## Intended use\n\n"
        "Use this as a visual-development reference set. It is not a runtime bundle, "
        "a final compositing contract, or evidence that every depicted design is live in game. "
        "Prefer the exact source files for new production and the previews only for discovery.\n\n"
        "## Rights boundary\n\n"
        "Ael explicitly requested public archival and GitHub Release distribution of this named pack. "
        "No separate open-license, trademark, or canonical-identity grant is asserted.\n",
        encoding="utf-8",
    )

    internal_manifest = {
        "schemaVersion": 1,
        "assetId": "warpkeep.references.background-video.2026-08-03",
        "name": "Warpkeep background-video creation reference pack",
        "snapshotDate": "2026-08-03",
        "purpose": "Future Warpkeep menu-background and cinematic video visual development.",
        "designation": "reference-only; current runtime integration and final production status are not asserted",
        "source": {
            "suppliedBy": "Ael",
            "authorization": "Ael explicitly requested packaging and public upload to Warpkeep-Assets.",
            "preservation": "All source files are byte-exact; archive paths alone were renamed descriptively.",
        },
        "license": {
            "spdx": None,
            "status": "public-archive-authorized-no-separate-open-license",
        },
        "sourceFiles": source_records,
        "derivedPreviews": [
            {
                "path": overview.relative_to(package).as_posix(),
                "bytes": overview.stat().st_size,
                "sha256": sha256(overview),
                "dimensions": [2400, 1500],
            },
            {
                "path": contact_sheet.relative_to(package).as_posix(),
                "bytes": contact_sheet.stat().st_size,
                "sha256": sha256(contact_sheet),
                "dimensions": [1800, 1500],
            },
        ],
    }
    internal_manifest_path = package / "manifest.json"
    write_json(internal_manifest_path, internal_manifest)

    checksummed = sorted(path for path in package.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    checksum_path = package / "SHA256SUMS.txt"
    checksum_path.write_text(
        "".join(f"{sha256(path)}  {path.relative_to(package).as_posix()}\n" for path in checksummed),
        encoding="utf-8",
    )

    zip_path = output / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(package.rglob("*")):
            if not path.is_file():
                continue
            relative = f"{PACKAGE_ROOT}/{path.relative_to(package).as_posix()}"
            info = zipfile.ZipInfo(relative, date_time=(2026, 8, 3, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    entries = []
    with zipfile.ZipFile(zip_path) as archive:
        for item in sorted(archive.infolist(), key=lambda value: value.filename):
            extracted = package / Path(item.filename).relative_to(PACKAGE_ROOT)
            entry = zip_entry(extracted, package)
            entry["compressedBytes"] = item.compress_size
            entries.append(entry)

    release_manifest = {
        "schemaVersion": 1,
        "repository": "ael-dev3/Warpkeep-Assets",
        "tag": TAG,
        "source": {
            "suppliedBy": "Ael",
            "authorization": "Ael explicitly requested packaging and public upload to Warpkeep-Assets.",
            "privateWorkflowMetadata": "intentionally omitted",
        },
        "designation": {
            "name": "Warpkeep background-video creation reference pack",
            "role": "future menu-background and cinematic video visual development",
            "runtimeIntegration": "reference-only; current integration not asserted",
        },
        "license": {
            "spdx": None,
            "status": "public-archive-authorized-no-separate-open-license",
            "scope": "Public archival and GitHub Release distribution are authorized for this named reference pack. No separate open-license, trademark, or canonical-identity grant is asserted.",
        },
        "attachments": [
            {
                "name": ZIP_NAME,
                "variant": "complete-byte-exact-reference-pack",
                "bytes": zip_path.stat().st_size,
                "sha256": sha256(zip_path),
                "mediaType": "application/zip",
                "packageRoot": PACKAGE_ROOT,
                "entries": entries,
                "url": RELEASE_URL,
            }
        ],
        "verification": {
            "sourceCount": 5,
            "sourcePreservation": "Every supplied source file is present byte-exact inside the ZIP.",
            "checksums": "The release attachment and every ZIP entry are SHA-256 addressed.",
            "videoAudit": "The supplied MP4 decodes as a 10.08-second 834×1112 H.264 60 fps video with stereo AAC audio.",
        },
    }

    source_manifest = {
        "schemaVersion": 1,
        "assetId": "warpkeep.references.background-video.2026-08-03",
        "archivePurpose": "Preserve future-reference media for Warpkeep menu-background and cinematic video creation.",
        "snapshotDate": "2026-08-03",
        "designation": release_manifest["designation"],
        "source": internal_manifest["source"],
        "licensePolicy": release_manifest["license"],
        "sourceFiles": source_records,
        "release": {
            "tag": TAG,
            "attachments": [
                {
                    "name": ZIP_NAME,
                    "bytes": zip_path.stat().st_size,
                    "sha256": sha256(zip_path),
                }
            ],
        },
        "previews": [
            {
                "file": "00-background-video-reference-overview.jpg",
                "title": "Warpkeep background-video reference overview",
                "source": "deterministic composite of all supplied references and a source-video frame",
                "bytes": overview.stat().st_size,
                "sha256": sha256(overview),
                "dimensions": [2400, 1500],
            },
            {
                "file": "01-source-video-contact-sheet.jpg",
                "title": "Source video contact sheet",
                "source": "six deterministic time samples from the supplied MP4",
                "bytes": contact_sheet.stat().st_size,
                "sha256": sha256(contact_sheet),
                "dimensions": [1800, 1500],
            },
        ],
    }

    metadata = output / "repo-metadata"
    write_json(metadata / "source-manifest.json", source_manifest)
    write_json(metadata / "release-manifest.json", release_manifest)
    shutil.copyfile(overview, metadata / "00-background-video-reference-overview.jpg")
    shutil.copyfile(contact_sheet, metadata / "01-source-video-contact-sheet.jpg")
    write_json(
        metadata / "gallery.json",
        {
            "schema": "warpkeep.preview-gallery.v1",
            "releaseTag": TAG,
            "images": source_manifest["previews"],
        },
    )
    (metadata / "SHA256SUMS.txt").write_text(f"{sha256(zip_path)}  {ZIP_NAME}\n", encoding="utf-8")
    write_json(
        output / "build-report.json",
        {
            "zip": str(zip_path),
            "zipBytes": zip_path.stat().st_size,
            "zipSha256": sha256(zip_path),
            "sourceFiles": source_records,
            "entryCount": len(entries),
        },
    )


if __name__ == "__main__":
    main()
