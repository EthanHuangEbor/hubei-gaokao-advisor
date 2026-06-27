from __future__ import annotations

from services.crawler.adapters.hubei.hubei_source_discovery import HubeiSourceDiscovery

REQUIRED_SOURCE_URLS = {
    "https://www.hbea.edu.cn/",
    "https://www.hbksw.com/",
    "https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/",
    "https://zspt.hubzs.com.cn/",
    "https://www.hbksw.com/info/38/1771.html",
    "https://www.hbksw.com/info/38/1770.html",
    "https://www.hbksw.com/info/38/1768.html",
    "https://www.hbksw.com/info/38/1746.html",
    "https://www.hbksw.com/info/5/1304.html",
    "https://www.hbksw.com/info/38/1748.html",
    "https://www.hbksw.com/info/38/1845.html",
    "https://www.hbksw.com/info/11/1803.html",
    "https://jyt.hubei.gov.cn/bmdt/ztzl/gxzs/zszy/zsfw/202506/t20250618_5697087.shtml",
}


def test_seed_registry_contains_required_hubei_public_sources() -> None:
    sources = HubeiSourceDiscovery().seed_registry()
    urls = {source.source_url for source in sources}

    assert REQUIRED_SOURCE_URLS <= urls
    platform = next(source for source in sources if source.source_url == "https://zspt.hubzs.com.cn/")
    assert platform.review_status == "manual_only"


def test_discover_from_html_resolves_links_and_classifies_sources() -> None:
    html = """
    <html><body>
      <a href="/info/38/1845.html">2025 年湖北省普通高校招生排序成绩一分一段统计表</a>
      <a href="https://www.hbksw.com/info/38/1771.html">2023--2025 年各批次各类投档线合集</a>
      <a href="https://example.com/private/login">考生登录入口</a>
    </body></html>
    """

    sources = HubeiSourceDiscovery().discover_from_html("https://www.hbksw.com/list/38.html", html)

    assert [source.source_type for source in sources] == ["rank_segments", "admission_lines"]
    assert sources[0].source_url == "https://www.hbksw.com/info/38/1845.html"
    assert all(source.review_status == "pending" for source in sources)
