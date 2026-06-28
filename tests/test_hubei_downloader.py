from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from services.data.hubei.source_registry import load_source_registry


def test_source_registry_loads_pipeline_metadata(tmp_path: Path) -> None:
    registry_path = tmp_path / "sources.yaml"
    registry_path.write_text(
        """
version: 1
sources:
  - source_id: hubei_rank
    title: "Rank"
    source_url: "file:///tmp/rank.csv"
    source_type: "official"
    owner: "Hubei"
    data_type: "rank_segments"
    years: "2026"
    status: "verified"
    license_note: "public"
    parser: "rank_segments.csv"
    raw_subdir: "rank_segments"
    allow_network_download: true
    requires_manual_review: true
""",
        encoding="utf-8",
    )

    registry = load_source_registry(registry_path)

    source = registry.sources[0]
    assert source.parser == "rank_segments.csv"
    assert source.raw_subdir == "rank_segments"
    assert source.allow_network_download is True
    assert source.requires_manual_review is True


def test_downloader_fetches_only_public_official_sources_and_writes_manifests(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from services.data.hubei import downloader

    allowed_url = "https://www.hbksw.com/rank.csv"
    allowed_second_url = "https://jyt.hubei.gov.cn/rank-second.csv"
    payloads = {
        allowed_url: b"score,cumulative_rank\n650,1000\n",
        allowed_second_url: b"score,cumulative_rank\n640,2000\n",
    }
    requested_urls: list[str] = []

    def fake_read_url(url: str) -> bytes:
        requested_urls.append(url)
        return payloads[url]

    monkeypatch.setattr(downloader, "_read_url", fake_read_url)
    registry_path = tmp_path / "sources.yaml"
    registry_path.write_text(
        """
version: 1
sources:
  - source_id: allowed_rank
    title: "Allowed rank"
    source_url: "https://www.hbksw.com/rank.csv"
    source_type: "official"
    owner: "Hubei"
    data_type: "rank_segments"
    years: "2026"
    status: "verified"
    license_note: "public"
    parser: "rank_segments.csv"
    raw_subdir: "rank_segments"
    allow_network_download: true
    requires_manual_review: true
  - source_id: allowed_rank_second
    title: "Allowed rank second"
    source_url: "https://jyt.hubei.gov.cn/rank-second.csv"
    source_type: "official_public"
    owner: "Hubei"
    data_type: "rank_segments"
    years: "2026"
    status: "verified"
    license_note: "public"
    parser: "rank_segments.csv"
    raw_subdir: "rank_segments"
    allow_network_download: true
    requires_manual_review: true
  - source_id: blocked_platform
    title: "Blocked platform"
    source_url: "https://www.hbksw.com/platform.csv"
    source_type: "official_platform"
    owner: "Hubei"
    data_type: "platform"
    years: "2026"
    status: "registry_only"
    license_note: "manual only"
    parser: ""
    raw_subdir: "platform"
    allow_network_download: true
    requires_manual_review: true
  - source_id: blocked_vendor
    title: "Blocked vendor"
    source_url: "https://www.hbksw.com/vendor.csv"
    source_type: "vendor_docs"
    owner: "Vendor"
    data_type: "vendor"
    years: "2026"
    status: "registry_only"
    license_note: "manual only"
    parser: ""
    raw_subdir: "vendor"
    allow_network_download: true
    requires_manual_review: true
  - source_id: blocked_file
    title: "Blocked file"
    source_url: "file:///tmp/rank.csv"
    source_type: "official"
    owner: "Hubei"
    data_type: "rank_segments"
    years: "2026"
    status: "verified"
    license_note: "public"
    parser: "rank_segments.csv"
    raw_subdir: "rank_segments"
    allow_network_download: true
    requires_manual_review: true
  - source_id: blocked_internal
    title: "Blocked internal"
    source_url: "http://127.0.0.1/rank.csv"
    source_type: "official"
    owner: "Hubei"
    data_type: "rank_segments"
    years: "2026"
    status: "verified"
    license_note: "public"
    parser: "rank_segments.csv"
    raw_subdir: "rank_segments"
    allow_network_download: true
    requires_manual_review: true
  - source_id: blocked_unsupported
    title: "Blocked unsupported scheme"
    source_url: "ftp://www.hbksw.com/rank.csv"
    source_type: "official"
    owner: "Hubei"
    data_type: "rank_segments"
    years: "2026"
    status: "verified"
    license_note: "public"
    parser: "rank_segments.csv"
    raw_subdir: "rank_segments"
    allow_network_download: true
    requires_manual_review: true
""",
        encoding="utf-8",
    )

    raw_root = tmp_path / "data" / "raw" / "hubei"
    result = downloader.download_sources(
        registry_path=registry_path,
        raw_root=raw_root,
    )

    downloaded = raw_root / "rank_segments" / "allowed_rank.csv"
    downloaded_second = raw_root / "rank_segments" / "allowed_rank_second.csv"
    assert downloaded.read_bytes() == payloads[allowed_url]
    assert downloaded_second.read_bytes() == payloads[allowed_second_url]
    assert not (raw_root / "platform" / "blocked_platform.csv").exists()
    assert not (raw_root / "vendor" / "blocked_vendor.csv").exists()
    assert not (raw_root / "rank_segments" / "blocked_file.csv").exists()
    assert not (raw_root / "rank_segments" / "blocked_internal.csv").exists()
    assert not (raw_root / "rank_segments" / "blocked_unsupported.csv").exists()
    assert requested_urls == [allowed_url, allowed_second_url]
    assert result.downloaded_count == 2
    assert result.skipped_count == 5

    expected_rows = [
        {
            "source_id": "allowed_rank",
            "source_url": allowed_url,
            "raw_subdir": "rank_segments",
            "filename": "allowed_rank.csv",
            "sha256": hashlib.sha256(payloads[allowed_url]).hexdigest(),
            "bytes": str(len(payloads[allowed_url])),
            "status": "downloaded",
            "review_status": "pending",
        },
        {
            "source_id": "allowed_rank_second",
            "source_url": allowed_second_url,
            "raw_subdir": "rank_segments",
            "filename": "allowed_rank_second.csv",
            "sha256": hashlib.sha256(payloads[allowed_second_url]).hexdigest(),
            "bytes": str(len(payloads[allowed_second_url])),
            "status": "downloaded",
            "review_status": "pending",
        },
    ]

    with result.manifest_path.open(encoding="utf-8-sig", newline="") as file:
        root_rows = list(csv.DictReader(file))
    assert root_rows == expected_rows

    subdir_manifest_path = raw_root / "rank_segments" / "download_manifest.csv"
    with subdir_manifest_path.open(encoding="utf-8-sig", newline="") as file:
        subdir_rows = list(csv.DictReader(file))
    assert subdir_rows == expected_rows
    assert {row["sha256"] for row in subdir_rows} == {row["sha256"] for row in expected_rows}
    assert {row["review_status"] for row in subdir_rows} == {"pending"}
