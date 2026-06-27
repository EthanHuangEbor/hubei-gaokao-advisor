from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    year: int = 2026
    province: str = "湖北"
    batch: str = "本科普通批"
    category: str = "普通类"
    first_subject: Literal["physics", "history"]
    second_subjects: list[str] = Field(default_factory=list)
    score: int
    rank: int
    preferred_cities: list[str] = Field(default_factory=list)
    avoid_cities: list[str] = Field(default_factory=list)
    preferred_majors: list[str] = Field(default_factory=list)
    avoid_majors: list[str] = Field(default_factory=list)
    max_tuition: int | None = None
    accept_private_college: bool = True
    accept_sino_foreign: bool = True
    accept_adjustment: bool = True
    physical_limits: list[str] = Field(default_factory=list)
    single_subject_limits: dict[str, int] = Field(default_factory=dict)
    priority_strategy: Literal[
        "school_first", "major_first", "city_first", "employment_first", "balanced"
    ] = "balanced"

    def preferences(self) -> dict[str, Any]:
        return {
            "preferred_cities": self.preferred_cities,
            "avoid_cities": self.avoid_cities,
            "preferred_majors": self.preferred_majors,
            "avoid_majors": self.avoid_majors,
            "max_tuition": self.max_tuition,
            "accept_private_college": self.accept_private_college,
            "accept_sino_foreign": self.accept_sino_foreign,
            "accept_adjustment": self.accept_adjustment,
            "physical_limits": self.physical_limits,
            "single_subject_limits": self.single_subject_limits,
            "priority_strategy": self.priority_strategy,
        }


class ParseJobRequest(BaseModel):
    job_type: str = "hubei_plan_parse"
    payload: dict[str, Any] = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    review_status: str
    reviewer_note: str = ""
