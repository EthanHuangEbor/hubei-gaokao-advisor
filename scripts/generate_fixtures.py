from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "data" / "fixtures" / "hubei"

SOURCE_URLS = {
    "records": "https://www.hbksw.com/info/38/1771.html",
    "rank": "https://www.hbksw.com/info/38/1746.html",
    "plan": "manual-upload://official-hubei-2026-plan-fixture",
}

MAJOR_CATALOG = [
    ("080901", "计算机科学与技术", "物理+化学专业组"),
    ("080701", "电子信息工程", "物理+化学专业组"),
    ("080801", "自动化", "物理+化学专业组"),
    ("081001", "土木工程", "物理+不限专业组"),
    ("100201", "临床医学", "物理+化学专业组"),
    ("120203", "会计学", "历史+不限专业组"),
    ("050101", "汉语言文学", "历史+不限专业组"),
    ("030101", "法学", "历史+政治专业组"),
    ("020301", "金融学", "历史+不限专业组"),
    ("050201", "英语", "历史+不限专业组"),
]

CITIES = ["武汉", "襄阳", "宜昌", "黄冈", "荆州", "十堰", "孝感", "咸宁"]


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIXTURE_DIR / name
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def subject_rows(first_subject: str, count: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    is_physics = first_subject == "physics"
    subject_label = "物理" if is_physics else "历史"
    base_rank = 9000 if is_physics else 6000
    step = 1150 if is_physics else 900
    for idx in range(1, count + 1):
        university_no = idx if is_physics else idx + 60
        university_code = f"HBA{university_no:03d}"
        group_code = f"{university_code}-{'P' if is_physics else 'H'}{idx:02d}"
        major_code, major_name, group_suffix = MAJOR_CATALOG[(idx - 1) % (5 if is_physics else 5) + (0 if is_physics else 5)]
        requirement = "化学" if "化学" in group_suffix else ("政治" if "政治" in group_suffix else "不限")
        min_rank_2025 = base_rank + idx * step
        volatility = (idx % 5 - 2) * 140
        rows.append(
            {
                "university_code": university_code,
                "university_name": f"湖北样例{university_no:03d}大学",
                "major_group_code": group_code,
                "major_group_name": f"{subject_label}{idx:02d}组-{group_suffix}",
                "first_subject": first_subject,
                "second_subject_requirement": requirement,
                "major_code": major_code,
                "major_name": major_name,
                "campus": CITIES[idx % len(CITIES)],
                "is_private": "是" if idx % 17 == 0 else "否",
                "is_sino_foreign": "是" if idx % 19 == 0 else "否",
                "tuition": 42000 if idx % 19 == 0 else (28000 if idx % 17 == 0 else 5200 + (idx % 6) * 500),
                "plan_seats_2025": 55 + (idx % 8) * 4,
                "plan_seats_2026": max(12, 55 + (idx % 8) * 4 + (idx % 7 - 3) * 3),
                "min_rank_2023": min_rank_2025 + 600 + volatility,
                "min_rank_2024": min_rank_2025 - 260 - volatility,
                "min_rank_2025": min_rank_2025,
                "min_score_2023": max(360, 670 - min_rank_2025 // (520 if is_physics else 430)),
                "min_score_2024": max(360, 674 - min_rank_2025 // (520 if is_physics else 430)),
                "min_score_2025": max(360, 678 - min_rank_2025 // (520 if is_physics else 430)),
            }
        )
    return rows


def generate() -> None:
    physics = subject_rows("physics", 54)
    history = subject_rows("history", 54)
    groups = physics + history

    write_csv(
        "hubei_sample_universities.csv",
        ["university_code", "university_name", "province", "city", "is_private"],
        [
            {
                "university_code": row["university_code"],
                "university_name": row["university_name"],
                "province": "湖北",
                "city": row["campus"],
                "is_private": row["is_private"],
            }
            for row in groups
        ],
    )
    write_csv(
        "hubei_sample_major_groups.csv",
        [
            "university_code",
            "university_name",
            "major_group_code",
            "major_group_name",
            "first_subject",
            "second_subject_requirement",
        ],
        [
            {
                "university_code": row["university_code"],
                "university_name": row["university_name"],
                "major_group_code": row["major_group_code"],
                "major_group_name": row["major_group_name"],
                "first_subject": row["first_subject"],
                "second_subject_requirement": row["second_subject_requirement"],
            }
            for row in groups
        ],
    )
    write_csv(
        "hubei_sample_majors.csv",
        ["major_code", "major_name", "major_group_code", "university_code"],
        [
            {
                "major_code": row["major_code"],
                "major_name": row["major_name"],
                "major_group_code": row["major_group_code"],
                "university_code": row["university_code"],
            }
            for row in groups
        ],
    )
    write_csv(
        "hubei_sample_admission_plans_2026.csv",
        [
            "year",
            "province",
            "batch",
            "category",
            "first_subject",
            "second_subject_requirement",
            "university_code",
            "university_name",
            "major_group_code",
            "major_group_name",
            "major_code",
            "major_name",
            "plan_seats",
            "tuition",
            "schooling_years",
            "campus",
            "is_sino_foreign",
            "is_private",
            "notes",
            "physical_limit_note",
            "single_subject_limit_note",
            "source_id",
            "source_url",
            "confidence_score",
        ],
        [
            {
                "year": 2026,
                "province": "湖北",
                "batch": "本科普通批",
                "category": "普通类",
                "first_subject": row["first_subject"],
                "second_subject_requirement": row["second_subject_requirement"],
                "university_code": row["university_code"],
                "university_name": row["university_name"],
                "major_group_code": row["major_group_code"],
                "major_group_name": row["major_group_name"],
                "major_code": row["major_code"],
                "major_name": row["major_name"],
                "plan_seats": row["plan_seats_2026"],
                "tuition": row["tuition"],
                "schooling_years": "4年",
                "campus": row["campus"],
                "is_sino_foreign": row["is_sino_foreign"],
                "is_private": row["is_private"],
                "notes": "虚构样例，仅用于格式和流程测试",
                "physical_limit_note": "色弱慎报" if row["major_name"] == "临床医学" else "",
                "single_subject_limit_note": "英语不低于100分" if row["major_name"] == "英语" else "",
                "source_id": "fixture-plan-2026",
                "source_url": SOURCE_URLS["plan"],
                "confidence_score": 0.95,
            }
            for row in groups
        ],
    )

    for year in [2023, 2024, 2025]:
        write_csv(
            f"hubei_sample_admission_records_{year}.csv",
            [
                "year",
                "province",
                "batch",
                "category",
                "first_subject",
                "second_subject_requirement",
                "university_code",
                "university_name",
                "major_group_code",
                "major_group_name",
                "admission_category",
                "min_score",
                "min_rank",
                "plan_seats",
                "source_id",
                "source_url",
                "confidence_score",
                "parser_version",
            ],
            [
                {
                    "year": year,
                    "province": "湖北",
                    "batch": "本科普通批",
                    "category": "普通类",
                    "first_subject": row["first_subject"],
                    "second_subject_requirement": row["second_subject_requirement"],
                    "university_code": row["university_code"],
                    "university_name": row["university_name"],
                    "major_group_code": row["major_group_code"],
                    "major_group_name": row["major_group_name"],
                    "admission_category": "平行志愿",
                    "min_score": row[f"min_score_{year}"],
                    "min_rank": row[f"min_rank_{year}"],
                    "plan_seats": row["plan_seats_2025"] + (year - 2025) * 2,
                    "source_id": f"fixture-lines-{year}",
                    "source_url": SOURCE_URLS["records"],
                    "confidence_score": 0.95,
                    "parser_version": "fixture-v1",
                }
                for row in groups
            ],
        )

    for year in [2023, 2024, 2025, 2026]:
        rows: list[dict[str, object]] = []
        for first_subject in ["physics", "history"]:
            base = 695 if first_subject == "physics" else 665
            for step_idx, score in enumerate(range(base, 339, -25), start=1):
                rank_start = 1 + (step_idx - 1) * (2800 if first_subject == "physics" else 2300)
                rank_end = rank_start + (2800 if first_subject == "physics" else 2300) - 1
                rows.append(
                    {
                        "year": year,
                        "province": "湖北",
                        "category": "普通类",
                        "first_subject": first_subject,
                        "score": score,
                        "same_score_count": 300 + step_idx * 13,
                        "cumulative_rank": rank_end,
                        "rank_start": rank_start,
                        "rank_end": rank_end,
                        "source_id": f"fixture-rank-{year}",
                        "source_url": SOURCE_URLS["rank"],
                        "confidence_score": 0.95,
                    }
                )
        write_csv(
            f"hubei_sample_rank_segments_{year}.csv",
            [
                "year",
                "province",
                "category",
                "first_subject",
                "score",
                "same_score_count",
                "cumulative_rank",
                "rank_start",
                "rank_end",
                "source_id",
                "source_url",
                "confidence_score",
            ],
            rows,
        )

    write_csv(
        "hubei_sample_same_rank_reference_groups.csv",
        [
            "target_year",
            "history_year",
            "province",
            "first_subject",
            "candidate_rank",
            "rank_window_start",
            "rank_window_end",
            "university_code",
            "university_name",
            "major_group_code",
            "major_group_name",
            "min_score",
            "min_rank",
            "rank_gap",
            "reference_type",
            "confidence_score",
            "source_url",
        ],
        [],
    )


if __name__ == "__main__":
    generate()
    print(f"Generated fixtures in {FIXTURE_DIR}")

