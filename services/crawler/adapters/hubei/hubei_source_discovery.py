from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

from services.compliance.crawler_policy import may_crawl


@dataclass(frozen=True)
class DataSource:
    source_id: str
    source_name: str
    source_url: str
    source_type: str
    priority: int
    review_status: str = "pending"
    fetched_at: str = ""


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._active_href = ""
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._active_href = href
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._active_href:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._active_href:
            return
        title = " ".join(part.strip() for part in self._text_parts if part.strip())
        if title:
            self.links.append((title, self._active_href))
        self._active_href = ""
        self._text_parts = []


SEED_SOURCES = [
    DataSource("hbea", "湖北省教育考试院", "https://www.hbea.edu.cn/", "official_home", 1),
    DataSource("hbksw", "湖北招生考试网", "https://www.hbksw.com/", "quasi_official_home", 1),
    DataSource(
        "jyt-gxzs",
        "湖北省教育厅高校招生专栏",
        "https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/",
        "official_topic",
        1,
    ),
    DataSource(
        "hubzs-platform",
        "湖北省招生数智综合平台",
        "https://zspt.hubzs.com.cn/",
        "official_platform",
        1,
    ),
    DataSource(
        "hbksw-lines-2023-2025",
        "2023-2025 年各批次各类投档线合集",
        "https://www.hbksw.com/info/38/1771.html",
        "admission_lines",
        1,
    ),
    DataSource(
        "hbksw-lines-2023",
        "2023 年各批次各类投档线合集",
        "https://www.hbksw.com/info/38/1770.html",
        "admission_lines",
        1,
    ),
    DataSource(
        "hbksw-lines-2024",
        "2024 年各批次各类投档线合集",
        "https://www.hbksw.com/info/38/1768.html",
        "admission_lines",
        1,
    ),
    DataSource(
        "hbksw-rank-2023-2026",
        "2023-2026 年湖北一分一段表统计表",
        "https://www.hbksw.com/info/38/1746.html",
        "rank_segments",
        1,
    ),
    DataSource(
        "hbksw-rank-2023",
        "2023 年普通高校招生排序成绩一分一段统计表",
        "https://www.hbksw.com/info/5/1304.html",
        "rank_segments",
        1,
    ),
    DataSource(
        "hbksw-rank-2024",
        "2024 年普通高校招生排序成绩一分一段统计表",
        "https://www.hbksw.com/info/38/1748.html",
        "rank_segments",
        1,
    ),
    DataSource(
        "hbksw-rank-2025",
        "2025 年普通高校招生排序成绩一分一段统计表",
        "https://www.hbksw.com/info/38/1845.html",
        "rank_segments",
        1,
    ),
    DataSource(
        "hbksw-plan-guide-2025",
        "计划查询与志愿填报辅助系统开通及操作指南",
        "https://www.hbksw.com/info/11/1803.html",
        "admission_plan_guide",
        1,
    ),
    DataSource(
        "jyt-policy-2025",
        "2025 年阳光招生政策暨志愿填报问答",
        "https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/zszy/zsfw/202506/t20250618_5697087.shtml",
        "policy_qa",
        1,
    ),
]


class HubeiSourceDiscovery:
    keywords = ("投档线", "一分一段", "招生计划", "计划查询", "阳光招生", "志愿填报", "本科普通批")

    def seed_registry(self) -> list[DataSource]:
        fetched_at = datetime.now(UTC).isoformat()
        return [
            DataSource(
                source_id=item.source_id,
                source_name=item.source_name,
                source_url=item.source_url,
                source_type=item.source_type,
                priority=item.priority,
                review_status=self._review_status(item.source_url, item.source_type, seed=True),
                fetched_at=fetched_at,
            )
            for item in SEED_SOURCES
        ]

    def discover_from_html(self, base_url: str, html: str) -> list[DataSource]:
        parser = _AnchorParser()
        parser.feed(html)
        links = [(title, urljoin(base_url, href)) for title, href in parser.links]
        return self.discover_from_links(links)

    def discover_from_links(self, links: list[tuple[str, str]]) -> list[DataSource]:
        fetched_at = datetime.now(UTC).isoformat()
        results: list[DataSource] = []
        for index, (title, url) in enumerate(links, start=1):
            if not any(keyword in title for keyword in self.keywords):
                continue
            source_type = self._classify(title)
            review_status = self._review_status(url, source_type, seed=False)
            if review_status == "blocked_external":
                continue
            results.append(
                DataSource(
                    source_id=f"discovered-{index}",
                    source_name=title,
                    source_url=url,
                    source_type=source_type,
                    priority=2,
                    review_status=review_status,
                    fetched_at=fetched_at,
                )
            )
        return results

    def _review_status(self, url: str, source_type: str, seed: bool) -> str:
        if source_type in {"official_platform", "admission_plan_guide"}:
            return "manual_only"
        if may_crawl(url):
            return "approved_seed" if seed else "pending"
        return "manual_only" if seed else "blocked_external"

    def _classify(self, title: str) -> str:
        if "投档线" in title:
            return "admission_lines"
        if "一分一段" in title:
            return "rank_segments"
        if "计划查询" in title or "招生计划" in title:
            return "admission_plan_guide"
        if "问答" in title or "阳光招生" in title:
            return "policy_qa"
        return "public_page"
