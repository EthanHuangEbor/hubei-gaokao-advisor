from __future__ import annotations

from collections import Counter
from pathlib import Path

from services.crawler.adapters.static_csv_adapter import StaticCsvHubeiFixtureAdapter
from services.recommender.admission_risk_model import HubeiAdmissionRiskModel
from services.recommender.models import CandidateProfile
from services.recommender.same_rank_reference_builder import SameRankReferenceBuilder
from services.recommender.volunteer_plan_builder import VolunteerPlanBuilder


def run_fixture_backtest(fixture_dir: Path) -> dict[str, object]:
    adapter = StaticCsvHubeiFixtureAdapter(fixture_dir)
    dataset = adapter.load()
    ranks = [12000, 22000, 36000, 52000]
    model = HubeiAdmissionRiskModel()
    reference_builder = SameRankReferenceBuilder()
    plan_builder = VolunteerPlanBuilder()
    tier_counter: Counter[str] = Counter()
    total_items = 0
    for first_subject in ["physics", "history"]:
        for rank in ranks:
            candidate = CandidateProfile(
                year=2026,
                province="湖北",
                first_subject=first_subject,  # type: ignore[arg-type]
                second_subjects=("chemistry", "biology"),
                score=600 if first_subject == "physics" else 570,
                rank=rank,
                preferences={
                    "accept_private_college": True,
                    "accept_sino_foreign": True,
                    "max_tuition": 60000,
                    "priority_strategy": "balanced",
                },
            )
            refs = reference_builder.build(
                target_year=2026,
                candidate_rank=rank,
                province="湖北",
                first_subject=first_subject,
                batch="本科普通批",
                records=dataset.admission_records,
            )
            items = model.recommend(candidate, dataset.admission_records, dataset.admission_plans, refs)
            run = plan_builder.build(run_id=f"backtest-{first_subject}-{rank}", candidate=candidate, items=items)
            tier_counter.update(item.tier for item in run.items)
            total_items += len(run.items)
    return {
        "sample_count": len(ranks) * 2,
        "recommendation_items": total_items,
        "tier_counts": dict(tier_counter),
        "data_missing_rate": 0.0 if total_items else 1.0,
        "note": "Fixture backtest validates pipeline shape only; official 2025 replay requires audited public data.",
    }


def write_backtest_report(fixture_dir: Path, output: Path) -> dict[str, object]:
    result = run_fixture_backtest(fixture_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "# Backtest Report\n\n"
        "当前报告使用虚构湖北 fixtures 验证回测流程，不宣称真实准确率。\n\n"
        f"- sample_count: {result['sample_count']}\n"
        f"- recommendation_items: {result['recommendation_items']}\n"
        f"- tier_counts: {result['tier_counts']}\n"
        f"- data_missing_rate: {result['data_missing_rate']}\n\n"
        "真实 2025 回测必须在官方公开投档线和计划数据通过质量审计后运行。\n",
        encoding="utf-8",
    )
    return result

