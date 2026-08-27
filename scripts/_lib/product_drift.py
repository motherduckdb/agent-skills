from __future__ import annotations

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


DEFAULT_RELEASE_NOTES_RSS = "https://motherduck.com/docs/release-notes/rss.xml"
LINK_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)


def normalize_url(value: str) -> str:
    parts = urlsplit(value)
    path = re.sub(r"/+", "/", parts.path).rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def _fetch(url: str) -> tuple[bytes, str, int]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/rss+xml, application/xml, text/markdown, text/html",
            "User-Agent": "motherduck-agent-skills-drift-audit/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read(), response.geturl(), response.status


def _load_catalog(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: catalog must be a JSON object")
    return payload


def _source_owners(catalog: dict[str, dict[str, object]]) -> dict[str, list[str]]:
    owners: dict[str, list[str]] = {}
    for skill_name, entry in catalog.items():
        for source in entry.get("source_docs", []):
            owners.setdefault(normalize_url(str(source)), []).append(skill_name)
    return owners


def _release_entries(xml_bytes: bytes, *, since: date) -> list[dict[str, object]]:
    root = ET.fromstring(xml_bytes)
    entries: list[dict[str, object]] = []
    for item in root.findall("./channel/item"):
        title = item.findtext("title") or "Untitled release"
        url = item.findtext("link") or ""
        published_raw = item.findtext("pubDate") or ""
        published = parsedate_to_datetime(published_raw).date()
        if published < since:
            continue
        description = unescape(item.findtext("description") or "")
        linked_docs = sorted(
            {
                normalize_url(link)
                for link in LINK_RE.findall(description)
                if urlsplit(link).netloc.lower() == "motherduck.com" and "/docs/" in urlsplit(link).path
            }
        )
        entries.append(
            {
                "title": title,
                "published": published.isoformat(),
                "url": url,
                "linked_docs": linked_docs,
            }
        )
    return entries


def _check_source(url: str) -> dict[str, object]:
    try:
        _, final_url, status_code = _fetch(url)
    except Exception as exc:  # network audit should report, not hide, failures
        return {"url": url, "status": "error", "error": f"{type(exc).__name__}: {exc}"}

    final_normalized = normalize_url(final_url)
    original_normalized = normalize_url(url)
    if status_code != 200:
        return {"url": url, "status": "http_error", "status_code": status_code, "final_url": final_url}
    if final_normalized != original_normalized:
        return {"url": url, "status": "redirect", "status_code": status_code, "final_url": final_url}
    return {"url": url, "status": "ok", "status_code": status_code, "final_url": final_url}


def audit_product_drift(
    *,
    since: str,
    rss_url: str,
    catalog_path: Path,
    check_sources: bool,
) -> dict[str, object]:
    since_date = date.fromisoformat(since)
    catalog = _load_catalog(catalog_path)
    owners = _source_owners(catalog)
    rss_bytes, _, _ = _fetch(rss_url)
    entries = _release_entries(rss_bytes, since=since_date)

    mapped_entries: list[dict[str, object]] = []
    unmatched: set[str] = set()
    for entry in entries:
        linked: list[dict[str, object]] = []
        for url in entry["linked_docs"]:
            skills = sorted(owners.get(str(url), []))
            linked.append({"url": url, "skills": skills})
            if not skills:
                unmatched.add(str(url))
        mapped_entries.append({**entry, "linked_docs": linked})

    source_checks: list[dict[str, object]] = []
    if check_sources:
        source_urls = sorted({str(url) for entry in catalog.values() for url in entry.get("source_docs", [])})
        with ThreadPoolExecutor(max_workers=8) as executor:
            source_checks = list(executor.map(_check_source, source_urls))

    return {
        "since": since_date.isoformat(),
        "rss_url": rss_url,
        "catalog": str(catalog_path),
        "entries": mapped_entries,
        "unmatched_links": sorted(unmatched),
        "source_checks": source_checks,
    }
