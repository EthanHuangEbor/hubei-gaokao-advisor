from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.parse import urlparse
from urllib.request import urlopen

from services.data.hubei.source_registry import HubeiSource, load_source_registry

PUBLIC_DOWNLOAD_SOURCE_TYPES = {"official", "quasi_official", "official_public"}
ALLOWED_DOWNLOAD_SCHEMES = {"http", "https"}
ALLOWED_EXACT_HOSTS = {"hbksw.com", "www.hbksw.com"}
ALLOWED_HUBEI_GOV_HOST_SUFFIX = ".hubei.gov.cn"


@dataclass(frozen=True)
class DownloadResult:
    downloaded_count: int
    skipped_count: int
    manifest_path: Path


def download_sources(*, registry_path: str | Path, raw_root: str | Path) -> DownloadResult:
    registry = load_source_registry(registry_path)
    root = Path(raw_root)
    manifest_rows: list[dict[str, str]] = []
    subdir_manifest_rows: dict[str, list[dict[str, str]]] = {}
    skipped = 0

    for source in registry.sources:
        if not _is_public_download_source(source):
            skipped += 1
            continue
        payload = _read_url(source.source_url)
        raw_subdir = source.raw_subdir or source.data_type
        target_dir = root / raw_subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = _download_filename(source)
        target_path = target_dir / filename
        target_path.write_bytes(payload)
        manifest_row = {
            "source_id": source.source_id,
            "source_url": source.source_url,
            "raw_subdir": raw_subdir,
            "filename": filename,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": str(len(payload)),
            "status": "downloaded",
            "review_status": "pending",
        }
        manifest_rows.append(manifest_row)
        subdir_manifest_rows.setdefault(raw_subdir, []).append(manifest_row)

    for raw_subdir, subdir_rows in subdir_manifest_rows.items():
        _write_manifest(root / raw_subdir / "download_manifest.csv", subdir_rows)

    manifest_path = root / "download_manifest.csv"
    _write_manifest(manifest_path, manifest_rows)
    return DownloadResult(
        downloaded_count=len(manifest_rows),
        skipped_count=skipped,
        manifest_path=manifest_path,
    )


def _is_public_download_source(source: HubeiSource) -> bool:
    return (
        source.allow_network_download
        and source.source_type in PUBLIC_DOWNLOAD_SOURCE_TYPES
        and _is_allowed_download_url(source.source_url)
    )


def _is_allowed_download_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_DOWNLOAD_SCHEMES:
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    return host in ALLOWED_EXACT_HOSTS or host.endswith(ALLOWED_HUBEI_GOV_HOST_SUFFIX)


def _read_url(url: str) -> bytes:
    if not _is_allowed_download_url(url):
        raise ValueError(f"download URL is not an allowed official Hubei HTTP(S) source: {url}")
    with urlopen(url) as response:  # noqa: S310 - URL is validated against official HTTP(S) allowlist.
        return cast(bytes, response.read())


def _download_filename(source: HubeiSource) -> str:
    suffix = Path(urlparse(source.source_url).path).suffix or ".raw"
    safe_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in source.source_id)
    return f"{safe_id}{suffix}"


def _write_manifest(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_id",
        "source_url",
        "raw_subdir",
        "filename",
        "sha256",
        "bytes",
        "status",
        "review_status",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
