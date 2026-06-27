from __future__ import annotations

from collections.abc import Iterable

SUBJECT_ALIASES = {
    "物理": "physics",
    "physics": "physics",
    "历史": "history",
    "history": "history",
    "化学": "chemistry",
    "chemistry": "chemistry",
    "生物": "biology",
    "biology": "biology",
    "政治": "politics",
    "思想政治": "politics",
    "politics": "politics",
    "地理": "geography",
    "geography": "geography",
}

CN_SUBJECTS = {
    "physics": "物理",
    "history": "历史",
    "chemistry": "化学",
    "biology": "生物",
    "politics": "政治",
    "geography": "地理",
}


def normalize_subject(subject: str) -> str:
    value = subject.strip().lower()
    return SUBJECT_ALIASES.get(value, SUBJECT_ALIASES.get(subject.strip(), value))


def normalize_second_subjects(subjects: Iterable[str]) -> set[str]:
    return {normalize_subject(item) for item in subjects if item}


def requirement_satisfied(requirement: str, second_subjects: Iterable[str]) -> bool:
    """Evaluate Hubei-style secondary subject requirements.

    Supported examples: 不限, 化学, 化学+生物, 化学/生物, 再选化学或生物.
    """

    req = requirement.strip()
    if not req or req in {"不限", "无", "none", "any"}:
        return True

    selected = normalize_second_subjects(second_subjects)
    tokens = [
        ("化学", "chemistry"),
        ("生物", "biology"),
        ("政治", "politics"),
        ("思想政治", "politics"),
        ("地理", "geography"),
    ]
    present = [canonical for text, canonical in tokens if text in req or canonical in req.lower()]
    if not present:
        return True

    if "或" in req or "/" in req or "任选" in req:
        return any(item in selected for item in present)
    return all(item in selected for item in present)


def first_subject_label(first_subject: str) -> str:
    return CN_SUBJECTS.get(normalize_subject(first_subject), first_subject)


def tier_for_probability(probability: float) -> str:
    if probability < 0.45:
        return "冲"
    if probability < 0.75:
        return "稳"
    if probability < 0.92:
        return "保"
    return "垫"


def probability_band_label(tier: str) -> str:
    return {
        "冲": "20%-45%估计区间",
        "稳": "45%-75%估计区间",
        "保": "75%-92%估计区间",
        "垫": "92%以上估计区间",
    }.get(tier, "低置信估计区间")

