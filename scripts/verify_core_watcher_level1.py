#!/usr/bin/env python3
"""Structurally verify the Core Watcher Level 1 release-candidate package.

This dependency-free verifier accepts either a ZIP candidate or its extracted
package root and checks the declared Core Watcher structure, runtime contract,
GLB geometry, and nested checksums.  It is not an authenticity trust anchor.
Authenticate an exact release archive separately with the tracked
``releases/core-watcher-level1-2026-08-03/manifest.json`` and adjacent
``SHA256SUMS.txt`` by using ``scripts/verify_release.py``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import struct
import unicodedata
import zlib
from zipfile import BadZipFile, ZipFile, ZipInfo, ZIP_DEFLATED, ZIP_STORED


PACKAGE_NAME = "Warpkeep_CoreWatcher_Level1_GameReady"
RUNTIME_DIRECTORY = "Runtime/Encounters/Core/WatcherLevel1"
RUNTIME_MANIFEST = f"{RUNTIME_DIRECTORY}/runtime-manifest.json"
SOURCE_BLEND = "Source/Warpkeep_CoreWatcher_Level1_Editable.blend"
QA_REPORT = "QA/Warpkeep_CoreWatcher_Level1_RuntimeQA.json"
ASSET_MANIFEST = "asset-manifest.json"
CHECKSUMS = "SHA256SUMS.txt"
REVISION = "genesis-001-core-watcher-level1-2026-08-03"
ASSET_ID = "warpkeep.encounters.core.watcher.level1"
SOURCE_SEMANTIC_FINGERPRINT_SHA256 = (
    "a51eae5665ee3e7c59191b36dd1abfbbc1fa3ddd76405bee52c6c5fb3dad344c"
)
INTEGRATION_PROFILE_PATH = (
    Path(__file__).resolve().parents[1]
    / "contracts/core-watcher-level1-2026-08-03.integration-profile.json"
)
INTEGRATION_PROFILE_SHA256 = (
    "0a34614dfb42f754fd2524b23ef213c2db502768ad9230bd6a27a9198a8251c0"
)

RUNTIME_LOD_GUIDANCE = {
    "LOD0_High": "selected inspection and close Realm zoom",
    "LOD1_Balanced": "nearby normal-quality Realm view",
    "LOD2_Compact": "medium distance and reduced-quality selected view",
    "LOD3_Map": "far map signal and static reduced-motion presentation",
    "suggestedDistancesMeters": {
        "LOD0_HighThrough": 8,
        "LOD1_BalancedThrough": 18,
        "LOD2_CompactThrough": 36,
        "LOD3_MapThrough": 72,
    },
}
RUNTIME_MOTION_CONTRACT = {
    "animations": [],
    "continuousMotionRequired": False,
    "forbiddenClips": ["Attack", "Walk", "Death"],
    "mode": "bounded-runtime-rigid-hierarchy",
    "reducedMotion": "static",
    "skins": 0,
}
RUNTIME_SELECTION_GUIDANCE = {
    "presentationFootprintRadiusMeters": 0.9,
    "renderGeometryIsAuthoritativeCollision": False,
    "suggestedPickCylinderHeightMeters": 2.55,
    "suggestedPickCylinderRadiusMeters": 0.72,
}
RUNTIME_DESIGN_INTENT = {
    "camera": "three-quarter isometric 4X world map and selected encounter record",
    "excluded": (
        "human face, legs, weapon, gun, wings, banner, heraldry, spaceship, "
        "modern robot"
    ),
    "identity": (
        "ancient fantasy-machine infrastructure expressed through obsidian and cold "
        "ultraviolet"
    ),
    "silhouette": "tall bifurcated monolith, suspended core, asymmetric floating shards",
}
RUNTIME_AUTHORING_CONTRACT = {
    "animations": [],
    "front": "+Z glTF / -Y Blender",
    "lods": ["LOD0_High", "LOD1_Balanced", "LOD2_Compact", "LOD3_Map"],
    "metersPerUnit": 1.0,
    "motion": "optional bounded runtime rigid hierarchy; static under reduced motion",
    "selfContained": True,
    "textures": 0,
}

LOD_CONTRACT = (
    (
        "LOD0_High",
        "Warpkeep_CoreWatcher_Level1_LOD0_High_Runtime.glb",
        3500,
        180224,
    ),
    (
        "LOD1_Balanced",
        "Warpkeep_CoreWatcher_Level1_LOD1_Balanced_Runtime.glb",
        2200,
        102400,
    ),
    (
        "LOD2_Compact",
        "Warpkeep_CoreWatcher_Level1_LOD2_Compact_Runtime.glb",
        1100,
        61440,
    ),
    (
        "LOD3_Map",
        "Warpkeep_CoreWatcher_Level1_LOD3_Map_Runtime.glb",
        600,
        35840,
    ),
)

PREVIEW_DIMENSIONS = {
    "Previews/Warpkeep_CoreWatcher_Level1_LOD_Lineup_2400.jpg": (2400, 1200),
    "Previews/Warpkeep_CoreWatcher_Level1_Presentation_1920.jpg": (1920, 1080),
    "Previews/Warpkeep_CoreWatcher_Level1_Transparent_1600.png": (1600, 1600),
    "Previews/Mobile/Warpkeep_CoreWatcher_Level1_Map_512.png": (512, 512),
}

EXPECTED_FILES = frozenset(
    {
        "PACKAGE-NOTICE.md",
        "README.md",
        CHECKSUMS,
        ASSET_MANIFEST,
        SOURCE_BLEND,
        QA_REPORT,
        RUNTIME_MANIFEST,
        *PREVIEW_DIMENSIONS,
        *(f"{RUNTIME_DIRECTORY}/{filename}" for _, filename, _, _ in LOD_CONTRACT),
    }
)

EXPECTED_MATERIALS = frozenset(
    {
        "WK_Core_Obsidian",
        "WK_Core_BlackenedMetal",
        "WK_Core_Ultraviolet",
    }
)
ALLOWED_EXTENSIONS = frozenset({"KHR_materials_emissive_strength"})
AUTHORITY_BOUNDARY = {
    "ai": False,
    "collision": False,
    "combat": False,
    "damage": False,
    "health": False,
    "ownership": False,
    "picking": False,
    "placement": False,
    "respawn": False,
    "rewards": False,
    "routing": False,
    "spacetimeDb": False,
    "visualOnly": True,
}

LOD_QA_CHECK_SUFFIXES = (
    "GLB 2.0 header and chunk integrity",
    "triangle ceiling",
    "byte ceiling",
    "one scene",
    "finite bounded geometry",
    "self-contained embedded buffer",
    "texture-free opaque runtime",
    "static rigid runtime",
    "no cameras or unsupported extensions",
    "ground contact",
    "map footprint bound",
    "stable height",
)
EXPECTED_QA_CHECKS = (
    "exact four runtime LODs",
    "strict triangle reduction",
    "strict byte reduction",
    *(
        f"{tier} {suffix}"
        for tier, _, _, _ in LOD_CONTRACT
        for suffix in LOD_QA_CHECK_SUFFIXES
    ),
    "one closed enemy kind",
    "exact Level 1 classification",
    "combat disabled",
    "zero gameplay authority",
    "no Hegemony heraldry or textures",
    "source semantic fingerprint pinned",
    "required previews written",
)
if len(EXPECTED_QA_CHECKS) != 58 or len(set(EXPECTED_QA_CHECKS)) != 58:
    raise RuntimeError("internal Core Watcher QA check contract is invalid")

FORBIDDEN_PNG_CHUNKS = frozenset({b"eXIf", b"tEXt", b"zTXt", b"iTXt", b"tIME"})
FORBIDDEN_JPEG_MARKERS = {
    0xFE: "COM",
    0xE1: "APP1",
    0xE2: "APP2",
    0xED: "APP13",
}

MEBIBYTE = 1024 * 1024
MAX_ARCHIVE_BYTES = 32 * MEBIBYTE
MAX_TOTAL_BYTES = 48 * MEBIBYTE
MAX_ENTRY_BYTES = 16 * MEBIBYTE
MAX_TEXT_BYTES = 2 * MEBIBYTE
MAX_COMPRESSION_RATIO = 200
MAX_ARCHIVE_ENTRIES = 64
MAX_AUTHORING_BOUND_MARGIN_METERS = 0.08
BOUND_TOLERANCE_METERS = 1e-5
NORMAL_LENGTH_TOLERANCE = 1e-4
QUATERNION_LENGTH_TOLERANCE = 1e-5
SHA256_RE = re.compile(r"[0-9a-f]{64}")
CHECKSUM_LINE_RE = re.compile(r"([0-9a-f]{64})  ([^\r\n]+)")

PRIVATE_PATTERNS = (
    ("macOS private home path", re.compile(rb"/Users/", re.IGNORECASE)),
    ("Unix private home path", re.compile(rb"/home/", re.IGNORECASE)),
    (
        "macOS temporary build path",
        re.compile(rb"/(?:private/)?var/folders/", re.IGNORECASE),
    ),
    ("Unix temporary build path", re.compile(rb"/(?:var/)?tmp/", re.IGNORECASE)),
    ("Windows private home path", re.compile(rb"[A-Za-z]:\\\\Users\\\\", re.IGNORECASE)),
    (
        "Windows temporary build path",
        re.compile(rb"\\\\AppData\\\\Local\\\\Temp\\\\", re.IGNORECASE),
    ),
)
CREDENTIAL_PATTERNS = (
    ("GitHub credential", re.compile(rb"github_pat_[A-Za-z0-9_]{10,}")),
    ("GitHub credential", re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("OpenAI credential", re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{16,}")),
    ("AWS credential", re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}")),
    ("Slack credential", re.compile(rb"xox[baprs]-[A-Za-z0-9-]{10,}")),
    (
        "private key",
        re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
)

COMPONENTS = {
    5120: (1, "b"),
    5121: (1, "B"),
    5122: (2, "h"),
    5123: (2, "H"),
    5125: (4, "I"),
    5126: (4, "f"),
}
TYPE_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


@dataclass(frozen=True)
class RuntimeMaterial:
    name: str
    alpha_mode: str
    opaque: bool
    double_sided: bool
    base_color_factor: tuple[float, float, float, float]
    metallic: float
    roughness: float
    emissive_factor: tuple[float, float, float]
    emissive_strength: float


@dataclass(frozen=True)
class GlbSemanticContract:
    tier: str
    profile_id: str
    root_node: str
    part_nodes: tuple[str, ...]


@dataclass(frozen=True)
class GlbSemanticEvidence:
    root_node: str
    part_nodes: tuple[str, ...]
    semantic_roles: tuple[tuple[str, str], ...]
    material_assignments: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class GlbMetrics:
    bytes: int
    sha256: str
    triangles: int
    uploaded_vertices: int
    embedded_buffer_bytes: int
    scenes: int
    nodes: int
    meshes: int
    primitives: int
    materials: int
    images: int
    textures: int
    samplers: int
    cameras: int
    skins: int
    animations: int
    extensions_used: tuple[str, ...]
    runtime_materials: tuple[RuntimeMaterial, ...]
    bounds_gltf_min: tuple[float, float, float]
    bounds_gltf_max: tuple[float, float, float]
    bounds_gltf_size: tuple[float, float, float]
    footprint_radius: float
    semantic: GlbSemanticEvidence


@dataclass(frozen=True)
class VerificationResult:
    source: Path
    files: int
    lods: int
    triangles: tuple[int, ...]
    bytes: tuple[int, ...]


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def load_json(payload: bytes, label: str) -> dict:
    if len(payload) > MAX_TEXT_BYTES:
        raise ValueError(f"JSON file exceeds size limit: {label}")
    try:
        document = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid UTF-8 JSON: {label}") from exc
    if not isinstance(document, dict):
        raise ValueError(f"JSON root must be an object: {label}")

    def require_finite(value: object) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"non-finite JSON number: {label}")
        if isinstance(value, dict):
            for child in value.values():
                require_finite(child)
        elif isinstance(value, list):
            for child in value:
                require_finite(child)

    require_finite(document)
    return document


def safe_relative_path(name: str) -> bool:
    if not isinstance(name, str) or not name or not name.isprintable():
        return False
    posix = PurePosixPath(name)
    windows = PureWindowsPath(name)
    return (
        not name.startswith("/")
        and "\\" not in name
        and not windows.drive
        and all(part not in ("", ".", "..") for part in posix.parts)
        and posix.as_posix() == name
        and unicodedata.normalize("NFC", name) == name
    )


def _scan_public_bytes(payload: bytes, label: str) -> None:
    for description, pattern in (*PRIVATE_PATTERNS, *CREDENTIAL_PATTERNS):
        if pattern.search(payload) is not None:
            raise ValueError(f"{description} found in package file: {label}")


def _zip_mode(info: ZipInfo) -> int:
    return (info.external_attr >> 16) & 0xFFFF


def _read_zip(path: Path) -> dict[str, bytes]:
    try:
        linked = path.lstat()
    except OSError as exc:
        raise ValueError(f"unable to inspect ZIP: {path}") from exc
    if stat.S_ISLNK(linked.st_mode) or not stat.S_ISREG(linked.st_mode):
        raise ValueError("package ZIP must be a regular, non-symlink file")
    if linked.st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("package ZIP exceeds size limit")

    files: dict[str, bytes] = {}
    seen_archive_names: set[str] = set()
    total = 0
    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ARCHIVE_ENTRIES:
                raise ValueError("ZIP exceeds entry-count limit")
            for info in infos:
                name = info.filename
                if name in seen_archive_names:
                    raise ValueError(f"duplicate ZIP entry: {name!r}")
                seen_archive_names.add(name)
                if not safe_relative_path(name):
                    raise ValueError(f"unsafe ZIP path: {name!r}")
                if info.is_dir() or name.endswith("/"):
                    raise ValueError(f"directory entries are not allowed: {name!r}")
                if info.flag_bits & 0x1:
                    raise ValueError(f"encrypted ZIP entry is not allowed: {name!r}")
                if info.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
                    raise ValueError(f"unsupported ZIP compression: {name!r}")
                mode = _zip_mode(info)
                if stat.S_ISLNK(mode):
                    raise ValueError(f"symlink ZIP entry is not allowed: {name!r}")
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                    raise ValueError(f"special-file ZIP entry is not allowed: {name!r}")
                if mode & 0o111:
                    raise ValueError(f"executable ZIP entry is not allowed: {name!r}")
                if info.file_size > MAX_ENTRY_BYTES:
                    raise ValueError(f"ZIP entry exceeds size limit: {name!r}")
                if info.file_size and info.compress_size == 0:
                    raise ValueError(f"invalid ZIP compression size: {name!r}")
                if (
                    info.compress_size
                    and info.file_size > info.compress_size * MAX_COMPRESSION_RATIO
                ):
                    raise ValueError(f"ZIP entry exceeds compression-ratio limit: {name!r}")
                total += info.file_size
                if total > MAX_TOTAL_BYTES:
                    raise ValueError("ZIP exceeds total uncompressed size limit")
                with archive.open(info) as stream:
                    payload = stream.read(info.file_size + 1)
                if len(payload) != info.file_size:
                    raise ValueError(f"ZIP entry byte-count mismatch: {name!r}")
                prefix = f"{PACKAGE_NAME}/"
                if not name.startswith(prefix):
                    raise ValueError(f"unexpected ZIP package root: {name!r}")
                relative = name[len(prefix) :]
                if not relative or relative in files:
                    raise ValueError(f"duplicate or empty package path: {name!r}")
                files[relative] = payload
    except BadZipFile as exc:
        raise ValueError("invalid package ZIP") from exc
    return files


def _read_directory(root: Path) -> dict[str, bytes]:
    try:
        linked = root.lstat()
    except OSError as exc:
        raise ValueError(f"unable to inspect package root: {root}") from exc
    if root.name != PACKAGE_NAME:
        raise ValueError(f"unexpected extracted package root: {root.name!r}")
    if stat.S_ISLNK(linked.st_mode) or not stat.S_ISDIR(linked.st_mode):
        raise ValueError("package root must be a real directory")

    files: dict[str, bytes] = {}
    total = 0
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in directory_names:
            child = current_path / name
            mode = child.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise ValueError(f"non-directory or symlink in package: {child}")
        for name in file_names:
            child = current_path / name
            mode = child.lstat().st_mode
            relative = child.relative_to(root).as_posix()
            if not safe_relative_path(relative):
                raise ValueError(f"unsafe package path: {relative!r}")
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise ValueError(f"package entry must be a regular file: {relative!r}")
            if mode & 0o111:
                raise ValueError(f"executable package entry is not allowed: {relative!r}")
            size = os.stat(child, follow_symlinks=False).st_size
            if size > MAX_ENTRY_BYTES:
                raise ValueError(f"package entry exceeds size limit: {relative!r}")
            total += size
            if total > MAX_TOTAL_BYTES:
                raise ValueError("package exceeds total size limit")
            payload = child.read_bytes()
            if len(payload) != size:
                raise ValueError(f"package entry changed while reading: {relative!r}")
            files[relative] = payload
    return files


def read_package(path: Path) -> dict[str, bytes]:
    if path.suffix.casefold() == ".zip":
        files = _read_zip(path)
    elif path.is_dir():
        files = _read_directory(path)
    else:
        raise ValueError("package input must be a ZIP or extracted package root")
    actual = frozenset(files)
    if actual != EXPECTED_FILES:
        missing = sorted(EXPECTED_FILES - actual)
        unexpected = sorted(actual - EXPECTED_FILES)
        raise ValueError(
            f"package file set mismatch; missing={missing!r}, unexpected={unexpected!r}"
        )
    for name, payload in files.items():
        _scan_public_bytes(payload, name)
    return files


def verify_checksums(files: dict[str, bytes]) -> None:
    payload = files[CHECKSUMS]
    if len(payload) > MAX_TEXT_BYTES:
        raise ValueError("nested checksum file exceeds size limit")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("nested checksum file is not UTF-8") from exc
    if not text.endswith("\n") or "\r" in text:
        raise ValueError("nested checksum file must use newline-terminated LF records")

    declared: dict[str, str] = {}
    for line in text.splitlines():
        match = CHECKSUM_LINE_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"invalid nested checksum record: {line!r}")
        digest, name = match.groups()
        if not safe_relative_path(name):
            raise ValueError(f"unsafe nested checksum path: {name!r}")
        if name in declared:
            raise ValueError(f"duplicate nested checksum path: {name!r}")
        declared[name] = digest

    expected_names = EXPECTED_FILES - {CHECKSUMS}
    if frozenset(declared) != expected_names:
        raise ValueError("nested checksum coverage does not exactly match package files")
    for name, expected in declared.items():
        actual = hashlib.sha256(files[name]).hexdigest()
        if actual != expected:
            raise ValueError(f"nested checksum mismatch: {name}")


def _require_list(document: dict, key: str, label: str) -> list:
    value = document.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array: {label}")
    return value


def _index(value: object, count: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < count:
        raise ValueError(f"out-of-range {label}")
    return value


def _nonnegative_int(value: object, label: str, *, positive: bool = False) -> int:
    minimum = 1 if positive else 0
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < minimum
    ):
        raise ValueError(f"invalid {label}")
    return value


def _walk_extensions(value: object, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "extensions":
                if not isinstance(child, dict):
                    raise ValueError("GLB extensions value must be an object")
                for extension_name in child:
                    if extension_name not in ALLOWED_EXTENSIONS:
                        raise ValueError(f"unsupported GLB extension: {extension_name}")
                    found.add(extension_name)
            _walk_extensions(child, found)
    elif isinstance(value, list):
        for child in value:
            _walk_extensions(child, found)
    elif isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite GLB JSON number")


def _parse_glb(payload: bytes, label: str) -> tuple[dict, bytes]:
    if len(payload) < 20:
        raise ValueError(f"truncated GLB: {label}")
    magic, version, declared_length = struct.unpack_from("<4sII", payload, 0)
    if magic != b"glTF" or version != 2 or declared_length != len(payload):
        raise ValueError(f"invalid GLB 2.0 header: {label}")

    chunks: list[tuple[int, bytes]] = []
    offset = 12
    while offset < len(payload):
        if offset + 8 > len(payload):
            raise ValueError(f"truncated GLB chunk header: {label}")
        length, chunk_type = struct.unpack_from("<II", payload, offset)
        offset += 8
        if length % 4:
            raise ValueError(f"unaligned GLB chunk: {label}")
        end = offset + length
        if end > len(payload):
            raise ValueError(f"truncated GLB chunk payload: {label}")
        chunks.append((chunk_type, payload[offset:end]))
        offset = end
    if offset != len(payload) or len(chunks) != 2:
        raise ValueError(f"GLB must contain exactly JSON and BIN chunks: {label}")
    if chunks[0][0] != 0x4E4F534A or chunks[1][0] != 0x004E4942:
        raise ValueError(f"invalid GLB chunk order or type: {label}")

    json_chunk = chunks[0][1]
    stripped = json_chunk.rstrip(b" ")
    if not stripped or any(byte != 0x20 for byte in json_chunk[len(stripped) :]):
        raise ValueError(f"invalid GLB JSON padding: {label}")
    document = load_json(stripped, f"{label} JSON chunk")
    return document, chunks[1][1]


def _decode_accessor(
    accessor_index: int,
    accessors: list,
    buffer_views: list,
    binary: bytes,
    label: str,
) -> tuple[dict, list[tuple[int | float, ...]]]:
    accessor = accessors[accessor_index]
    if not isinstance(accessor, dict):
        raise ValueError(f"accessor must be an object: {label}")
    if "sparse" in accessor:
        raise ValueError(f"sparse accessors are not allowed: {label}")
    view_index = _index(accessor.get("bufferView"), len(buffer_views), f"bufferView: {label}")
    view = buffer_views[view_index]
    component_type = accessor.get("componentType")
    accessor_type = accessor.get("type")
    if component_type not in COMPONENTS or accessor_type not in TYPE_COMPONENTS:
        raise ValueError(f"unsupported accessor encoding: {label}")
    component_bytes, format_character = COMPONENTS[component_type]
    components = TYPE_COMPONENTS[accessor_type]
    element_bytes = component_bytes * components
    count = _nonnegative_int(accessor.get("count"), f"accessor count: {label}", positive=True)
    normalized = accessor.get("normalized", False)
    if not isinstance(normalized, bool) or (
        normalized and component_type not in (5120, 5121, 5122, 5123)
    ):
        raise ValueError(f"invalid accessor normalization: {label}")
    accessor_offset = _nonnegative_int(accessor.get("byteOffset", 0), f"accessor offset: {label}")
    view_offset = _nonnegative_int(view.get("byteOffset", 0), f"bufferView offset: {label}")
    view_length = _nonnegative_int(
        view.get("byteLength"), f"bufferView length: {label}", positive=True
    )
    stride = view.get("byteStride", element_bytes)
    if (
        not isinstance(stride, int)
        or isinstance(stride, bool)
        or stride < element_bytes
        or ("byteStride" in view and (stride < 4 or stride > 252 or stride % 4))
    ):
        raise ValueError(f"invalid accessor stride: {label}")
    absolute_offset = view_offset + accessor_offset
    if absolute_offset % component_bytes:
        raise ValueError(f"misaligned accessor: {label}")
    required = accessor_offset + (count - 1) * stride + element_bytes
    if required > view_length or view_offset + view_length > len(binary):
        raise ValueError(f"accessor exceeds its bufferView: {label}")

    unpacker = struct.Struct("<" + format_character * components)
    values = [
        unpacker.unpack_from(binary, absolute_offset + item * stride)
        for item in range(count)
    ]
    if component_type == 5126 and any(
        not math.isfinite(float(component)) for value in values for component in value
    ):
        raise ValueError(f"non-finite accessor value: {label}")
    return accessor, values


def _validate_declared_bounds(accessor: dict, values: list[tuple], label: str) -> None:
    for key, operation in (("min", min), ("max", max)):
        if key not in accessor:
            continue
        declared = accessor[key]
        components = len(values[0])
        if not isinstance(declared, list) or len(declared) != components:
            raise ValueError(f"invalid accessor {key}: {label}")
        for component in range(components):
            actual = operation(value[component] for value in values)
            expected = declared[component]
            if not isinstance(expected, (int, float)) or isinstance(expected, bool):
                raise ValueError(f"invalid accessor {key}: {label}")
            tolerance = max(1e-6, abs(float(actual)) * 1e-6)
            if not math.isclose(float(expected), float(actual), abs_tol=tolerance, rel_tol=1e-6):
                raise ValueError(f"incorrect accessor {key}: {label}")


def _finite_number(
    value: object,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"invalid finite number: {label}")
    number = float(value)
    if minimum is not None and number < minimum:
        raise ValueError(f"number below minimum: {label}")
    if maximum is not None and number > maximum:
        raise ValueError(f"number above maximum: {label}")
    return number


def _finite_vector(
    value: object,
    length: int,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"invalid vector: {label}")
    return tuple(
        _finite_number(component, label, minimum=minimum, maximum=maximum)
        for component in value
    )


Matrix4 = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]
IDENTITY_MATRIX: Matrix4 = (
    (1.0, 0.0, 0.0, 0.0),
    (0.0, 1.0, 0.0, 0.0),
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, 0.0, 1.0),
)


def _matrix_multiply(left: Matrix4, right: Matrix4) -> Matrix4:
    return tuple(
        tuple(
            sum(left[row][item] * right[item][column] for item in range(4))
            for column in range(4)
        )
        for row in range(4)
    )  # type: ignore[return-value]


def _transform_point(matrix: Matrix4, point: tuple) -> tuple[float, float, float]:
    homogeneous = tuple(float(component) for component in point) + (1.0,)
    result = tuple(
        sum(matrix[row][column] * homogeneous[column] for column in range(4))
        for row in range(4)
    )
    if not math.isclose(result[3], 1.0, rel_tol=0.0, abs_tol=1e-7):
        raise ValueError("node transform produced a non-affine geometry point")
    return result[0], result[1], result[2]


def _node_transform_matrix(node: dict, label: str) -> Matrix4:
    if "matrix" in node:
        values = _finite_vector(node["matrix"], 16, f"node matrix: {label}")
        matrix: Matrix4 = tuple(
            tuple(values[column * 4 + row] for column in range(4))
            for row in range(4)
        )  # type: ignore[assignment]
        if any(
            not math.isclose(matrix[3][column], expected, rel_tol=0.0, abs_tol=1e-7)
            for column, expected in enumerate((0.0, 0.0, 0.0, 1.0))
        ):
            raise ValueError(f"node matrix must be affine: {label}")
        return matrix

    translation = _finite_vector(
        node.get("translation", [0.0, 0.0, 0.0]), 3, f"node translation: {label}"
    )
    rotation = _finite_vector(
        node.get("rotation", [0.0, 0.0, 0.0, 1.0]), 4, f"node rotation: {label}"
    )
    scale = _finite_vector(
        node.get("scale", [1.0, 1.0, 1.0]), 3, f"node scale: {label}"
    )
    quaternion_length = math.sqrt(sum(component * component for component in rotation))
    if not math.isclose(
        quaternion_length,
        1.0,
        rel_tol=QUATERNION_LENGTH_TOLERANCE,
        abs_tol=QUATERNION_LENGTH_TOLERANCE,
    ):
        raise ValueError(f"node rotation quaternion is not normalized: {label}")
    if any(abs(component) <= 1e-8 for component in scale):
        raise ValueError(f"node scale collapses geometry: {label}")

    x, y, z, w = rotation
    sx, sy, sz = scale
    return (
        (
            (1.0 - 2.0 * (y * y + z * z)) * sx,
            (2.0 * (x * y - z * w)) * sy,
            (2.0 * (x * z + y * w)) * sz,
            translation[0],
        ),
        (
            (2.0 * (x * y + z * w)) * sx,
            (1.0 - 2.0 * (x * x + z * z)) * sy,
            (2.0 * (y * z - x * w)) * sz,
            translation[1],
        ),
        (
            (2.0 * (x * z - y * w)) * sx,
            (2.0 * (y * z + x * w)) * sy,
            (1.0 - 2.0 * (x * x + y * y)) * sz,
            translation[2],
        ),
        (0.0, 0.0, 0.0, 1.0),
    )


def _glb_runtime_material(material: dict, label: str) -> RuntimeMaterial:
    alpha_mode = material.get("alphaMode", "OPAQUE")
    if alpha_mode not in ("OPAQUE", "MASK", "BLEND"):
        raise ValueError(f"invalid material alphaMode: {label}")
    double_sided = material.get("doubleSided", False)
    if not isinstance(double_sided, bool):
        raise ValueError(f"invalid material doubleSided: {label}")
    pbr = material.get("pbrMetallicRoughness", {})
    if not isinstance(pbr, dict):
        raise ValueError(f"invalid pbrMetallicRoughness: {label}")
    if "baseColorTexture" in pbr or "metallicRoughnessTexture" in pbr:
        raise ValueError(f"texture reference is not allowed in runtime material: {label}")
    if any(
        key in material for key in ("normalTexture", "occlusionTexture", "emissiveTexture")
    ):
        raise ValueError(f"texture reference is not allowed in runtime material: {label}")
    base_color = _finite_vector(
        pbr.get("baseColorFactor", [1.0, 1.0, 1.0, 1.0]),
        4,
        f"baseColorFactor: {label}",
        minimum=0.0,
        maximum=1.0,
    )
    emissive_factor = _finite_vector(
        material.get("emissiveFactor", [0.0, 0.0, 0.0]),
        3,
        f"emissiveFactor: {label}",
        minimum=0.0,
        maximum=1.0,
    )
    extensions = material.get("extensions", {})
    if not isinstance(extensions, dict):
        raise ValueError(f"invalid material extensions: {label}")
    emissive_extension = extensions.get("KHR_materials_emissive_strength")
    if emissive_extension is None:
        # A zero factor has zero effective emission; otherwise glTF's strength
        # default is 1.0 when the extension is absent.
        emissive_strength = 0.0 if all(value == 0.0 for value in emissive_factor) else 1.0
    else:
        if not isinstance(emissive_extension, dict):
            raise ValueError(f"invalid emissive-strength extension: {label}")
        emissive_strength = _finite_number(
            emissive_extension.get("emissiveStrength", 1.0),
            f"emissiveStrength: {label}",
            minimum=0.0,
        )
    return RuntimeMaterial(
        name=material["name"],
        alpha_mode=alpha_mode,
        opaque=alpha_mode == "OPAQUE",
        double_sided=double_sided,
        base_color_factor=base_color,
        metallic=_finite_number(
            pbr.get("metallicFactor", 1.0),
            f"metallicFactor: {label}",
            minimum=0.0,
            maximum=1.0,
        ),
        roughness=_finite_number(
            pbr.get("roughnessFactor", 1.0),
            f"roughnessFactor: {label}",
            minimum=0.0,
            maximum=1.0,
        ),
        emissive_factor=emissive_factor,
        emissive_strength=emissive_strength,
    )


def inspect_glb(
    payload: bytes,
    label: str = "runtime GLB",
    semantic_contract: GlbSemanticContract | None = None,
) -> GlbMetrics:
    document, binary = _parse_glb(payload, label)
    asset = document.get("asset")
    if not isinstance(asset, dict) or asset.get("version") != "2.0":
        raise ValueError(f"GLB asset.version must be 2.0: {label}")

    extensions_used = _require_list(document, "extensionsUsed", label)
    extensions_required = _require_list(document, "extensionsRequired", label)
    if (
        any(not isinstance(item, str) for item in extensions_used + extensions_required)
        or len(set(extensions_used)) != len(extensions_used)
        or len(set(extensions_required)) != len(extensions_required)
        or not set(extensions_used).issubset(ALLOWED_EXTENSIONS)
        or not set(extensions_required).issubset(ALLOWED_EXTENSIONS)
        or not set(extensions_required).issubset(set(extensions_used))
    ):
        raise ValueError(f"unsupported or invalid GLB extension declaration: {label}")
    found_extensions: set[str] = set()
    _walk_extensions(document, found_extensions)
    if found_extensions != set(extensions_used):
        raise ValueError(f"GLB extension declarations do not match their use: {label}")

    forbidden_arrays = ("images", "textures", "samplers", "cameras", "skins", "animations")
    for key in forbidden_arrays:
        if _require_list(document, key, label):
            raise ValueError(f"GLB must not contain {key}: {label}")

    def reject_uri(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "uri":
                    raise ValueError(f"external or embedded URI is not allowed: {label}")
                reject_uri(child)
        elif isinstance(value, list):
            for child in value:
                reject_uri(child)

    reject_uri(document)

    buffers = _require_list(document, "buffers", label)
    if len(buffers) != 1 or not isinstance(buffers[0], dict):
        raise ValueError(f"GLB must contain exactly one embedded buffer: {label}")
    embedded_bytes = _nonnegative_int(
        buffers[0].get("byteLength"), f"embedded buffer byteLength: {label}", positive=True
    )
    if embedded_bytes > len(binary) or len(binary) - embedded_bytes > 3:
        raise ValueError(f"GLB BIN chunk length mismatch: {label}")
    if any(binary[embedded_bytes:]):
        raise ValueError(f"non-zero GLB BIN padding: {label}")

    buffer_views = _require_list(document, "bufferViews", label)
    accessors = _require_list(document, "accessors", label)
    if not buffer_views or not accessors:
        raise ValueError(f"GLB geometry tables must be non-empty: {label}")
    for index, view in enumerate(buffer_views):
        if not isinstance(view, dict):
            raise ValueError(f"invalid bufferView buffer: {label} #{index}")
        _index(view.get("buffer"), 1, f"bufferView buffer: {label} #{index}")
        offset = _nonnegative_int(view.get("byteOffset", 0), f"bufferView offset: {label}")
        length = _nonnegative_int(
            view.get("byteLength"), f"bufferView length: {label}", positive=True
        )
        if offset + length > embedded_bytes:
            raise ValueError(f"bufferView exceeds embedded buffer: {label} #{index}")
        if "target" in view and view["target"] not in (34962, 34963):
            raise ValueError(f"invalid bufferView target: {label} #{index}")

    decoded: dict[int, tuple[dict, list[tuple]]] = {}

    def decode(index: int) -> tuple[dict, list[tuple]]:
        if index not in decoded:
            decoded[index] = _decode_accessor(index, accessors, buffer_views, binary, label)
            _validate_declared_bounds(*decoded[index], f"{label} accessor {index}")
        return decoded[index]

    materials = _require_list(document, "materials", label)
    names: list[str] = []
    runtime_materials: list[RuntimeMaterial] = []
    for index, material in enumerate(materials):
        if not isinstance(material, dict) or not isinstance(material.get("name"), str):
            raise ValueError(f"invalid material record: {label} #{index}")
        if material.get("alphaMode", "OPAQUE") != "OPAQUE":
            raise ValueError(f"non-opaque material is not allowed: {label} #{index}")
        names.append(material["name"])
        runtime_materials.append(_glb_runtime_material(material, f"{label} #{index}"))
    if len(names) != 3 or frozenset(names) != EXPECTED_MATERIALS:
        raise ValueError(f"Core Watcher material names do not match contract: {label}")

    meshes = _require_list(document, "meshes", label)
    nodes = _require_list(document, "nodes", label)
    scenes = _require_list(document, "scenes", label)
    if (
        not meshes
        or not nodes
        or len(scenes) != 1
        or not _strict_json_equal(document.get("scene"), 0)
    ):
        raise ValueError(f"GLB must have one populated default scene: {label}")

    primitive_count = 0
    triangle_count = 0
    uploaded_vertices = 0
    mesh_positions: list[list[tuple]] = [[] for _ in meshes]
    for mesh_index, mesh in enumerate(meshes):
        if not isinstance(mesh, dict) or not isinstance(mesh.get("primitives"), list):
            raise ValueError(f"invalid mesh: {label} #{mesh_index}")
        if len(mesh["primitives"]) != 1 or "weights" in mesh:
            raise ValueError(
                f"every GLB mesh must contain exactly one primitive: {label} #{mesh_index}"
            )
        for primitive_index, primitive in enumerate(mesh["primitives"]):
            primitive_label = f"{label} mesh {mesh_index} primitive {primitive_index}"
            if not isinstance(primitive, dict) or primitive.get("mode", 4) != 4:
                raise ValueError(f"only triangle primitives are allowed: {primitive_label}")
            if "targets" in primitive:
                raise ValueError(f"morph targets are not allowed: {primitive_label}")
            attributes = primitive.get("attributes")
            if not isinstance(attributes, dict) or "POSITION" not in attributes:
                raise ValueError(f"primitive requires POSITION: {primitive_label}")
            if set(attributes) != {"POSITION", "NORMAL"}:
                raise ValueError(
                    f"primitive attributes must be exactly POSITION and NORMAL: {primitive_label}"
                )
            material_index = _index(
                primitive.get("material"), len(materials), f"material: {primitive_label}"
            )
            del material_index

            attribute_count: int | None = None
            position_count = 0
            position_values: list[tuple] = []
            for semantic, accessor_reference in attributes.items():
                accessor_index = _index(
                    accessor_reference, len(accessors), f"attribute accessor: {primitive_label}"
                )
                accessor, values = decode(accessor_index)
                accessor_view = buffer_views[accessor["bufferView"]]
                if accessor_view.get("target") != 34962:
                    raise ValueError(f"vertex accessor must target ARRAY_BUFFER: {primitive_label}")
                if attribute_count is None:
                    attribute_count = len(values)
                elif len(values) != attribute_count:
                    raise ValueError(f"vertex attribute count mismatch: {primitive_label}")
                if semantic == "POSITION":
                    if accessor.get("componentType") != 5126 or accessor.get("type") != "VEC3":
                        raise ValueError(f"POSITION must be float VEC3: {primitive_label}")
                    if "min" not in accessor or "max" not in accessor:
                        raise ValueError(f"POSITION must declare bounds: {primitive_label}")
                    position_count = len(values)
                    position_values = values
                    mesh_positions[mesh_index].extend(values)
                elif semantic == "NORMAL" and (
                    accessor.get("componentType") != 5126 or accessor.get("type") != "VEC3"
                ):
                    raise ValueError(f"NORMAL must be float VEC3: {primitive_label}")
                elif semantic == "NORMAL":
                    for normal in values:
                        length = math.sqrt(
                            sum(float(component) * float(component) for component in normal)
                        )
                        if not math.isclose(
                            length,
                            1.0,
                            rel_tol=NORMAL_LENGTH_TOLERANCE,
                            abs_tol=NORMAL_LENGTH_TOLERANCE,
                        ):
                            raise ValueError(
                                f"NORMAL vector is not normalized: {primitive_label}"
                            )

            indices_index = _index(
                primitive.get("indices"), len(accessors), f"index accessor: {primitive_label}"
            )
            index_accessor, index_values = decode(indices_index)
            index_view = buffer_views[index_accessor["bufferView"]]
            if (
                index_accessor.get("componentType") not in (5121, 5123, 5125)
                or index_accessor.get("type") != "SCALAR"
                or index_accessor.get("normalized", False) is not False
                or index_view.get("target") != 34963
                or "byteStride" in index_view
                or len(index_values) % 3
            ):
                raise ValueError(f"invalid triangle index accessor: {primitive_label}")
            flat_indices = [int(value[0]) for value in index_values]
            if any(index >= position_count for index in flat_indices):
                raise ValueError(f"out-of-range triangle index: {primitive_label}")
            for offset in range(0, len(flat_indices), 3):
                triangle_indices = flat_indices[offset : offset + 3]
                if len(set(triangle_indices)) != 3:
                    raise ValueError(f"degenerate triangle index: {primitive_label}")
                first, second, third = (
                    position_values[index] for index in triangle_indices
                )
                edge_a = tuple(second[axis] - first[axis] for axis in range(3))
                edge_b = tuple(third[axis] - first[axis] for axis in range(3))
                cross = (
                    edge_a[1] * edge_b[2] - edge_a[2] * edge_b[1],
                    edge_a[2] * edge_b[0] - edge_a[0] * edge_b[2],
                    edge_a[0] * edge_b[1] - edge_a[1] * edge_b[0],
                )
                cross_squared = sum(component * component for component in cross)
                scale_squared = max(
                    sum(component * component for component in edge_a),
                    sum(component * component for component in edge_b),
                    sum(
                        (third[axis] - second[axis]) ** 2
                        for axis in range(3)
                    ),
                )
                if cross_squared <= max(1e-24, scale_squared * scale_squared * 1e-14):
                    raise ValueError(f"zero-area or collinear triangle: {primitive_label}")
            primitive_count += 1
            triangle_count += len(flat_indices) // 3
            uploaded_vertices += position_count

    parents = [0] * len(nodes)
    local_matrices: list[Matrix4] = []
    mesh_references = [0] * len(meshes)
    for node_index, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError(f"invalid node: {label} #{node_index}")
        if any(key in node for key in ("camera", "skin", "weights")):
            raise ValueError(f"non-rigid node is not allowed: {label} #{node_index}")
        transform_shapes = {"translation": 3, "rotation": 4, "scale": 3, "matrix": 16}
        if "matrix" in node and any(key in node for key in ("translation", "rotation", "scale")):
            raise ValueError(f"node mixes matrix and TRS transforms: {label} #{node_index}")
        for transform, expected_length in transform_shapes.items():
            if transform not in node:
                continue
            value = node[transform]
            if (
                not isinstance(value, list)
                or len(value) != expected_length
                or any(
                    not isinstance(component, (int, float)) or isinstance(component, bool)
                    for component in value
                )
            ):
                raise ValueError(f"invalid node {transform}: {label} #{node_index}")
        if "mesh" in node:
            mesh_index = _index(
                node["mesh"], len(meshes), f"node mesh: {label} #{node_index}"
            )
            mesh_references[mesh_index] += 1
        children = node.get("children", [])
        if (
            not isinstance(children, list)
            or any(not isinstance(child, int) or isinstance(child, bool) for child in children)
            or len(set(children)) != len(children)
        ):
            raise ValueError(f"invalid node children: {label} #{node_index}")
        for child in children:
            child_index = _index(child, len(nodes), f"node child: {label} #{node_index}")
            parents[child_index] += 1
            if parents[child_index] > 1:
                raise ValueError(f"node has multiple parents: {label} #{child_index}")
        local_matrices.append(_node_transform_matrix(node, f"{label} #{node_index}"))

    if any(references != 1 for references in mesh_references):
        raise ValueError(f"every GLB mesh must be referenced exactly once: {label}")

    scene = scenes[0]
    if not isinstance(scene, dict) or not isinstance(scene.get("nodes"), list):
        raise ValueError(f"invalid default scene: {label}")
    roots = scene["nodes"]
    if (
        not roots
        or any(not isinstance(root, int) or isinstance(root, bool) for root in roots)
        or len(set(roots)) != len(roots)
    ):
        raise ValueError(f"invalid default-scene roots: {label}")
    visited: set[int] = set()
    active: set[int] = set()
    world_matrices: list[Matrix4 | None] = [None] * len(nodes)

    def visit(node_index: int, parent_matrix: Matrix4) -> None:
        _index(node_index, len(nodes), f"scene node: {label}")
        if node_index in active:
            raise ValueError(f"cycle in node hierarchy: {label}")
        if node_index in visited:
            raise ValueError(f"node appears more than once in scene: {label}")
        active.add(node_index)
        world_matrix = _matrix_multiply(parent_matrix, local_matrices[node_index])
        world_matrices[node_index] = world_matrix
        for child in nodes[node_index].get("children", []):
            visit(child, world_matrix)
        active.remove(node_index)
        visited.add(node_index)

    for root in roots:
        visit(root, IDENTITY_MATRIX)
    if len(visited) != len(nodes):
        raise ValueError(f"orphan node outside default scene: {label}")

    semantic = _extract_semantic_evidence(document, roots)
    if semantic_contract is not None:
        _verify_glb_semantic_contract(document, roots, semantic_contract, label)

    # Decode every accessor, including any not reached through a primitive.
    for accessor_index in range(len(accessors)):
        decode(accessor_index)

    world_positions: list[tuple[float, float, float]] = []
    for node_index, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        world_matrix = world_matrices[node_index]
        if world_matrix is None:
            raise ValueError(f"missing world transform for rendered node: {label}")
        mesh_index = node["mesh"]
        world_positions.extend(
            _transform_point(world_matrix, position)
            for position in mesh_positions[mesh_index]
        )
    if not world_positions:
        raise ValueError(f"GLB contains no rendered world-space geometry: {label}")
    bounds_min = tuple(
        min(position[axis] for position in world_positions) for axis in range(3)
    )
    bounds_max = tuple(
        max(position[axis] for position in world_positions) for axis in range(3)
    )
    bounds_size = tuple(
        bounds_max[axis] - bounds_min[axis] for axis in range(3)
    )
    if any(size <= 0.0 for size in bounds_size):
        raise ValueError(f"GLB world-space bounds are degenerate: {label}")
    footprint_radius = max(
        math.hypot(position[0], position[2]) for position in world_positions
    )

    return GlbMetrics(
        bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        triangles=triangle_count,
        uploaded_vertices=uploaded_vertices,
        embedded_buffer_bytes=embedded_bytes,
        scenes=len(scenes),
        nodes=len(nodes),
        meshes=len(meshes),
        primitives=primitive_count,
        materials=len(materials),
        images=len(document.get("images", [])),
        textures=len(document.get("textures", [])),
        samplers=len(document.get("samplers", [])),
        cameras=len(document.get("cameras", [])),
        skins=len(document.get("skins", [])),
        animations=len(document.get("animations", [])),
        extensions_used=tuple(extensions_used),
        runtime_materials=tuple(runtime_materials),
        bounds_gltf_min=bounds_min,
        bounds_gltf_max=bounds_max,
        bounds_gltf_size=bounds_size,
        footprint_radius=footprint_radius,
        semantic=semantic,
    )


def _strict_json_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            _strict_json_equal(actual[key], expected[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _strict_json_equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def _expect(document: dict, key: str, expected: object, label: str) -> None:
    if key not in document or not _strict_json_equal(document[key], expected):
        raise ValueError(f"unexpected {key} in {label}")


def _expect_exact_keys(document: object, expected: set[str], label: str) -> dict:
    if not isinstance(document, dict) or set(document) != expected:
        raise ValueError(f"unexpected field set in {label}")
    return document


def load_integration_semantic_contracts(
    path: Path = INTEGRATION_PROFILE_PATH,
) -> dict[str, GlbSemanticContract]:
    """Load the digest-bound semantic declarations used by the runtime GLBs."""

    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("tracked integration profile must be a regular non-symlink")
        if metadata.st_size > MAX_TEXT_BYTES:
            raise ValueError("tracked integration profile exceeds size limit")
        payload = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read tracked integration profile: {path}") from exc
    if len(payload) != metadata.st_size:
        raise ValueError("tracked integration profile changed while reading")
    profile = load_json(payload, str(path))
    if profile.get("schema") != "warpkeep.asset-integration-profile.v1":
        raise ValueError("unexpected integration profile schema")
    identity = profile.get("identity")
    if not isinstance(identity, dict) or identity.get("assetId") != ASSET_ID:
        raise ValueError("integration profile asset identity does not match")

    digest_record = _expect_exact_keys(
        profile.get("contractDigest"),
        {"algorithm", "canonicalization", "sha256"},
        "integration profile contractDigest",
    )
    _expect(digest_record, "algorithm", "sha256", "integration profile contractDigest")
    _expect(
        digest_record,
        "canonicalization",
        (
            "exact tracked UTF-8 bytes with the 64 lowercase hexadecimal characters "
            "at $.contractDigest.sha256 replaced by 64 ASCII zeroes; no other "
            "transformation"
        ),
        "integration profile contractDigest",
    )
    declared_digest = digest_record.get("sha256")
    if not isinstance(declared_digest, str) or not SHA256_RE.fullmatch(declared_digest):
        raise ValueError("invalid integration profile contract digest")
    digest_bytes = declared_digest.encode("ascii")
    if payload.count(digest_bytes) != 1:
        raise ValueError("integration profile digest must occur exactly once")
    canonical_payload = payload.replace(digest_bytes, b"0" * 64, 1)
    if hashlib.sha256(canonical_payload).hexdigest() != declared_digest:
        raise ValueError("integration profile contract digest mismatch")
    if declared_digest != INTEGRATION_PROFILE_SHA256:
        raise ValueError("integration profile digest is not the production-pinned digest")

    records = profile.get("profiles")
    if not isinstance(records, list) or len(records) != len(LOD_CONTRACT):
        raise ValueError("integration profile must declare exactly four profiles")
    profile_ids = ("high", "balanced", "compact", "map")
    contracts: dict[str, GlbSemanticContract] = {}
    for record, profile_id, (tier, _, _, _) in zip(
        records, profile_ids, LOD_CONTRACT
    ):
        record = _expect_exact_keys(
            record,
            {
                "boundsGltfMeters",
                "bytes",
                "drawCalls",
                "embeddedBufferBytes",
                "file",
                "id",
                "materials",
                "meshes",
                "nodes",
                "onePrimitivePerMesh",
                "partNodes",
                "primitives",
                "rootNode",
                "sha256",
                "tier",
                "triangles",
                "uploadedVertices",
            },
            f"integration profile {tier}",
        )
        _expect(record, "id", profile_id, f"integration profile {tier}")
        _expect(record, "tier", tier, f"integration profile {tier}")
        _expect(
            record,
            "rootNode",
            f"Warpkeep_CoreWatcher_Level1_{tier}",
            f"integration profile {tier}",
        )
        _expect(record, "onePrimitivePerMesh", True, f"integration profile {tier}")
        part_nodes = record.get("partNodes")
        if (
            not isinstance(part_nodes, list)
            or not part_nodes
            or any(not isinstance(name, str) or not name for name in part_nodes)
            or len(set(part_nodes)) != len(part_nodes)
            or part_nodes != sorted(part_nodes)
        ):
            raise ValueError(f"integration profile {tier} partNodes must be sorted and unique")
        for key, expected in (
            ("nodes", len(part_nodes) + 1),
            ("meshes", len(part_nodes)),
            ("primitives", len(part_nodes)),
            ("drawCalls", len(part_nodes)),
        ):
            _expect(record, key, expected, f"integration profile {tier}")
        contracts[tier] = GlbSemanticContract(
            tier=tier,
            profile_id=profile_id,
            root_node=record["rootNode"],
            part_nodes=tuple(part_nodes),
        )
    return contracts


def _expected_semantic_role(node_name: str) -> str:
    if node_name.startswith("CoreWatcher_CoreCage_"):
        return "core-cage"
    if node_name.startswith(("CoreWatcher_FloatingShard_", "CoreWatcher_GroundShard_")):
        return "floating-shard"
    if node_name.startswith("CoreWatcher_GroundFracture_"):
        return "ground-sigil"
    if node_name == "CoreWatcher_SuspendedCore":
        return "suspended-core"
    if node_name in {
        "CoreWatcher_BifurcatedBody_Left",
        "CoreWatcher_BifurcatedBody_Right",
        "CoreWatcher_CrownRib_Left",
        "CoreWatcher_CrownRib_Right",
        "CoreWatcher_Footprint",
        "CoreWatcher_LowerPedestal",
    }:
        return node_name
    raise ValueError(f"unknown Core Watcher semantic part: {node_name!r}")


def _expected_part_material(node_name: str) -> str:
    if node_name.startswith("CoreWatcher_GroundFracture_") or node_name in {
        "CoreWatcher_CoreCage_2",
        "CoreWatcher_SuspendedCore",
    }:
        return "WK_Core_Ultraviolet"
    if node_name in {
        "CoreWatcher_CoreCage_1",
        "CoreWatcher_CrownRib_Left",
        "CoreWatcher_CrownRib_Right",
        "CoreWatcher_FloatingShard_1",
        "CoreWatcher_FloatingShard_3",
        "CoreWatcher_LowerPedestal",
    }:
        return "WK_Core_BlackenedMetal"
    if node_name in {
        "CoreWatcher_BifurcatedBody_Left",
        "CoreWatcher_BifurcatedBody_Right",
        "CoreWatcher_FloatingShard_2",
        "CoreWatcher_Footprint",
    } or node_name.startswith("CoreWatcher_GroundShard_"):
        return "WK_Core_Obsidian"
    raise ValueError(f"unknown Core Watcher material assignment: {node_name!r}")


def _extract_semantic_evidence(
    document: dict, roots: list[int]
) -> GlbSemanticEvidence:
    nodes = document["nodes"]
    meshes = document["meshes"]
    materials = document["materials"]
    root_name = ""
    if len(roots) == 1:
        candidate = nodes[roots[0]].get("name")
        if isinstance(candidate, str):
            root_name = candidate
    part_nodes: list[str] = []
    roles: list[tuple[str, str]] = []
    assignments: list[tuple[str, str]] = []
    for node in nodes:
        if "mesh" not in node:
            continue
        name = node.get("name") if isinstance(node.get("name"), str) else ""
        extras = node.get("extras")
        role = (
            extras.get("warpkeep_semantic_role")
            if isinstance(extras, dict)
            and isinstance(extras.get("warpkeep_semantic_role"), str)
            else ""
        )
        mesh = meshes[node["mesh"]]
        material_index = mesh["primitives"][0]["material"]
        material_name = materials[material_index]["name"]
        part_nodes.append(name)
        roles.append((name, role))
        assignments.append((name, material_name))
    return GlbSemanticEvidence(
        root_node=root_name,
        part_nodes=tuple(part_nodes),
        semantic_roles=tuple(roles),
        material_assignments=tuple(assignments),
    )


def _verify_glb_semantic_contract(
    document: dict,
    roots: list[int],
    contract: GlbSemanticContract,
    label: str,
) -> None:
    nodes = document["nodes"]
    meshes = document["meshes"]
    materials = document["materials"]
    part_count = len(contract.part_nodes)
    if len(nodes) != part_count + 1 or len(meshes) != part_count:
        raise ValueError(f"semantic node and mesh counts do not match {contract.tier}: {label}")
    if roots != [part_count]:
        raise ValueError(f"{contract.tier} must have one exact semantic root: {label}")
    root = nodes[part_count]
    if set(root) != {"children", "extras", "name"}:
        raise ValueError(f"{contract.tier} root node fields are not exact: {label}")
    if root.get("name") != contract.root_node:
        raise ValueError(f"{contract.tier} root node name does not match contract: {label}")
    expected_root_extras = {
        "warpkeep_asset_id": ASSET_ID,
        "warpkeep_enemy_kind": "core-watcher",
        "warpkeep_encounter_level": 1,
        "warpkeep_state": "dormant-presence",
        "warpkeep_combat_enabled": False,
        "warpkeep_lod": contract.tier,
    }
    if not _strict_json_equal(root.get("extras"), expected_root_extras):
        raise ValueError(f"{contract.tier} root extras do not match contract: {label}")
    if root.get("children") != list(range(part_count)):
        raise ValueError(f"{contract.tier} hierarchy must be flat root-to-parts: {label}")

    rendered_names = tuple(node.get("name") for node in nodes[:part_count])
    if rendered_names != contract.part_nodes or len(set(rendered_names)) != part_count:
        raise ValueError(f"{contract.tier} part node list does not match contract: {label}")
    for index, expected_name in enumerate(contract.part_nodes):
        node = nodes[index]
        if node.get("mesh") != index or "children" in node:
            raise ValueError(f"{contract.tier} hierarchy must be flat root-to-parts: {label}")
        expected_extras = {
            "warpkeep_semantic_role": _expected_semantic_role(expected_name)
        }
        if not _strict_json_equal(node.get("extras"), expected_extras):
            raise ValueError(
                f"{contract.tier} semantic role does not match for {expected_name}: {label}"
            )
        mesh = meshes[index]
        if set(mesh) != {"name", "primitives"}:
            raise ValueError(f"{contract.tier} mesh fields are not exact: {label}")
        if mesh.get("name") != f"{expected_name}_Mesh":
            raise ValueError(
                f"{contract.tier} mesh name does not match for {expected_name}: {label}"
            )
        primitive = mesh["primitives"][0]
        material_index = primitive["material"]
        material_name = materials[material_index]["name"]
        if material_name != _expected_part_material(expected_name):
            raise ValueError(
                f"{contract.tier} material assignment does not match for "
                f"{expected_name}: {label}"
            )


def _declared_runtime_material(record: object, label: str) -> RuntimeMaterial:
    expected_keys = {
        "name",
        "alphaMode",
        "opaque",
        "doubleSided",
        "baseColorFactor",
        "metallic",
        "roughness",
        "emissiveFactor",
        "emissiveStrength",
    }
    if not isinstance(record, dict) or set(record) != expected_keys:
        raise ValueError(f"runtime material field set does not match contract: {label}")
    name = record["name"]
    alpha_mode = record["alphaMode"]
    opaque = record["opaque"]
    double_sided = record["doubleSided"]
    if not isinstance(name, str) or name not in EXPECTED_MATERIALS:
        raise ValueError(f"invalid runtime material name: {label}")
    if alpha_mode not in ("OPAQUE", "MASK", "BLEND"):
        raise ValueError(f"invalid declared material alphaMode: {label}")
    if not isinstance(opaque, bool) or opaque is not (alpha_mode == "OPAQUE"):
        raise ValueError(f"declared opaque/alphaMode mismatch: {label}")
    if not isinstance(double_sided, bool):
        raise ValueError(f"invalid declared material doubleSided: {label}")
    return RuntimeMaterial(
        name=name,
        alpha_mode=alpha_mode,
        opaque=opaque,
        double_sided=double_sided,
        base_color_factor=_finite_vector(
            record["baseColorFactor"],
            4,
            f"declared baseColorFactor: {label}",
            minimum=0.0,
            maximum=1.0,
        ),
        metallic=_finite_number(
            record["metallic"],
            f"declared metallic: {label}",
            minimum=0.0,
            maximum=1.0,
        ),
        roughness=_finite_number(
            record["roughness"],
            f"declared roughness: {label}",
            minimum=0.0,
            maximum=1.0,
        ),
        emissive_factor=_finite_vector(
            record["emissiveFactor"],
            3,
            f"declared emissiveFactor: {label}",
            minimum=0.0,
            maximum=1.0,
        ),
        emissive_strength=_finite_number(
            record["emissiveStrength"],
            f"declared emissiveStrength: {label}",
            minimum=0.0,
        ),
    )


def _runtime_materials_close(
    declared: RuntimeMaterial, emitted: RuntimeMaterial
) -> bool:
    if (
        declared.name != emitted.name
        or declared.alpha_mode != emitted.alpha_mode
        or declared.opaque is not emitted.opaque
        or declared.double_sided is not emitted.double_sided
    ):
        return False

    def close(left: float, right: float) -> bool:
        return math.isclose(left, right, rel_tol=1e-6, abs_tol=1e-7)

    return (
        all(
            close(left, right)
            for left, right in zip(
                declared.base_color_factor, emitted.base_color_factor
            )
        )
        and close(declared.metallic, emitted.metallic)
        and close(declared.roughness, emitted.roughness)
        and all(
            close(left, right)
            for left, right in zip(declared.emissive_factor, emitted.emissive_factor)
        )
        and close(declared.emissive_strength, emitted.emissive_strength)
    )


def verify_material_contract(
    manifest: dict, metrics: tuple[GlbMetrics, ...]
) -> None:
    contract = _expect_exact_keys(
        manifest.get("materialContract"),
        {
            "alphaBlendMaterials",
            "authoringNote",
            "heraldry",
            "images",
            "materials",
            "palette",
            "textures",
        },
        "runtime materialContract",
    )
    for key, expected in (
        ("alphaBlendMaterials", 0),
        ("heraldry", "none"),
        ("images", 0),
        ("textures", 0),
        (
            "authoringNote",
            {
                "note": (
                    "Blender glTF export normalizes emissive color and strength; "
                    "the material records above are the emitted runtime values."
                ),
                "runtimeValuesDerivedFromExportedGlbs": True,
                "ultravioletNodeEmissionStrength": 3.5,
            },
        ),
        ("palette", "obsidian, blackened metal, restrained cold ultraviolet"),
    ):
        _expect(contract, key, expected, "runtime materialContract")

    records = contract.get("materials")
    if not isinstance(records, list) or len(records) != 3:
        raise ValueError("runtime materialContract must contain exactly three materials")
    declared_list = tuple(
        _declared_runtime_material(record, f"runtime material #{index}")
        for index, record in enumerate(records)
    )
    declared = {material.name: material for material in declared_list}
    if len(declared) != 3 or frozenset(declared) != EXPECTED_MATERIALS:
        raise ValueError("runtime materialContract names must be exact and unique")

    for (tier, _, _, _), metric in zip(LOD_CONTRACT, metrics):
        emitted = {material.name: material for material in metric.runtime_materials}
        if frozenset(emitted) != EXPECTED_MATERIALS or len(emitted) != 3:
            raise ValueError(f"{tier} emitted material names are not exact and unique")
        for name in EXPECTED_MATERIALS:
            if not _runtime_materials_close(declared[name], emitted[name]):
                raise ValueError(
                    f"runtime materialContract differs from {tier} emitted {name} values"
                )


def _verify_bounds_blender(record: object, metric: GlbMetrics, tier: str) -> None:
    bounds = _expect_exact_keys(
        record, {"min", "max", "size"}, f"runtime LOD {tier} boundsBlender"
    )
    declared_min = _finite_vector(
        bounds["min"], 3, f"runtime LOD {tier} boundsBlender min"
    )
    declared_max = _finite_vector(
        bounds["max"], 3, f"runtime LOD {tier} boundsBlender max"
    )
    declared_size = _finite_vector(
        bounds["size"],
        3,
        f"runtime LOD {tier} boundsBlender size",
        minimum=0.0,
    )
    for axis in range(3):
        if declared_max[axis] <= declared_min[axis]:
            raise ValueError(f"runtime LOD {tier} boundsBlender is degenerate")
        actual_size = declared_max[axis] - declared_min[axis]
        if not math.isclose(
            declared_size[axis], actual_size, rel_tol=1e-6, abs_tol=1e-6
        ):
            raise ValueError(f"runtime LOD {tier} boundsBlender size is inconsistent")

    # glTF exports Blender (X, Y, Z) into runtime (X, Z, -Y). Convert the
    # emitted, hierarchy-transformed geometry back to authoring axes before
    # comparing it with the source-scene envelope recorded by the builder.
    emitted_blender_min = (
        metric.bounds_gltf_min[0],
        -metric.bounds_gltf_max[2],
        metric.bounds_gltf_min[1],
    )
    emitted_blender_max = (
        metric.bounds_gltf_max[0],
        -metric.bounds_gltf_min[2],
        metric.bounds_gltf_max[1],
    )
    for axis in range(3):
        lower_margin = emitted_blender_min[axis] - declared_min[axis]
        upper_margin = declared_max[axis] - emitted_blender_max[axis]
        if lower_margin < -BOUND_TOLERANCE_METERS or upper_margin < -BOUND_TOLERANCE_METERS:
            raise ValueError(
                f"runtime LOD {tier} boundsBlender does not contain emitted glTF geometry"
            )
        if (
            lower_margin > MAX_AUTHORING_BOUND_MARGIN_METERS
            or upper_margin > MAX_AUTHORING_BOUND_MARGIN_METERS
        ):
            raise ValueError(
                f"runtime LOD {tier} boundsBlender is too loose for emitted glTF geometry"
            )


def verify_runtime_manifest(files: dict[str, bytes]) -> tuple[GlbMetrics, ...]:
    manifest = load_json(files[RUNTIME_MANIFEST], RUNTIME_MANIFEST)
    _expect_exact_keys(
        manifest,
        {
            "assetId",
            "authoringCoordinateSystem",
            "authorityBoundary",
            "category",
            "combatEnabled",
            "coordinateSystem",
            "encounterLevel",
            "enemyKind",
            "faction",
            "frontFacing",
            "lodGuidance",
            "lods",
            "materialContract",
            "metersPerUnit",
            "motion",
            "name",
            "pivot",
            "revision",
            "schema",
            "selectionGuidance",
            "state",
            "version",
        },
        "runtime manifest",
    )
    for key, expected in (
        ("schema", "warpkeep.runtime-encounter-asset.v1"),
        ("version", "1.0.0"),
        ("revision", REVISION),
        ("assetId", ASSET_ID),
        ("authoringCoordinateSystem", "Blender, right-handed, +Z up, -Y front"),
        ("category", "Encounters/Core/WatcherLevel1"),
        ("coordinateSystem", "glTF 2.0, right-handed, +Y up, +Z forward"),
        ("faction", "The Core"),
        ("frontFacing", "+Z in glTF / -Y in Blender"),
        ("name", "Core Watcher"),
        ("enemyKind", "core-watcher"),
        ("encounterLevel", 1),
        ("combatEnabled", False),
        ("authorityBoundary", AUTHORITY_BOUNDARY),
        ("lodGuidance", RUNTIME_LOD_GUIDANCE),
        ("metersPerUnit", 1.0),
        ("motion", RUNTIME_MOTION_CONTRACT),
        ("pivot", "footprint center on Blender Z=0 / glTF Y=0"),
        ("selectionGuidance", RUNTIME_SELECTION_GUIDANCE),
        ("state", "dormant-presence"),
    ):
        _expect(manifest, key, expected, "runtime manifest")

    lod_records = manifest.get("lods")
    if not isinstance(lod_records, list) or len(lod_records) != len(LOD_CONTRACT):
        raise ValueError("runtime manifest must contain exactly four LOD records")

    semantic_contracts = load_integration_semantic_contracts()
    metrics: list[GlbMetrics] = []
    for record, (tier, filename, triangle_ceiling, byte_ceiling) in zip(
        lod_records, LOD_CONTRACT
    ):
        record = _expect_exact_keys(
            record,
            {
                "animations",
                "boundsBlender",
                "bytes",
                "cameras",
                "embeddedBufferBytes",
                "extensionsUsed",
                "externalUris",
                "file",
                "images",
                "materials",
                "meshes",
                "nodes",
                "primitives",
                "rigged",
                "samplers",
                "scenes",
                "sha256",
                "skins",
                "textures",
                "tier",
                "triangles",
                "uploadedVertices",
            },
            f"runtime LOD {tier}",
        )
        _expect(record, "tier", tier, f"runtime LOD {tier}")
        _expect(record, "file", filename, f"runtime LOD {tier}")
        path = f"{RUNTIME_DIRECTORY}/{filename}"
        payload = files[path]
        if len(payload) > byte_ceiling:
            raise ValueError(f"{tier} exceeds byte ceiling {byte_ceiling}")
        metric = inspect_glb(payload, path, semantic_contracts[tier])
        if not 0 < metric.triangles <= triangle_ceiling:
            raise ValueError(f"{tier} exceeds triangle ceiling {triangle_ceiling}")
        expected_fields = {
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
        for key, expected in expected_fields.items():
            _expect(record, key, expected, f"runtime LOD {tier}")
        _verify_bounds_blender(record["boundsBlender"], metric, tier)
        metrics.append(metric)

    triangles = [metric.triangles for metric in metrics]
    byte_counts = [metric.bytes for metric in metrics]
    if any(left <= right for left, right in zip(triangles, triangles[1:])):
        raise ValueError("LOD triangles must be strictly descending")
    if any(left <= right for left, right in zip(byte_counts, byte_counts[1:])):
        raise ValueError("LOD bytes must be strictly descending")
    result = tuple(metrics)
    for (tier, _, _, _), metric in zip(LOD_CONTRACT, result):
        if not math.isclose(
            metric.bounds_gltf_min[1],
            0.0,
            rel_tol=0.0,
            abs_tol=BOUND_TOLERANCE_METERS,
        ):
            raise ValueError(f"{tier} emitted glTF geometry does not contact the ground")
        if (
            metric.footprint_radius
            > RUNTIME_SELECTION_GUIDANCE["presentationFootprintRadiusMeters"]
            + BOUND_TOLERANCE_METERS
        ):
            raise ValueError(f"{tier} exceeds the presentation footprint radius")
        if (
            metric.bounds_gltf_max[1]
            > RUNTIME_SELECTION_GUIDANCE["suggestedPickCylinderHeightMeters"]
            + BOUND_TOLERANCE_METERS
        ):
            raise ValueError(f"{tier} exceeds the suggested pick-cylinder height")
    heights = [metric.bounds_gltf_size[1] for metric in result]
    if max(heights) - min(heights) > 0.02:
        raise ValueError("LOD emitted glTF heights are not stable")
    verify_material_contract(manifest, result)
    return result


def verify_asset_manifest(files: dict[str, bytes], metrics: tuple[GlbMetrics, ...]) -> None:
    manifest = load_json(files[ASSET_MANIFEST], ASSET_MANIFEST)
    _expect_exact_keys(
        manifest,
        {
            "canonicalEditableSource",
            "category",
            "designIntent",
            "faction",
            "heroPreview",
            "lodLineupPreview",
            "mobilePreview",
            "name",
            "qaReport",
            "revision",
            "runtimeContracts",
            "schema",
            "sourceSemanticFingerprintSha256",
            "status",
            "transparentPreview",
            "version",
            "watcher",
        },
        "asset manifest",
    )
    for key, expected in (
        ("schema", "warpkeep.authoring-package.v1"),
        ("version", "1.0.0"),
        ("revision", REVISION),
        ("category", "Encounters/Core/WatcherLevel1"),
        ("faction", "The Core"),
        ("name", "Warpkeep Core Watcher — Level 1"),
        ("canonicalEditableSource", SOURCE_BLEND),
        ("designIntent", RUNTIME_DESIGN_INTENT),
        ("heroPreview", "Previews/Warpkeep_CoreWatcher_Level1_Presentation_1920.jpg"),
        ("lodLineupPreview", "Previews/Warpkeep_CoreWatcher_Level1_LOD_Lineup_2400.jpg"),
        ("transparentPreview", "Previews/Warpkeep_CoreWatcher_Level1_Transparent_1600.png"),
        ("mobilePreview", "Previews/Mobile/Warpkeep_CoreWatcher_Level1_Map_512.png"),
        ("qaReport", QA_REPORT),
        ("runtimeContracts", RUNTIME_AUTHORING_CONTRACT),
        ("status", "editable-static-runtime-validated-release-candidate"),
    ):
        _expect(manifest, key, expected, "asset manifest")
    fingerprint = manifest.get("sourceSemanticFingerprintSha256")
    if fingerprint != SOURCE_SEMANTIC_FINGERPRINT_SHA256:
        raise ValueError("asset manifest source semantic fingerprint is not the pinned source")
    watcher = _expect_exact_keys(
        manifest.get("watcher"),
        {
            "assetId",
            "combatEnabled",
            "encounterLevel",
            "enemyKind",
            "name",
            "runtimeManifest",
            "source",
            "state",
            "triangles",
        },
        "asset manifest watcher record",
    )
    for key, expected in (
        ("assetId", ASSET_ID),
        ("name", "Core Watcher"),
        ("enemyKind", "core-watcher"),
        ("encounterLevel", 1),
        ("combatEnabled", False),
        ("runtimeManifest", RUNTIME_MANIFEST),
        ("source", SOURCE_BLEND),
        ("state", "dormant-presence"),
    ):
        _expect(watcher, key, expected, "asset manifest watcher record")
    expected_triangles = {
        tier: metric.triangles
        for (tier, _, _, _), metric in zip(LOD_CONTRACT, metrics)
    }
    _expect(watcher, "triangles", expected_triangles, "asset manifest watcher record")


def verify_qa(files: dict[str, bytes]) -> None:
    report = load_json(files[QA_REPORT], QA_REPORT)
    for key, expected in (
        ("schema", "warpkeep.runtime-qa.v1"),
        ("revision", REVISION),
        ("status", "passed"),
        (
            "budgets",
            {
                tier: {"triangles": triangle_ceiling, "bytes": byte_ceiling}
                for tier, _, triangle_ceiling, byte_ceiling in LOD_CONTRACT
            },
        ),
    ):
        _expect(report, key, expected, "runtime QA report")
    checks = report.get("checks")
    expected_records = [
        {"check": name, "passed": True} for name in EXPECTED_QA_CHECKS
    ]
    if not _strict_json_equal(checks, expected_records):
        raise ValueError("runtime QA report must contain the exact 58 unique passed checks")
    if not _strict_json_equal(report.get("checksTotal"), 58) or not _strict_json_equal(
        report.get("checksPassed"), 58
    ):
        raise ValueError("runtime QA report must declare exactly 58/58 checks passed")


def _png_dimensions(payload: bytes, label: str) -> tuple[int, int]:
    if len(payload) < 8 or payload[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"invalid PNG preview: {label}")
    offset = 8
    dimensions: tuple[int, int] | None = None
    seen_idat = False
    idat_ended = False
    while offset < len(payload):
        if offset + 12 > len(payload):
            raise ValueError(f"truncated PNG chunk: {label}")
        length = struct.unpack_from(">I", payload, offset)[0]
        chunk_type = payload[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(payload):
            raise ValueError(f"truncated PNG chunk payload: {label}")
        if len(chunk_type) != 4 or any(
            not (65 <= byte <= 90 or 97 <= byte <= 122) for byte in chunk_type
        ):
            raise ValueError(f"invalid PNG chunk type: {label}")
        data = payload[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack_from(">I", payload, offset + 8 + length)[0]
        actual_crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"PNG chunk CRC mismatch: {label}")
        if chunk_type in FORBIDDEN_PNG_CHUNKS:
            raise ValueError(
                f"forbidden PNG metadata chunk {chunk_type.decode('ascii')}: {label}"
            )

        if dimensions is None and chunk_type != b"IHDR":
            raise ValueError(f"PNG IHDR must be first: {label}")
        if chunk_type == b"IHDR":
            if dimensions is not None or length != 13:
                raise ValueError(f"invalid PNG IHDR: {label}")
            width, height, bit_depth, color_type, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", data)
            )
            valid_depths = {
                0: {1, 2, 4, 8, 16},
                2: {8, 16},
                3: {1, 2, 4, 8},
                4: {8, 16},
                6: {8, 16},
            }
            if (
                width == 0
                or height == 0
                or bit_depth not in valid_depths.get(color_type, set())
                or compression != 0
                or filtering != 0
                or interlace not in (0, 1)
            ):
                raise ValueError(f"invalid PNG IHDR values: {label}")
            dimensions = (width, height)
        elif chunk_type == b"IDAT":
            if idat_ended:
                raise ValueError(f"non-contiguous PNG IDAT chunks: {label}")
            seen_idat = True
        elif seen_idat:
            idat_ended = True

        if chunk_type == b"IEND":
            if length != 0 or not seen_idat or end != len(payload) or dimensions is None:
                raise ValueError(f"invalid PNG IEND or trailing data: {label}")
            return dimensions
        offset = end
    raise ValueError(f"PNG IEND is missing: {label}")


def _jpeg_dimensions(payload: bytes, label: str) -> tuple[int, int]:
    if len(payload) < 4 or payload[:2] != b"\xff\xd8" or payload[-2:] != b"\xff\xd9":
        raise ValueError(f"invalid JPEG preview: {label}")
    offset = 2
    dimensions: tuple[int, int] | None = None
    seen_scan = False
    frame_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while offset < len(payload):
        if payload[offset] != 0xFF:
            raise ValueError(f"invalid JPEG marker stream: {label}")
        while offset < len(payload) and payload[offset] == 0xFF:
            offset += 1
        if offset >= len(payload):
            break
        marker = payload[offset]
        offset += 1
        if marker == 0xD9:
            if offset != len(payload) or dimensions is None or not seen_scan:
                raise ValueError(f"invalid JPEG end marker or missing frame/scan: {label}")
            return dimensions
        if marker == 0xD8:
            raise ValueError(f"unexpected JPEG start marker: {label}")
        if marker == 0x00:
            raise ValueError(f"stuffed JPEG byte outside scan data: {label}")
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if marker in FORBIDDEN_JPEG_MARKERS:
            raise ValueError(
                f"forbidden JPEG metadata marker {FORBIDDEN_JPEG_MARKERS[marker]}: {label}"
            )
        if offset + 2 > len(payload):
            raise ValueError(f"truncated JPEG marker: {label}")
        segment_length = struct.unpack_from(">H", payload, offset)[0]
        if segment_length < 2 or offset + segment_length > len(payload):
            raise ValueError(f"invalid JPEG segment length: {label}")
        if marker in frame_markers:
            if segment_length < 7:
                raise ValueError(f"invalid JPEG frame: {label}")
            height, width = struct.unpack_from(">HH", payload, offset + 3)
            if width == 0 or height == 0 or dimensions is not None:
                raise ValueError(f"invalid or duplicate JPEG frame: {label}")
            dimensions = (width, height)
        segment_end = offset + segment_length
        if marker != 0xDA:
            offset = segment_end
            continue

        seen_scan = True
        offset = segment_end
        while offset < len(payload):
            marker_start = payload.find(b"\xff", offset)
            if marker_start < 0 or marker_start + 1 >= len(payload):
                raise ValueError(f"unterminated JPEG scan data: {label}")
            cursor = marker_start + 1
            while cursor < len(payload) and payload[cursor] == 0xFF:
                cursor += 1
            if cursor >= len(payload):
                raise ValueError(f"unterminated JPEG marker fill: {label}")
            escaped = payload[cursor]
            if escaped == 0x00 or 0xD0 <= escaped <= 0xD7:
                offset = cursor + 1
                continue
            offset = marker_start
            break
    raise ValueError(f"JPEG end marker is missing: {label}")


def verify_supporting_files(files: dict[str, bytes]) -> None:
    blend = files[SOURCE_BLEND]
    if (
        len(blend) < 17
        or blend[:7] != b"BLENDER"
        or not blend[7:9].isdigit()
        or blend[9:10] != b"-"
        or not blend[10:12].isdigit()
        or blend[12:13] != b"v"
        or not blend[13:17].isdigit()
    ):
        raise ValueError("editable source has an invalid Blender header")

    for name in ("PACKAGE-NOTICE.md", "README.md"):
        try:
            text = files[name].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"invalid UTF-8 text file: {name}") from exc
        if not text.strip():
            raise ValueError(f"required text file is empty: {name}")

    for name, dimensions in PREVIEW_DIMENSIONS.items():
        payload = files[name]
        actual = (
            _png_dimensions(payload, name)
            if name.endswith(".png")
            else _jpeg_dimensions(payload, name)
        )
        if actual != dimensions:
            raise ValueError(f"preview dimensions mismatch: {name}")


def verify_package(path: Path | str) -> VerificationResult:
    source = Path(path)
    files = read_package(source)
    verify_checksums(files)
    metrics = verify_runtime_manifest(files)
    verify_asset_manifest(files, metrics)
    verify_qa(files)
    verify_supporting_files(files)
    return VerificationResult(
        source=source,
        files=len(files),
        lods=len(metrics),
        triangles=tuple(metric.triangles for metric in metrics),
        bytes=tuple(metric.bytes for metric in metrics),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Structurally verify a Core Watcher Level 1 ZIP candidate or extracted "
            "package root."
        ),
        epilog=(
            "This check does not establish archive authenticity. Authenticate an exact "
            "release with releases/core-watcher-level1-2026-08-03/manifest.json and "
            "its SHA256SUMS.txt through scripts/verify_release.py."
        ),
    )
    parser.add_argument("package", type=Path, help="release-candidate ZIP or package root")
    args = parser.parse_args()
    try:
        result = verify_package(args.package)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Core Watcher verification failed: {exc}\n")
    triangle_summary = "/".join(str(value) for value in result.triangles)
    print(
        f"Structurally verified {PACKAGE_NAME}: {result.files} files, {result.lods} LODs, "
        f"triangles {triangle_summary}."
    )


if __name__ == "__main__":
    main()
