from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.crawler.adapters.static_csv_adapter import StaticCsvHubeiFixtureAdapter
from services.crawler.quality.hubei_quality_checks import run_quality_checks


def main() -> None:
    fixture_dir = ROOT / "data" / "fixtures" / "hubei"
    dataset = StaticCsvHubeiFixtureAdapter(fixture_dir).load()
    findings = run_quality_checks(dataset)
    print(
        {
            "admission_records": len(dataset.admission_records),
            "admission_plans": len(dataset.admission_plans),
            "rank_segments": len(dataset.rank_segments),
            "quality_findings": len(findings),
            "errors": len([item for item in findings if item.severity == "error"]),
        }
    )


if __name__ == "__main__":
    main()
