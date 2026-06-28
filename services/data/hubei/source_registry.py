from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HubeiSource:
    source_id: str
    title: str
    source_url: str
    source_type: str
    owner: str
    data_type: str
    years: str
    status: str
    license_note: str
    parser: str = ""
    raw_subdir: str = ""
    allow_network_download: bool = False
    requires_manual_review: bool = True


@dataclass(frozen=True)
class HubeiSourceRegistry:
    version: int
    sources: list[HubeiSource]


def load_source_registry(path: str | Path) -> HubeiSourceRegistry:
    """Load the project-owned source registry without adding a YAML dependency."""

    registry_path = Path(path)
    if not registry_path.exists():
        raise FileNotFoundError(registry_path)

    version = 1
    raw_sources: list[dict[str, str | bool]] = []
    current: dict[str, str | bool] | None = None

    for raw_line in registry_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("version:"):
            version = int(_parse_value(stripped.split(":", 1)[1]))
            continue
        if stripped.startswith("- "):
            if current:
                raw_sources.append(current)
            current = {}
            key, value = _split_key_value(stripped[2:])
            current[key] = value
            continue
        if current is not None and ":" in stripped:
            key, value = _split_key_value(stripped)
            current[key] = value

    if current:
        raw_sources.append(current)

    required = {
        "source_id",
        "title",
        "source_url",
        "source_type",
        "owner",
        "data_type",
        "years",
        "status",
        "license_note",
    }
    sources: list[HubeiSource] = []
    for index, raw_source in enumerate(raw_sources, start=1):
        missing = sorted(required - raw_source.keys())
        if missing:
            raise ValueError(f"source #{index} missing fields: {', '.join(missing)}")
        values = {
            "parser": "",
            "raw_subdir": str(raw_source.get("data_type", "")),
            "allow_network_download": False,
            "requires_manual_review": True,
            **raw_source,
        }
        sources.append(HubeiSource(**values))  # type: ignore[arg-type]
    return HubeiSourceRegistry(version=version, sources=sources)


def _split_key_value(text: str) -> tuple[str, str | bool]:
    key, value = text.split(":", 1)
    return key.strip(), _parse_value(value)


def _parse_value(value: str) -> str | bool:
    parsed = value.strip()
    if (parsed.startswith('"') and parsed.endswith('"')) or (
        parsed.startswith("'") and parsed.endswith("'")
    ):
        return parsed[1:-1]
    if parsed.lower() == "true":
        return True
    if parsed.lower() == "false":
        return False
    return parsed
