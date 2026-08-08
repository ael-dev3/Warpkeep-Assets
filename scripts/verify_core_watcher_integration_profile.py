#!/usr/bin/env python3
"""Verify the tracked, review-only Core Watcher integration handoff.

This verifier needs no unpublished release binary. It binds the advisory
renderer profile to the tracked release manifest, the byte-exact packaged
runtime-manifest copy, and metadata-free review images. It does not authorize
publication, integration, gameplay, or activation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import sys


PROFILE_PATH = Path(
    "contracts/core-watcher-level1-2026-08-03.integration-profile.json"
)
RUNTIME_PATH = Path(
    "contracts/core-watcher-level1-2026-08-03.runtime-manifest.json"
)
RELEASE_MANIFEST_PATH = Path("releases/core-watcher-level1-2026-08-03/manifest.json")
GALLERY_PATH = Path("previews/core-watcher-level1-2026-08-03/gallery.json")
PACKAGE_VERIFIER_PATH = Path("scripts/verify_core_watcher_level1.py")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
ZERO_DIGEST = "0" * 64
EXPECTED_PROFILE_DIGEST = "0a34614dfb42f754fd2524b23ef213c2db502768ad9230bd6a27a9198a8251c0"
MAX_PROFILE_BYTES = 256 * 1024
MAX_TRACKED_JSON_BYTES = 2 * 1024 * 1024
MAX_PREVIEW_BYTES = 8 * 1024 * 1024
CANONICALIZATION = (
    "exact tracked UTF-8 bytes with the 64 lowercase hexadecimal characters at "
    "$.contractDigest.sha256 replaced by 64 ASCII zeroes; no other transformation"
)

ROOT_KEYS = {
    "assetBinding",
    "authorityBoundary",
    "contractDigest",
    "fallbackAndAccessibility",
    "futureGameplaySlices",
    "geometry",
    "identity",
    "instancing",
    "loading",
    "motion",
    "presentation",
    "profiles",
    "qualityCamera",
    "schema",
    "selectionAndGestures",
    "status",
    "telemetryAndPrivacy",
    "version",
}

EXPECTED_STATUS = {
    "activationAuthorized": False,
    "gameplayImplemented": False,
    "integrated": False,
    "releasePublished": False,
    "reviewOnly": True,
    "runtimeUseAuthorized": False,
}
EXPECTED_AUTHORITY = {
    "actions": False,
    "activation": False,
    "ai": False,
    "catalog": False,
    "collision": False,
    "combat": False,
    "combatState": False,
    "cooldowns": False,
    "damage": False,
    "encounterState": False,
    "fogOfWar": False,
    "health": False,
    "loot": False,
    "networking": False,
    "ownership": False,
    "pathing": False,
    "persistence": False,
    "picking": False,
    "placement": False,
    "placementEligibility": False,
    "populationCount": False,
    "respawn": False,
    "rewards": False,
    "routing": False,
    "selection": False,
    "siteIdentity": False,
    "spacetimeDb": False,
    "visibility": False,
    "visualOnly": True,
    "worldCoordinates": False,
}
EXPECTED_LOADING = {
    "abortable": True,
    "allowedExtensions": ["KHR_materials_emissive_strength"],
    "contentAddressFilenamePattern": "<role>-<sha256-first-16>.glb",
    "contextRecoverySupported": True,
    "credentials": "same-origin",
    "embeddedOnly": True,
    "exactBytesBeforeParse": True,
    "exactSha256BeforeParse": True,
    "idempotentDisposal": True,
    "ordinaryBuildNetworkAccess": False,
    "redirectsAllowed": False,
    "releasePublicationRequiredBeforeUse": True,
    "runtimeGitHubReleaseDependency": False,
    "runtimeUseAuthorized": False,
    "sameOriginOnly": True,
    "timeoutCapMilliseconds": 60000,
    "timeoutMilliseconds": 20000,
    "transactionalInstall": True,
}
EXPECTED_RELEASE_BINDING = {
    "bytes": 7520,
    "sha256": "60eaa17e477d37f42d25b446ab9a907c6d57b919007b3632c3e5f327283113f0",
    "trackedPath": "releases/core-watcher-level1-2026-08-03/manifest.json",
}
EXPECTED_GALLERY_BINDING = {
    "bytes": 1255,
    "sha256": "90ec48066c69c6a4223dbc3911784c08c6dc86cad686d3581f4cfcfd15cab6bc",
    "trackedPath": "previews/core-watcher-level1-2026-08-03/gallery.json",
}
EXPECTED_RUNTIME_BINDING = {
    "bytes": 7462,
    "packagePath": (
        "Warpkeep_CoreWatcher_Level1_GameReady/Runtime/Encounters/Core/"
        "WatcherLevel1/runtime-manifest.json"
    ),
    "sha256": "0339dc9abe5c6a9340ef9be1d0ad908a5130eb9339a7ace4fafdb25a7548d1fd",
    "trackedPath": "contracts/core-watcher-level1-2026-08-03.runtime-manifest.json",
}
EXPECTED_SOURCE_BINDING = {
    "bytes": 2416,
    "sha256": "2c52e4744914b27fad6ba6b1e28ae1a02363612080079ac62933fd16ce580b04",
    "trackedPath": "manifests/core-watcher-level1-2026-08-03.source.json",
}
EXPECTED_QUALITY = {
    "allocatorOwnsFinalChoice": True,
    "beyondFarBand": "engine-marker",
    "distanceHintsMeters": {
        "balancedThrough": 18,
        "compactThrough": 36,
        "highThrough": 8,
        "mapThrough": 72,
    },
    "hysteresisRequired": True,
    "modelPresentationNeverGatesDiscoverability": True,
    "packageReducedQualityHintDisposition": (
        "superseded-here-by-no-optional-fetch; LOD2 remains available to "
        "non-reduced camera allocation"
    ),
    "policies": {
        "balanced": {
            "closeSelected": "LOD1_Balanced",
            "optionalAssetFetch": True,
            "overview": "LOD3_Map",
            "strategy": "LOD2_Compact",
        },
        "high": {
            "closeSelected": "LOD0_High",
            "optionalAssetFetch": True,
            "overview": "LOD3_Map",
            "strategy": "LOD2_Compact",
        },
        "reduced": {
            "closeSelected": "engine-marker",
            "optionalAssetFetch": False,
            "overview": "engine-marker",
            "strategy": "engine-marker",
        },
    },
    "semanticMarkerAlwaysMountedForValidInFramePublicRecord": True,
    "strategicOverviewPresentationPointerInert": True,
}
EXPECTED_SELECTION = {
    "distantColliderCannotWin": True,
    "engineOwnsPicking": True,
    "focusRestoredAfterClose": True,
    "mapZoomCadenceIndependent": True,
    "mapZoomCumulativePerGesture": True,
    "minimumControlCssPixels": 44,
    "mustNotCaptureMapPanPinchOrWheel": True,
    "presentationMeshesPointerInertInOverview": True,
    "preferredControlCssPixels": 48,
    "resetGestureStateOn": [
        "pointer-up",
        "pointer-cancel",
        "lost-pointer-capture",
        "viewport-change",
        "visibility-change",
    ],
    "sharedPickArbitrationRequired": True,
}
EXPECTED_MOTION = {
    "authoredAnimations": [],
    "continuousMotionRequired": False,
    "default": "static",
    "forbiddenClips": ["Attack", "Walk", "Death"],
    "independentAnimationLoops": 0,
    "mayEncodeGameplayState": False,
    "phaseSource": "engine-supplied-public-instance-key",
    "presentationOnly": True,
    "reducedMotion": "static",
    "scheduler": "existing-bounded-realm-scene-scheduler",
    "staticWhen": [
        "reduced-quality",
        "prefers-reduced-motion",
        "strategic-overview",
        "offscreen",
    ],
    "targets": [
        {"maxVerticalMeters": 0.03, "maxYawDegrees": 6, "node": "CoreWatcher_SuspendedCore"},
        {"maxVerticalMeters": 0.02, "maxYawDegrees": 4, "node": "CoreWatcher_FloatingShard_1"},
        {"maxVerticalMeters": 0.02, "maxYawDegrees": 4, "node": "CoreWatcher_FloatingShard_2"},
    ],
}
EXPECTED_FALLBACK = {
    "accessibleName": "Level 1 Core Watcher",
    "cameraNeutralInspect": True,
    "completeSemanticExploreListAlwaysAvailable": True,
    "engineGenerated": True,
    "fallbackShape": "bifurcated-spire-marker",
    "historyBackClosesInspectionBeforeLeavingRealm": True,
    "locateIsTheOnlyCameraMovingAction": True,
    "modelFailurePreservesPublicRecord": True,
    "opaqueIdentifiersExcludedFromDomAndAltText": True,
    "presentationArtDecorative": True,
    "preserveSelection": True,
    "required": True,
    "retryPolicy": "client-owned-bounded-no-retry-storm",
    "semanticDataSource": "engine-and-server-public-projection",
    "testMatrix": {
        "keyboardAndScreenReader": True,
        "pageZoomPercent": 200,
        "prefersReducedMotion": True,
        "safariIphone": {
            "pageScroll": True,
            "pinchZoom": True,
            "safeAreaInsets": True,
            "visualViewportResize": True,
        },
        "viewportCssPixels": [390, 844],
    },
}
EXPECTED_TELEMETRY = {
    "aggregateFields": [
        "public-records-visible",
        "semantic-markers-rendered",
        "models-rendered-by-profile",
        "instanced-draw-groups",
        "visible-triangles",
        "asset-bytes-loaded",
        "fallback-count",
        "context-loss-count",
        "bounded-retry-count",
    ],
    "clientTelemetryImplementedHere": False,
    "privateCoordinatesAllowed": False,
    "privateIdentifiersAllowed": False,
    "privateStateAllowedInAltTextOrDom": False,
    "privateWorldAtlasAllowed": False,
}
EXPECTED_FUTURE_SLICES = [
    {
        "implementedHere": False,
        "owner": "Warpkeep public catalogue and server placement authority",
        "slice": "B",
        "surface": (
            "public Core site identities, eligible cells, selected-world topology, "
            "hydrology, and visibility projection"
        ),
    },
    {
        "implementedHere": False,
        "owner": "Warpkeep Realm client",
        "slice": "C",
        "surface": (
            "content-addressed loading, markers, LOD allocation, instancing, picking, "
            "mobile gestures, fallback, and accessibility"
        ),
    },
    {
        "implementedHere": False,
        "owner": "SpacetimeDB and authoritative Realm UI",
        "slice": "D",
        "surface": (
            "encounter state, combat, health, damage, actions, rewards, cooldowns, "
            "and persistence"
        ),
    },
    {
        "implementedHere": False,
        "owner": "Warpkeep QA and operators",
        "slice": "E",
        "surface": "desktop and mobile budgets, migrations, observability, recovery, and rollout evidence",
    },
    {
        "implementedHere": False,
        "owner": "Warpkeep owner",
        "slice": "F",
        "surface": "fail-closed activation and staged rollout",
    },
]
EXPECTED_BOUNDS = {
    "LOD0_High": {
        "min": [-0.7993891586294642, 0.0, -0.7494720541633232],
        "max": [0.855703592300415, 2.14163864938768, 0.8585932850837708],
        "size": [1.6550927509298794, 2.14163864938768, 1.6080653392470938],
    },
    "LOD1_Balanced": {
        "min": [-0.7993891586294642, 0.0, -0.7494720541633232],
        "max": [0.7317647502528593, 2.142855711951041, 0.7091407179832458],
        "size": [1.5311539088823234, 2.142855711951041, 1.458612772146569],
    },
    "LOD2_Compact": {
        "min": [-0.7993891586294642, 0.0, -0.6200000047683716],
        "max": [0.7317647502528593, 2.1436644242985894, 0.7091407179832458],
        "size": [1.5311539088823234, 2.1436644242985894, 1.3291407227516174],
    },
    "LOD3_Map": {
        "min": [-0.7870411055325282, 0.0, -0.6200000047683716],
        "max": [0.6449754041834016, 2.1446314543004137, 0.7091407179832458],
        "size": [1.4320165097159299, 2.1446314543004137, 1.3291407227516174],
    },
}
EXPECTED_ROOTS = {
    "LOD0_High": "Warpkeep_CoreWatcher_Level1_LOD0_High",
    "LOD1_Balanced": "Warpkeep_CoreWatcher_Level1_LOD1_Balanced",
    "LOD2_Compact": "Warpkeep_CoreWatcher_Level1_LOD2_Compact",
    "LOD3_Map": "Warpkeep_CoreWatcher_Level1_LOD3_Map",
}
EXPECTED_PART_NODES = {
    "LOD0_High": [
        "CoreWatcher_BifurcatedBody_Left", "CoreWatcher_BifurcatedBody_Right",
        "CoreWatcher_CoreCage_1", "CoreWatcher_CoreCage_2",
        "CoreWatcher_CrownRib_Left", "CoreWatcher_CrownRib_Right",
        "CoreWatcher_FloatingShard_1", "CoreWatcher_FloatingShard_2",
        "CoreWatcher_FloatingShard_3", "CoreWatcher_Footprint",
        "CoreWatcher_GroundFracture_1", "CoreWatcher_GroundFracture_2",
        "CoreWatcher_GroundFracture_3", "CoreWatcher_GroundFracture_4",
        "CoreWatcher_GroundFracture_5", "CoreWatcher_GroundFracture_6",
        "CoreWatcher_GroundFracture_7", "CoreWatcher_GroundShard_1",
        "CoreWatcher_GroundShard_2", "CoreWatcher_GroundShard_3",
        "CoreWatcher_GroundShard_4", "CoreWatcher_LowerPedestal",
        "CoreWatcher_SuspendedCore",
    ],
    "LOD1_Balanced": [
        "CoreWatcher_BifurcatedBody_Left", "CoreWatcher_BifurcatedBody_Right",
        "CoreWatcher_CoreCage_1", "CoreWatcher_CoreCage_2",
        "CoreWatcher_CrownRib_Left", "CoreWatcher_CrownRib_Right",
        "CoreWatcher_FloatingShard_1", "CoreWatcher_FloatingShard_2",
        "CoreWatcher_FloatingShard_3", "CoreWatcher_Footprint",
        "CoreWatcher_GroundFracture_1", "CoreWatcher_GroundFracture_2",
        "CoreWatcher_GroundFracture_3", "CoreWatcher_GroundFracture_4",
        "CoreWatcher_GroundFracture_5", "CoreWatcher_GroundShard_1",
        "CoreWatcher_GroundShard_2", "CoreWatcher_GroundShard_3",
        "CoreWatcher_LowerPedestal", "CoreWatcher_SuspendedCore",
    ],
    "LOD2_Compact": [
        "CoreWatcher_BifurcatedBody_Left", "CoreWatcher_BifurcatedBody_Right",
        "CoreWatcher_CoreCage_1", "CoreWatcher_CrownRib_Left",
        "CoreWatcher_CrownRib_Right", "CoreWatcher_FloatingShard_1",
        "CoreWatcher_FloatingShard_2", "CoreWatcher_Footprint",
        "CoreWatcher_GroundFracture_1", "CoreWatcher_GroundFracture_2",
        "CoreWatcher_GroundFracture_3", "CoreWatcher_GroundShard_1",
        "CoreWatcher_GroundShard_2", "CoreWatcher_LowerPedestal",
        "CoreWatcher_SuspendedCore",
    ],
    "LOD3_Map": [
        "CoreWatcher_BifurcatedBody_Left", "CoreWatcher_BifurcatedBody_Right",
        "CoreWatcher_CrownRib_Left", "CoreWatcher_CrownRib_Right",
        "CoreWatcher_FloatingShard_1", "CoreWatcher_FloatingShard_2",
        "CoreWatcher_Footprint", "CoreWatcher_GroundFracture_1",
        "CoreWatcher_GroundFracture_2", "CoreWatcher_GroundShard_1",
        "CoreWatcher_LowerPedestal", "CoreWatcher_SuspendedCore",
    ],
}


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _load_json(payload: bytes, label: str) -> dict:
    try:
        document = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid UTF-8 JSON: {label}") from exc
    if not isinstance(document, dict):
        raise ValueError(f"JSON root must be an object: {label}")

    def finite(value: object) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"non-finite JSON number: {label}")
        if isinstance(value, dict):
            for child in value.values():
                finite(child)
        elif isinstance(value, list):
            for child in value:
                finite(child)

    finite(document)
    return document


def _strict_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            _strict_equal(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _strict_equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def _expect(actual: object, expected: object, label: str) -> None:
    if not _strict_equal(actual, expected):
        raise ValueError(f"unexpected {label}")


def _exact_keys(value: object, keys: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"unexpected field set in {label}")
    return value


def _safe_relative(value: object) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("unsafe tracked path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("unsafe tracked path")
    return Path(*path.parts)


def _regular_file_bytes(
    root: Path,
    relative: Path,
    label: str,
    *,
    expected_bytes: int | None = None,
    max_bytes: int,
) -> bytes:
    target = root / relative
    try:
        resolved = target.resolve(strict=True)
        resolved.relative_to(root)
        metadata = target.lstat()
        mode = metadata.st_mode
    except (OSError, ValueError) as exc:
        raise ValueError(f"missing or escaping tracked file: {relative.as_posix()}") from exc
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise ValueError(f"tracked file must be a regular non-symlink: {relative.as_posix()}")
    if metadata.st_size > max_bytes:
        raise ValueError(f"tracked file exceeds pre-read size limit: {label}")
    if expected_bytes is not None and metadata.st_size != expected_bytes:
        raise ValueError(f"tracked byte count mismatch: {label}")
    payload = target.read_bytes()
    if len(payload) != metadata.st_size:
        raise ValueError(f"tracked file changed while reading: {label}")
    return payload


def _tracked_bytes(root: Path, record: dict, label: str) -> bytes:
    _exact_keys(record, {"bytes", "sha256", "trackedPath"}, label)
    declared_bytes = record["bytes"]
    if type(declared_bytes) is not int or not 0 < declared_bytes <= MAX_TRACKED_JSON_BYTES:
        raise ValueError(f"invalid tracked byte count: {label}")
    relative = _safe_relative(record["trackedPath"])
    payload = _regular_file_bytes(
        root,
        relative,
        label,
        expected_bytes=declared_bytes,
        max_bytes=MAX_TRACKED_JSON_BYTES,
    )
    digest = record["sha256"]
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise ValueError(f"invalid tracked SHA-256: {label}")
    if hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError(f"tracked SHA-256 mismatch: {label}")
    return payload


def _package_verifier():
    # --root is untrusted verification data. Never import Python from it.
    path = Path(__file__).resolve().with_name("verify_core_watcher_level1.py")
    spec = importlib.util.spec_from_file_location("_core_watcher_package_verifier", path)
    if spec is None or spec.loader is None:
        raise ValueError("unable to load Core Watcher package verifier")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _verify_digest(raw: bytes, profile: dict) -> str:
    digest = _exact_keys(
        profile.get("contractDigest"),
        {"algorithm", "canonicalization", "sha256"},
        "contractDigest",
    )
    _expect(digest["algorithm"], "sha256", "contract digest algorithm")
    _expect(digest["canonicalization"], CANONICALIZATION, "canonicalization")
    declared = digest["sha256"]
    if not isinstance(declared, str) or not SHA256_RE.fullmatch(declared):
        raise ValueError("invalid contract digest")
    token = declared.encode("ascii")
    if raw.count(token) != 1:
        raise ValueError("contract digest must occur exactly once")
    actual = hashlib.sha256(raw.replace(token, ZERO_DIGEST.encode("ascii"))).hexdigest()
    if actual != declared:
        raise ValueError("contract digest mismatch")
    if declared != EXPECTED_PROFILE_DIGEST:
        raise ValueError("integration profile digest is not the production-pinned digest")
    return declared


def _verify_bindings(root: Path, profile: dict) -> tuple[dict, dict]:
    binding = _exact_keys(
        profile.get("assetBinding"),
        {
            "archive", "gallery", "packageRoot", "releaseManifest",
            "runtimeManifest", "sourceManifest", "sourceSemanticFingerprintSha256",
        },
        "assetBinding",
    )
    archive = _exact_keys(binding["archive"], {"bytes", "entries", "name", "sha256"}, "archive binding")
    _expect(
        archive,
        {
            "bytes": 1405757,
            "entries": 15,
            "name": "warpkeep-core-watcher-level1-game-ready-2026-08-03-v1.zip",
            "sha256": "34c8a80186642659acea893c06199a8e7b615ac0f9685f2c58c4a27641f56a33",
        },
        "archive binding",
    )
    _expect(binding["packageRoot"], "Warpkeep_CoreWatcher_Level1_GameReady", "package root")
    _expect(
        binding["sourceSemanticFingerprintSha256"],
        "a51eae5665ee3e7c59191b36dd1abfbbc1fa3ddd76405bee52c6c5fb3dad344c",
        "source semantic fingerprint",
    )

    _expect(binding["releaseManifest"], EXPECTED_RELEASE_BINDING, "release manifest binding")
    _expect(binding["gallery"], EXPECTED_GALLERY_BINDING, "gallery binding")
    _expect(binding["runtimeManifest"], EXPECTED_RUNTIME_BINDING, "runtime manifest binding")
    _expect(binding["sourceManifest"], EXPECTED_SOURCE_BINDING, "source manifest binding")

    release_payload = _tracked_bytes(root, binding["releaseManifest"], "release manifest binding")
    gallery_payload = _tracked_bytes(root, binding["gallery"], "gallery binding")
    source_payload = _tracked_bytes(root, binding["sourceManifest"], "source manifest binding")
    release = _load_json(release_payload, RELEASE_MANIFEST_PATH.as_posix())
    gallery = _load_json(gallery_payload, GALLERY_PATH.as_posix())
    source = _load_json(source_payload, EXPECTED_SOURCE_BINDING["trackedPath"])
    sanitization = source.get("sanitization")
    if not isinstance(sanitization, dict):
        raise ValueError("source manifest sanitization record is missing")
    _expect(
        sanitization.get("sourceSemanticFingerprintSha256"),
        binding["sourceSemanticFingerprintSha256"],
        "source-manifest semantic fingerprint",
    )

    runtime_binding = _exact_keys(
        binding["runtimeManifest"],
        {"bytes", "packagePath", "sha256", "trackedPath"},
        "runtime manifest binding",
    )
    _expect(runtime_binding["trackedPath"], RUNTIME_PATH.as_posix(), "runtime tracked path")
    runtime_payload = _regular_file_bytes(
        root,
        _safe_relative(runtime_binding["trackedPath"]),
        "runtime manifest",
        expected_bytes=runtime_binding["bytes"],
        max_bytes=MAX_TRACKED_JSON_BYTES,
    )
    if len(runtime_payload) != runtime_binding["bytes"]:
        raise ValueError("runtime manifest byte count mismatch")
    if hashlib.sha256(runtime_payload).hexdigest() != runtime_binding["sha256"]:
        raise ValueError("runtime manifest SHA-256 mismatch")

    attachments = release.get("attachments")
    if not isinstance(attachments, list) or len(attachments) != 1:
        raise ValueError("release manifest must contain one attachment")
    attachment = attachments[0]
    if not isinstance(attachment, dict):
        raise ValueError("release attachment record must be an object")
    for key in ("bytes", "name", "sha256", "packageRoot"):
        _expect(attachment.get(key), archive[key] if key != "packageRoot" else binding["packageRoot"], f"release {key}")
    entries = attachment.get("entries")
    if not isinstance(entries, list) or len(entries) != archive["entries"]:
        raise ValueError("release entry count mismatch")
    if any(not isinstance(item, dict) for item in entries):
        raise ValueError("release entries must be objects")
    entry = next((item for item in entries if item.get("path") == runtime_binding["packagePath"]), None)
    if not isinstance(entry, dict):
        raise ValueError("runtime manifest release entry missing")
    _expect(entry.get("bytes"), runtime_binding["bytes"], "runtime release bytes")
    _expect(entry.get("sha256"), runtime_binding["sha256"], "runtime release SHA-256")
    return _load_json(runtime_payload, RUNTIME_PATH.as_posix()), {"release": release, "gallery": gallery, "entries": entries}


def _verify_profiles(profile: dict, runtime: dict) -> list[dict]:
    records = profile.get("profiles")
    lods = runtime.get("lods")
    if not isinstance(records, list) or len(records) != 4 or not isinstance(lods, list) or len(lods) != 4:
        raise ValueError("exactly four integration profiles and runtime LODs are required")
    profile_keys = {
        "boundsGltfMeters", "bytes", "drawCalls", "embeddedBufferBytes", "file",
        "id", "materials", "meshes", "nodes", "onePrimitivePerMesh", "partNodes",
        "primitives", "rootNode", "sha256", "tier", "triangles", "uploadedVertices",
    }
    ids = ["high", "balanced", "compact", "map"]
    metric_keys = {
        "bytes", "embeddedBufferBytes", "file", "materials", "meshes", "nodes",
        "primitives", "sha256", "tier", "triangles", "uploadedVertices",
    }
    for record, lod, expected_id in zip(records, lods, ids):
        _exact_keys(record, profile_keys, f"profile {expected_id}")
        if not isinstance(lod, dict):
            raise ValueError(f"runtime LOD {expected_id} must be an object")
        _expect(record["id"], expected_id, f"profile id {expected_id}")
        for key in metric_keys:
            _expect(record[key], lod.get(key), f"{record['tier']} {key}")
        tier = record["tier"]
        _expect(record["boundsGltfMeters"], EXPECTED_BOUNDS[tier], f"{tier} emitted bounds")
        _expect(record["rootNode"], EXPECTED_ROOTS[tier], f"{tier} root node")
        _expect(record["partNodes"], EXPECTED_PART_NODES[tier], f"{tier} part nodes")
        if record["onePrimitivePerMesh"] is not True or not (
            record["drawCalls"] == record["primitives"] == record["meshes"] == len(record["partNodes"])
        ):
            raise ValueError(f"{tier} draw/mesh/semantic-part contract mismatch")
    return records


def _verify_previews(root: Path, profile: dict, evidence: dict) -> None:
    presentation = _exact_keys(
        profile.get("presentation"),
        {"description", "levelLabel", "packageReviewArt", "previews", "shortLabel", "uiSemanticsComeFromEngine"},
        "presentation",
    )
    _expect(
        {
            "description": presentation["description"],
            "levelLabel": presentation["levelLabel"],
            "shortLabel": presentation["shortLabel"],
            "uiSemanticsComeFromEngine": presentation["uiSemanticsComeFromEngine"],
        },
        {
            "description": (
                "A dormant Core Watcher presentation. Realm state and actions "
                "remain server-authoritative."
            ),
            "levelLabel": "Level 1",
            "shortLabel": "Watcher",
            "uiSemanticsComeFromEngine": True,
        },
        "presentation semantics",
    )
    if presentation["uiSemanticsComeFromEngine"] is not True:
        raise ValueError("presentation semantics must come from the engine")
    previews = presentation["previews"]
    if not isinstance(previews, list) or len(previews) != 3:
        raise ValueError("exactly three tracked previews are required")
    verifier = _package_verifier()
    gallery_records = evidence["gallery"].get("images")
    if not isinstance(gallery_records, list) or len(gallery_records) != 3:
        raise ValueError("gallery must contain exactly three images")
    for record, gallery_record in zip(previews, gallery_records):
        _exact_keys(record, {"bytes", "decorative", "height", "path", "runtimeUse", "sha256", "width"}, "preview")
        if not isinstance(gallery_record, dict):
            raise ValueError("gallery preview record must be an object")
        if record["runtimeUse"] is not False or record["decorative"] is not True:
            raise ValueError("review previews must remain decorative and runtime-disabled")
        preview_bytes = record["bytes"]
        if type(preview_bytes) is not int or not 0 < preview_bytes <= MAX_PREVIEW_BYTES:
            raise ValueError("invalid preview byte count")
        payload = _regular_file_bytes(
            root,
            _safe_relative(record["path"]),
            "preview",
            expected_bytes=preview_bytes,
            max_bytes=MAX_PREVIEW_BYTES,
        )
        if len(payload) != record["bytes"] or hashlib.sha256(payload).hexdigest() != record["sha256"]:
            raise ValueError("preview bytes or SHA-256 mismatch")
        dimensions = (
            verifier._png_dimensions(payload, record["path"])
            if record["path"].endswith(".png")
            else verifier._jpeg_dimensions(payload, record["path"])
        )
        _expect(list(dimensions), [record["width"], record["height"]], "preview dimensions")
        _expect(gallery_record.get("bytes"), record["bytes"], "gallery preview bytes")
        _expect(gallery_record.get("sha256"), record["sha256"], "gallery preview SHA-256")

    art = _exact_keys(
        presentation["packageReviewArt"],
        {"bytes", "decorative", "height", "packagePath", "runtimeUse", "sha256", "width"},
        "package review art",
    )
    _expect(
        art,
        {
            "bytes": 580483,
            "decorative": True,
            "height": 1600,
            "packagePath": (
                "Warpkeep_CoreWatcher_Level1_GameReady/Previews/"
                "Warpkeep_CoreWatcher_Level1_Transparent_1600.png"
            ),
            "runtimeUse": False,
            "sha256": "bc20fa28239d8008b79f182509363a81b2bef6705fdf8436786ca70567e2cf9a",
            "width": 1600,
        },
        "package review art",
    )
    if art["runtimeUse"] is not False or art["decorative"] is not True:
        raise ValueError("package review art must remain decorative and runtime-disabled")
    entry = next((item for item in evidence["entries"] if item.get("path") == art["packagePath"]), None)
    if not isinstance(entry, dict) or entry.get("bytes") != art["bytes"] or entry.get("sha256") != art["sha256"]:
        raise ValueError("package review art release binding mismatch")


def _verify_policies(profile: dict, records: list[dict]) -> None:
    _expect(profile.get("status"), EXPECTED_STATUS, "status gates")
    _expect(profile.get("authorityBoundary"), EXPECTED_AUTHORITY, "authority boundary")
    _expect(profile.get("loading"), EXPECTED_LOADING, "loading policy")
    _expect(profile.get("qualityCamera"), EXPECTED_QUALITY, "quality/camera policy")
    _expect(profile.get("selectionAndGestures"), EXPECTED_SELECTION, "selection and gesture policy")

    geometry = _exact_keys(
        profile.get("geometry"),
        {"frontAxis", "nativeScaleMetersPerUnit", "pivot", "renderGeometryIsCollision", "renderGeometryIsPicking", "selectionHint", "units", "upAxis"},
        "geometry",
    )
    _expect(
        geometry,
        {
            "frontAxis": "+Z", "nativeScaleMetersPerUnit": 1.0,
            "pivot": "footprint-center-ground", "renderGeometryIsCollision": False,
            "renderGeometryIsPicking": False,
            "selectionHint": {
                "centerYMeters": 1.275, "engineOwned": True, "heightMeters": 2.55,
                "presentationFootprintRadiusMeters": 0.9,
                "packageSuggestedRadiusMeters": 0.72, "shape": "cylinder",
            },
            "units": "meters", "upAxis": "+Y",
        },
        "geometry contract",
    )
    identity = profile.get("identity")
    _expect(
        identity,
        {
            "accessibleName": "Level 1 Core Watcher",
            "assetId": "warpkeep.encounters.core.watcher.level1",
            "combatEnabled": False, "displayName": "Core Watcher", "encounterLevel": 1,
            "enemyKind": "core-watcher", "faction": "The Core",
            "revision": "genesis-001-core-watcher-level1-2026-08-03",
            "statePresentation": "dormant-presence",
        },
        "identity",
    )

    instancing = _exact_keys(
        profile.get("instancing"),
        {"capacityEvidence", "eligible", "gameplayStatePerRenderInstance", "onePrimitivePerMesh", "selectedHighDetailMaxInstances", "staticRigid", "strategy"},
        "instancing",
    )
    for key, expected in (
        ("eligible", True), ("gameplayStatePerRenderInstance", False),
        ("onePrimitivePerMesh", True), ("selectedHighDetailMaxInstances", 1),
        ("staticRigid", True), ("strategy", "per-semantic-mesh"),
    ):
        _expect(instancing[key], expected, f"instancing {key}")
    capacity = _exact_keys(
        instancing["capacityEvidence"],
        {"declaresPopulation", "mapProfileInstancedDrawGroups", "mapProfileNaiveCloneDrawCalls", "mapProfileVisibleTriangles", "nonAuthoritativeTestInstances"},
        "capacity evidence",
    )
    count = capacity["nonAuthoritativeTestInstances"]
    map_profile = records[-1]
    if type(count) is not int or count != 72 or capacity["declaresPopulation"] is not False:
        raise ValueError("capacity evidence must remain a non-authoritative 72-instance test")
    if (
        capacity["mapProfileVisibleTriangles"] != count * map_profile["triangles"]
        or capacity["mapProfileNaiveCloneDrawCalls"] != count * map_profile["drawCalls"]
        or capacity["mapProfileInstancedDrawGroups"] != map_profile["drawCalls"]
    ):
        raise ValueError("capacity evidence math mismatch")

    motion = profile.get("motion")
    _expect(motion, EXPECTED_MOTION, "motion policy")
    targets = motion["targets"]
    if not isinstance(targets, list) or len(targets) != 3:
        raise ValueError("motion targets mismatch")
    target_names = [target.get("node") for target in targets if isinstance(target, dict)]
    if len(target_names) != 3 or any(
        name not in record["partNodes"] for name in target_names for record in records
    ):
        raise ValueError("motion target is not stable across every LOD")

    _expect(
        profile.get("fallbackAndAccessibility"),
        EXPECTED_FALLBACK,
        "fallback/accessibility policy",
    )
    _expect(
        profile.get("telemetryAndPrivacy"),
        EXPECTED_TELEMETRY,
        "telemetry/privacy boundary",
    )
    _expect(
        profile.get("futureGameplaySlices"),
        EXPECTED_FUTURE_SLICES,
        "future gameplay slices",
    )


def verify(root: Path | str) -> str:
    repository = Path(root).resolve()
    raw = _regular_file_bytes(
        repository,
        PROFILE_PATH,
        "integration profile",
        max_bytes=MAX_PROFILE_BYTES,
    )
    profile = _load_json(raw, PROFILE_PATH.as_posix())
    _exact_keys(profile, ROOT_KEYS, "integration profile")
    _expect(profile["schema"], "warpkeep.asset-integration-profile.v1", "profile schema")
    _expect(profile["version"], "1.0.0", "profile version")
    digest = _verify_digest(raw, profile)
    runtime, evidence = _verify_bindings(repository, profile)
    records = _verify_profiles(profile, runtime)
    _verify_previews(repository, profile, evidence)
    _verify_policies(profile, records)

    forbidden = (b"/Users/", b"/home/", b"/var/folders/", b"/tmp/")
    if any(token in raw for token in forbidden):
        raise ValueError("private path found in integration profile")
    return digest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the tracked Core Watcher review-only integration profile."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Warpkeep-Assets repository root (defaults to this checkout)",
    )
    args = parser.parse_args()
    try:
        digest = verify(args.root)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Core Watcher integration-profile verification failed: {exc}\n")
    print(
        "Verified review-only Core Watcher integration profile "
        f"{digest}; no runtime, gameplay, release, or activation authority."
    )


if __name__ == "__main__":
    main()
