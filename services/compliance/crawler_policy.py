from __future__ import annotations

from urllib.parse import urlparse

ALLOWED_PUBLIC_HOSTS = {
    "www.hbea.edu.cn",
    "www.hbksw.com",
    "jyt.hubei.gov.cn",
    "zspt.hubzs.com.cn",
}


def is_allowed_public_source(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host in ALLOWED_PUBLIC_HOSTS


def requires_login(url: str) -> bool:
    lowered = url.lower()
    return any(token in lowered for token in ["login", "signin", "passport", "account"])


def may_crawl(url: str) -> bool:
    return is_allowed_public_source(url) and not requires_login(url)

