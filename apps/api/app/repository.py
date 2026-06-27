from __future__ import annotations

from pathlib import Path

from services.crawler.adapters.hubei.hubei_source_discovery import HubeiSourceDiscovery
from services.crawler.adapters.static_csv_adapter import (
    FixtureDataset,
    StaticCsvHubeiFixtureAdapter,
)


class Repository:
    def __init__(self, root: Path):
        self.root = root
        self.fixture_dir = root / "data" / "fixtures" / "hubei"
        self.dataset: FixtureDataset = StaticCsvHubeiFixtureAdapter(self.fixture_dir).load()
        self.source_discovery = HubeiSourceDiscovery()

    def reload(self) -> FixtureDataset:
        self.dataset = StaticCsvHubeiFixtureAdapter(self.fixture_dir).load()
        return self.dataset

    def sources(self) -> list[dict[str, object]]:
        return [source.__dict__ for source in self.source_discovery.seed_registry()]

