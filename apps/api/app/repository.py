from __future__ import annotations

from pathlib import Path

from services.crawler.adapters.hubei.hubei_source_discovery import HubeiSourceDiscovery
from services.crawler.adapters.static_csv_adapter import (
    FixtureDataset,
    StaticCsvHubeiFixtureAdapter,
)
from services.data.hubei.authenticity import (
    DatasetAuthenticity,
    inspect_curated_dir,
    strict_real_data_required,
)
from services.data.hubei.curated_loader import load_curated_dataset
from services.data.hubei.source_registry import load_source_registry


class Repository:
    def __init__(self, root: Path):
        self.root = root
        self.fixture_dir = root / "data" / "fixtures" / "hubei"
        self.curated_dir = root / "data" / "curated" / "hubei"
        self.source_registry_path = root / "data" / "source_registry" / "hubei_sources.yaml"
        self.source_discovery = HubeiSourceDiscovery()
        self.dataset_status: DatasetAuthenticity = inspect_curated_dir(self.curated_dir)
        self.dataset: FixtureDataset = self._load_dataset()

    def reload(self) -> FixtureDataset:
        self.dataset = self._load_dataset()
        return self.dataset

    def sources(self) -> list[dict[str, object]]:
        if self.source_registry_path.exists():
            registry = load_source_registry(self.source_registry_path)
            return [source.__dict__ for source in registry.sources]
        return [source.__dict__ for source in self.source_discovery.seed_registry()]

    def _load_dataset(self) -> FixtureDataset:
        self.dataset_status = inspect_curated_dir(self.curated_dir)
        strict_required = strict_real_data_required()
        if strict_required and not self.dataset_status.real_curated_ready:
            return self._empty_dataset()
        if self._curated_ready():
            try:
                return load_curated_dataset(self.curated_dir)
            except ValueError:
                if strict_required:
                    return self._empty_dataset()
                raise
        return StaticCsvHubeiFixtureAdapter(self.fixture_dir).load()

    def _curated_ready(self) -> bool:
        return all(
            (self.curated_dir / name).exists()
            for name in [
                "admission_records_2023_2025.csv",
                "rank_segments_2023_2026.csv",
                "admission_plans_2026.csv",
            ]
        )

    def _empty_dataset(self) -> FixtureDataset:
        return FixtureDataset(
            admission_records=[],
            admission_plans=[],
            rank_segments=[],
            universities=[],
            majors=[],
            major_groups=[],
        )
