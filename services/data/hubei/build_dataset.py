from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.crawler.adapters.static_csv_adapter import StaticCsvHubeiFixtureAdapter
from services.data.hubei.downloader import download_sources
from services.data.hubei.parsers.admission_lines import parse_csv as parse_admission_lines_csv
from services.data.hubei.parsers.plans import parse_csv as parse_plans_csv
from services.data.hubei.parsers.rank_segments import parse_csv as parse_rank_segments_csv
from services.data.hubei.promote import OUTPUT_FILES, candidate_eligible_counts, promote_candidates
from services.data.hubei.quality import REQUIRED_PROVENANCE_FIELDS, run_quality_checks
from services.data.hubei.source_registry import HubeiSource, load_source_registry

PARSER_VERSION = "curated-fixture-seed-v0.2"
REAL_CANDIDATE_DIRNAME = "hubei_real"
GENERATED_CANDIDATE_DIRNAME = "generated"


@dataclass(frozen=True)
class HubeiBuildResult:
    curated_records: int
    curated_rank_segments: int
    curated_plans: int
    curated_dir: Path
    quality_dir: Path

    def to_dict(self) -> dict[str, object]:
        return {
            "curated_records": self.curated_records,
            "curated_rank_segments": self.curated_rank_segments,
            "curated_plans": self.curated_plans,
            "curated_dir": str(self.curated_dir),
            "quality_dir": str(self.quality_dir),
        }


def build_dataset(
    *,
    root: Path,
    output_root: Path | None = None,
    download: bool = False,
    parse: bool = False,
    quality: bool = False,
    promote: bool = False,
) -> HubeiBuildResult:
    """Build v0.2 curated seed data plus reviewed real candidate hooks."""

    base = output_root or root
    raw_dir = base / "data" / "raw" / "hubei"
    candidate_dir = base / "data" / "candidate" / "hubei"
    real_candidate_dir = base / "data" / "candidate" / REAL_CANDIDATE_DIRNAME
    curated_dir = base / "data" / "curated" / "hubei"
    quality_dir = base / "data" / "quality" / "hubei"
    for layer_dir in [
        raw_dir / "admission_lines",
        raw_dir / "rank_segments",
        raw_dir / "plans",
        candidate_dir / "admission_lines",
        candidate_dir / "rank_segments",
        candidate_dir / "plans",
        real_candidate_dir / "admission_lines",
        real_candidate_dir / "rank_segments",
        real_candidate_dir / "plans",
        curated_dir,
        quality_dir,
    ]:
        layer_dir.mkdir(parents=True, exist_ok=True)

    dataset = StaticCsvHubeiFixtureAdapter(root / "data" / "fixtures" / "hubei").load()
    registry_path = root / "data" / "source_registry" / "hubei_sources.yaml"

    if download:
        if registry_path.exists():
            download_result = download_sources(registry_path=registry_path, raw_root=raw_dir)
            _write_json(
                raw_dir / "download_manifest.json",
                {
                    "status": "download_complete",
                    "downloaded_count": download_result.downloaded_count,
                    "skipped_count": download_result.skipped_count,
                    "manifest_path": str(download_result.manifest_path),
                },
            )
        else:
            _write_json(
                raw_dir / "download_manifest.json",
                {
                    "status": "registry_missing_no_network_fetch",
                    "note": "raw official PDFs/images stay local or artifact-only; fixtures seed curated schema",
                },
            )

    real_candidate_rows = 0
    if parse or promote:
        _write_csv(
            candidate_dir / "admission_lines" / "candidate_admission_records_2023_2025.csv",
            _record_rows(dataset.admission_records, review_status="pending"),
        )
        _write_csv(
            candidate_dir / "rank_segments" / "candidate_rank_segments_2023_2026.csv",
            _rank_rows(dataset.rank_segments, review_status="pending"),
        )
        _write_csv(
            candidate_dir / "plans" / "candidate_admission_plans_2026.csv",
            _plan_rows(dataset.admission_plans, review_status="pending"),
        )
        real_candidate_rows = _stage_real_candidates(raw_dir, real_candidate_dir, registry_path)

    if promote or (not download and not parse and not quality):
        _write_csv(
            curated_dir / "admission_records_2023_2025.csv",
            _record_rows(dataset.admission_records, review_status="approved"),
        )
        _write_csv(
            curated_dir / "rank_segments_2023_2026.csv",
            _rank_rows(dataset.rank_segments, review_status="approved"),
        )
        _write_csv(
            curated_dir / "admission_plans_2026.csv",
            _plan_rows(dataset.admission_plans, review_status="approved"),
        )

    real_quality_report = None
    real_promotable_counts = {dataset_name: 0 for dataset_name, _ in OUTPUT_FILES.values()}
    real_promotion_status = "not_requested"
    if (quality or promote) and real_candidate_rows:
        real_quality_report = run_quality_checks(real_candidate_dir)
        real_promotable_counts = candidate_eligible_counts(real_candidate_dir)
        if real_quality_report.has_errors:
            real_promotion_status = "blocked_quality_errors"
            if promote:
                raise RuntimeError(
                    f"quality errors block promotion: {len(real_quality_report.errors)}"
                )
        elif promote:
            if _real_candidate_complete(real_promotable_counts):
                promote_candidates(real_candidate_dir, curated_dir)
                real_promotion_status = "promoted"
            else:
                real_promotion_status = "skipped_incomplete"
        else:
            real_promotion_status = "review_pending"
    elif promote:
        real_promotion_status = "skipped_no_real_candidates"

    if quality or promote:
        report = {
            "admission_records": len(dataset.admission_records),
            "rank_segments": len(dataset.rank_segments),
            "admission_plans": len(dataset.admission_plans),
            "real_candidate_rows": real_candidate_rows,
            "real_candidate_quality_errors": len(real_quality_report.errors) if real_quality_report else 0,
            "real_promotable_counts": real_promotable_counts,
            "real_promotion_status": real_promotion_status,
            "policy": "OCR candidates remain pending; only approved curated rows are runtime eligible.",
            "parser_version": PARSER_VERSION,
        }
        _write_json(quality_dir / "data_build_report.json", report)
        _write_markdown_report(quality_dir / "data_build_report.md", report)

    curated_counts = _curated_row_counts(curated_dir)
    return HubeiBuildResult(
        curated_records=curated_counts["admission_records"],
        curated_rank_segments=curated_counts["rank_segments"],
        curated_plans=curated_counts["admission_plans"],
        curated_dir=curated_dir,
        quality_dir=quality_dir,
    )


def _record_rows(records: list[Any], *, review_status: str) -> list[dict[str, object]]:
    return [
        {
            "year": record.year,
            "province": record.province,
            "batch": record.batch,
            "category": record.category,
            "first_subject": record.first_subject,
            "second_subject_requirement": record.second_subject_requirement,
            "university_code": record.university_code,
            "university_name": record.university_name,
            "major_group_code": record.major_group_code,
            "major_group_name": record.major_group_name,
            "admission_category": record.admission_category,
            "min_score": record.min_score,
            "min_rank": record.min_rank,
            "plan_seats": record.plan_seats or "",
            "remarks": "",
            **_metadata(record.source_id, record.source_url, record.confidence_score, review_status),
        }
        for record in records
    ]


def _rank_rows(segments: list[Any], *, review_status: str) -> list[dict[str, object]]:
    return [
        {
            "year": segment.year,
            "province": segment.province,
            "category": segment.category,
            "first_subject": segment.first_subject,
            "score": segment.score,
            "same_score_count": segment.same_score_count,
            "cumulative_rank": segment.cumulative_rank,
            "rank_start": segment.rank_start,
            "rank_end": segment.rank_end,
            **_metadata(segment.source_id, segment.source_url, segment.confidence_score, review_status),
        }
        for segment in segments
    ]


def _plan_rows(plans: list[Any], *, review_status: str) -> list[dict[str, object]]:
    return [
        {
            "year": plan.year,
            "province": plan.province,
            "batch": plan.batch,
            "category": plan.category,
            "first_subject": plan.first_subject,
            "second_subject_requirement": plan.second_subject_requirement,
            "university_code": plan.university_code,
            "university_name": plan.university_name,
            "major_group_code": plan.major_group_code,
            "major_group_name": plan.major_group_name,
            "major_code": plan.major_code,
            "major_name": plan.major_name,
            "plan_seats": plan.plan_seats,
            "tuition": plan.tuition,
            "schooling_years": plan.schooling_years,
            "campus": plan.campus,
            "is_sino_foreign": "true" if plan.is_sino_foreign else "false",
            "is_private": "true" if plan.is_private else "false",
            "notes": plan.notes,
            "physical_limit_note": plan.physical_limit_note,
            "single_subject_limit_note": plan.single_subject_limit_note,
            "limits": " ".join(
                note for note in [plan.physical_limit_note, plan.single_subject_limit_note] if note
            ),
            **_metadata(plan.source_id, plan.source_url, plan.confidence_score, review_status),
        }
        for plan in plans
    ]


def _metadata(
    source_id: str,
    source_url: str,
    confidence_score: float,
    review_status: str,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "source_url": source_url,
        "source_type": "fixture_seed",
        "raw_document_sha256": hashlib.sha256(f"{source_id}|{source_url}".encode()).hexdigest(),
        "parser_name": "static_csv_seed",
        "parser_version": PARSER_VERSION,
        "parse_confidence": confidence_score,
        "confidence_score": confidence_score,
        "license_note": "fixture seed mirrors public Hubei admissions schema; replace with reviewed official rows before production",
        "review_status": review_status,
        "reviewer": "system_seed",
    }


def _stage_real_candidates(raw_dir: Path, real_candidate_dir: Path, registry_path: Path) -> int:
    for subdir in ["admission_lines", "rank_segments", "plans"]:
        generated_dir = real_candidate_dir / subdir / GENERATED_CANDIDATE_DIRNAME
        generated_dir.mkdir(parents=True, exist_ok=True)
        for generated_candidate in generated_dir.glob("candidate_*.csv"):
            if generated_candidate.is_file():
                generated_candidate.unlink()

    sources = _load_sources_by_id(registry_path)
    staged_rows = 0
    for subdir, parser in _parser_map().items():
        generated_dir = real_candidate_dir / subdir / GENERATED_CANDIDATE_DIRNAME
        for raw_csv in sorted((raw_dir / subdir).glob("*.csv")):
            rows = _read_csv(raw_csv)
            if not rows:
                continue
            target = generated_dir / f"candidate_{raw_csv.name}"
            if _has_candidate_metadata(rows[0]):
                shutil.copyfile(raw_csv, target)
                staged_rows += len(rows)
                continue
            source = sources.get(raw_csv.stem)
            if source is None:
                continue
            parsed_rows = parser(
                raw_csv,
                source=source,
                raw_document_sha256=hashlib.sha256(raw_csv.read_bytes()).hexdigest(),
            )
            if parsed_rows:
                _write_csv(target, parsed_rows)
                staged_rows += len(parsed_rows)
    return staged_rows


def _parser_map() -> dict[str, Callable[..., list[dict[str, str]]]]:
    return {
        "admission_lines": parse_admission_lines_csv,
        "rank_segments": parse_rank_segments_csv,
        "plans": parse_plans_csv,
    }


def _load_sources_by_id(registry_path: Path) -> dict[str, HubeiSource]:
    if not registry_path.exists():
        return {}
    registry = load_source_registry(registry_path)
    return {source.source_id: source for source in registry.sources}


def _has_candidate_metadata(row: dict[str, str]) -> bool:
    return all(field in row for field in REQUIRED_PROVENANCE_FIELDS)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_markdown_report(path: Path, payload: dict[str, object]) -> None:
    lines = ["# Hubei v0.2 Data Build Report", ""]
    for key, value in payload.items():
        lines.append(f"- {key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _real_candidate_complete(promotable_counts: dict[str, int]) -> bool:
    return all(count > 0 for count in promotable_counts.values())


def _curated_row_counts(curated_dir: Path) -> dict[str, int]:
    return {
        dataset_name: _count_csv_rows(curated_dir / output_name)
        for dataset_name, output_name in OUTPUT_FILES.values()
    }


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8-sig", newline="") as file:
        return sum(1 for _ in csv.DictReader(file))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Hubei v0.2 curated data layers")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--parse", action="store_true")
    parser.add_argument("--quality", action="store_true")
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    result = build_dataset(
        root=args.root,
        output_root=args.output_root,
        download=args.download,
        parse=args.parse,
        quality=args.quality,
        promote=args.promote,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
