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


def inspect_glb(payload: bytes, label: str = "runtime GLB") -> GlbMetrics:
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
    for mesh_index, mesh in enumerate(meshes):
        if not isinstance(mesh, dict) or not isinstance(mesh.get("primitives"), list):
            raise ValueError(f"invalid mesh: {label} #{mesh_index}")
        if not mesh["primitives"] or "weights" in mesh:
            raise ValueError(f"empty or morph-weighted mesh: {label} #{mesh_index}")
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
                elif semantic == "NORMAL" and (
                    accessor.get("componentType") != 5126 or accessor.get("type") != "VEC3"
                ):
                    raise ValueError(f"NORMAL must be float VEC3: {primitive_label}")

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
            _index(node["mesh"], len(meshes), f"node mesh: {label} #{node_index}")
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

    def visit(node_index: int) -> None:
        _index(node_index, len(nodes), f"scene node: {label}")
        if node_index in active:
            raise ValueError(f"cycle in node hierarchy: {label}")
        if node_index in visited:
            raise ValueError(f"node appears more than once in scene: {label}")
        active.add(node_index)
        for child in nodes[node_index].get("children", []):
            visit(child)
        active.remove(node_index)
        visited.add(node_index)

    for root in roots:
        visit(root)
    if len(visited) != len(nodes):
        raise ValueError(f"orphan node outside default scene: {label}")

    # Decode every accessor, including any not reached through a primitive.
    for accessor_index in range(len(accessors)):
        decode(accessor_index)

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
    contract = manifest.get("materialContract")
    if not isinstance(contract, dict):
        raise ValueError("runtime materialContract is missing")
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


def verify_runtime_manifest(files: dict[str, bytes]) -> tuple[GlbMetrics, ...]:
    manifest = load_json(files[RUNTIME_MANIFEST], RUNTIME_MANIFEST)
    for key, expected in (
        ("schema", "warpkeep.runtime-encounter-asset.v1"),
        ("version", "1.0.0"),
        ("revision", REVISION),
        ("assetId", ASSET_ID),
        ("category", "Encounters/Core/WatcherLevel1"),
        ("faction", "The Core"),
        ("name", "Core Watcher"),
        ("enemyKind", "core-watcher"),
        ("encounterLevel", 1),
        ("combatEnabled", False),
        ("authorityBoundary", AUTHORITY_BOUNDARY),
    ):
        _expect(manifest, key, expected, "runtime manifest")

    lod_records = manifest.get("lods")
    if not isinstance(lod_records, list) or len(lod_records) != len(LOD_CONTRACT):
        raise ValueError("runtime manifest must contain exactly four LOD records")

    metrics: list[GlbMetrics] = []
    for record, (tier, filename, triangle_ceiling, byte_ceiling) in zip(
        lod_records, LOD_CONTRACT
    ):
        if not isinstance(record, dict):
            raise ValueError(f"invalid runtime LOD record: {tier}")
        _expect(record, "tier", tier, f"runtime LOD {tier}")
        _expect(record, "file", filename, f"runtime LOD {tier}")
        path = f"{RUNTIME_DIRECTORY}/{filename}"
        payload = files[path]
        if len(payload) > byte_ceiling:
            raise ValueError(f"{tier} exceeds byte ceiling {byte_ceiling}")
        metric = inspect_glb(payload, path)
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
        metrics.append(metric)

    triangles = [metric.triangles for metric in metrics]
    byte_counts = [metric.bytes for metric in metrics]
    if any(left <= right for left, right in zip(triangles, triangles[1:])):
        raise ValueError("LOD triangles must be strictly descending")
    if any(left <= right for left, right in zip(byte_counts, byte_counts[1:])):
        raise ValueError("LOD bytes must be strictly descending")
    result = tuple(metrics)
    verify_material_contract(manifest, result)
    return result


def verify_asset_manifest(files: dict[str, bytes], metrics: tuple[GlbMetrics, ...]) -> None:
    manifest = load_json(files[ASSET_MANIFEST], ASSET_MANIFEST)
    for key, expected in (
        ("schema", "warpkeep.authoring-package.v1"),
        ("version", "1.0.0"),
        ("revision", REVISION),
        ("category", "Encounters/Core/WatcherLevel1"),
        ("faction", "The Core"),
        ("canonicalEditableSource", SOURCE_BLEND),
        ("heroPreview", "Previews/Warpkeep_CoreWatcher_Level1_Presentation_1920.jpg"),
        ("lodLineupPreview", "Previews/Warpkeep_CoreWatcher_Level1_LOD_Lineup_2400.jpg"),
        ("transparentPreview", "Previews/Warpkeep_CoreWatcher_Level1_Transparent_1600.png"),
        ("mobilePreview", "Previews/Mobile/Warpkeep_CoreWatcher_Level1_Map_512.png"),
        ("qaReport", QA_REPORT),
    ):
        _expect(manifest, key, expected, "asset manifest")
    fingerprint = manifest.get("sourceSemanticFingerprintSha256")
    if not isinstance(fingerprint, str) or SHA256_RE.fullmatch(fingerprint) is None:
        raise ValueError("asset manifest source semantic fingerprint is invalid")
    watcher = manifest.get("watcher")
    if not isinstance(watcher, dict):
        raise ValueError("asset manifest watcher record is missing")
    for key, expected in (
        ("assetId", ASSET_ID),
        ("name", "Core Watcher"),
        ("enemyKind", "core-watcher"),
        ("encounterLevel", 1),
        ("combatEnabled", False),
        ("runtimeManifest", RUNTIME_MANIFEST),
        ("source", SOURCE_BLEND),
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
