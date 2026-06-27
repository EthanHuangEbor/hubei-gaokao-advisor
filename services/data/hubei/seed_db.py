from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.data.hubei.curated_loader import load_curated_dataset


def seed_db(*, curated_dir: Path) -> dict[str, object]:
    """Validate curated rows and return seed counts for the database seed command."""

    dataset = load_curated_dataset(curated_dir)
    return {
        "status": "validated_curated_seed",
        "admission_records": len(dataset.admission_records),
        "rank_segments": len(dataset.rank_segments),
        "admission_plans": len(dataset.admission_plans),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and seed Hubei curated CSVs")
    parser.add_argument("--curated-dir", type=Path, default=Path("data/curated/hubei"))
    args = parser.parse_args()
    print(json.dumps(seed_db(curated_dir=args.curated_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
