from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.crawler.adapters.static_csv_adapter import StaticCsvHubeiFixtureAdapter

PARSER_VERSION = "curated-fixture-seed-v0.2"


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
    """Build v0.2 curated seed data from reviewed local fixture rows."""

    base = output_root or root
    raw_dir = base / "data" / "raw" / "hubei"
    candidate_dir = base / "data" / "candidate" / "hubei"
    curated_dir = base / "data" / "curated" / "hubei"
    quality_dir = base / "data" / "quality" / "hubei"
    for layer_dir in [
        raw_dir / "admission_lines",
        raw_dir / "rank_segments",
        raw_dir / "plans",
        candidate_dir / "admission_lines",
        candidate_dir / "rank_segments",
        candidate_dir / "plans",
        curated_dir,
        quality_dir,
    ]:
        layer_dir.mkdir(parents=True, exist_ok=True)

    dataset = StaticCsvHubeiFixtureAdapter(root / "data" / "fixtures" / "hubei").load()

    if download:
        _write_json(
            raw_dir / "download_manifest.json",
            {
                "status": "registry_ready_no_network_fetch",
                "note": "raw official PDFs/images stay local or artifact-only; fixtures seed curated schema",
            },
        )

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

    if quality or promote:
        report = {
            "admission_records": len(dataset.admission_records),
            "rank_segments": len(dataset.rank_segments),
            "admission_plans": len(dataset.admission_plans),
            "policy": "OCR candidates remain pending; only approved curated rows are runtime eligible.",
            "parser_version": PARSER_VERSION,
        }
        _write_json(quality_dir / "data_build_report.json", report)
        _write_markdown_report(quality_dir / "data_build_report.md", report)

    return HubeiBuildResult(
        curated_records=len(dataset.admission_records),
        curated_rank_segments=len(dataset.rank_segments),
        curated_plans=len(dataset.admission_plans),
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
            "is_sino_foreign": "是" if plan.is_sino_foreign else "否",
            "is_private": "是" if plan.is_private else "否",
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


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
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
