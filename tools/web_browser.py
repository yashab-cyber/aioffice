"""Web browsing tool — search, scrape, extract, monitor, RSS, and research."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup

from config import settings

logger = logging.getLogger("aioffice")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_TIMEOUT = 20.0

# ── Cache (in-memory, avoids redundant fetches) ──────────
_page_cache: dict[str, dict] = {}
_MAX_CACHE = 200

# ── Research log ──────────────────────────────────────────
_research_log: list[dict] = []
_MAX_LOG = 300


def _log_research(action: str, query: str, results_count: int, status: str, error: str = ""):
    entry = {
        "action": action,
        "query": query[:200],
        "results": results_count,
        "status": status,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _research_log.append(entry)
    if len(_research_log) > _MAX_LOG:
        _research_log.pop(0)
    return entry


def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _validate_url(url: str) -> str:
    """Validate and normalize a URL."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValueError(f"Invalid URL: {url}")
    # Block private/internal IPs to prevent SSRF
    hostname = parsed.hostname.lower()
    blocked = ("localhost", "127.0.0.1", "0.0.0.0", "169.254.", "10.", "192.168.", "172.16.", "172.17.", "172.18.",
               "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.",
               "172.27.", "172.28.", "172.29.", "172.30.", "172.31.", "[::1]", "metadata.google")
    for b in blocked:
        if hostname.startswith(b) or hostname == b:
            raise ValueError(f"Blocked URL target: {hostname}")
    return url


# ── Web Search ────────────────────────────────────────────

async def web_search(query: str, num_results: int = 8) -> list[dict]:
    """Search the web using DuckDuckGo HTML (no API key needed)."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        results = []
        for r in soup.select(".result")[:num_results]:
            title_el = r.select_one(".result__a")
            snippet_el = r.select_one(".result__snippet")
            link_el = r.select_one(".result__url")
            if title_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    "url": link_el.get_text(strip=True) if link_el else "",
                })

        _log_research("search", query, len(results), "ok")
        logger.info(f"🔍 Web search: '{query}' → {len(results)} results")
        return results
    except Exception as e:
        _log_research("search", query, 0, "error", str(e))
        logger.error(f"Web search failed: {e}")
        return [{"title": "Search failed", "snippet": str(e), "url": ""}]


async def multi_search(queries: list[str], num_results: int = 5) -> dict[str, list[dict]]:
    """Run multiple searches concurrently and return results keyed by query."""
    tasks = [web_search(q, num_results) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    output = {}
    for query, result in zip(queries, results):
        if isinstance(result, Exception):
            output[query] = [{"title": "Error", "snippet": str(result), "url": ""}]
        else:
            output[query] = result
    return output


# ── Page Fetching ─────────────────────────────────────────

async def fetch_page(url: str, max_chars: int = 8000, use_cache: bool = True) -> str:
    """Fetch a page and return cleaned text content."""
    url = _validate_url(url)
    cache_k = _cache_key(url)

    # Check cache
    if use_cache and cache_k in _page_cache:
        cached = _page_cache[cache_k]
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(cached["fetched_at"])).total_seconds()
        if age < 3600:  # 1-hour cache
            _log_research("fetch_cached", url, 1, "ok")
            return cached["text"][:max_chars]

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Cache it
        _page_cache[cache_k] = {"text": text, "url": url, "fetched_at": datetime.now(timezone.utc).isoformat()}
        if len(_page_cache) > _MAX_CACHE:
            oldest_key = next(iter(_page_cache))
            del _page_cache[oldest_key]

        _log_research("fetch", url, len(text), "ok")
        logger.info(f"🌐 Fetched page: {url} ({len(text)} chars)")
        return text[:max_chars]
    except Exception as e:
        _log_research("fetch", url, 0, "error", str(e))
        logger.error(f"Page fetch failed for {url}: {e}")
        return f"Failed to fetch {url}: {e}"


async def fetch_page_structured(url: str, max_chars: int = 8000) -> dict:
    """Fetch a page and return structured data: title, meta, headings, text, links."""
    url = _validate_url(url)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Extract metadata
        title = soup.title.get_text(strip=True) if soup.title else ""
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag:
            meta_desc = meta_tag.get("content", "")

        # Extract headings
        headings = []
        for level in range(1, 4):
            for h in soup.find_all(f"h{level}"):
                headings.append({"level": level, "text": h.get_text(strip=True)[:200]})

        # Extract links
        links = []
        for a in soup.find_all("a", href=True)[:50]:
            href = a.get("href", "")
            link_text = a.get_text(strip=True)
            if href and link_text and not href.startswith(("#", "javascript:")):
                links.append({"text": link_text[:100], "href": href})

        # Clean text
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r"\n{3,}", "\n\n", text)

        _log_research("fetch_structured", url, 1, "ok")
        return {
            "url": url,
            "title": title,
            "meta_description": meta_desc,
            "headings": headings[:30],
            "links": links[:30],
            "text": text[:max_chars],
            "text_length": len(text),
        }
    except Exception as e:
        _log_research("fetch_structured", url, 0, "error", str(e))
        return {"url": url, "error": str(e)}


# ── GitHub Integration ────────────────────────────────────

async def fetch_github_readme(repo_url: str) -> str:
    """Fetch the README from a GitHub repo."""
    parts = repo_url.rstrip("/").split("/")
    if len(parts) < 2:
        return "Invalid repo URL format. Expected: github.com/owner/repo"

    owner, repo = parts[-2], parts[-1]
    branches = ["main", "master"]

    for branch in branches:
        raw_url = f"https://raw.githubusercontent.com/{quote_plus(owner)}/{quote_plus(repo)}/{branch}/README.md"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
                resp = await client.get(raw_url, headers=_HEADERS)
                if resp.status_code == 200:
                    _log_research("github_readme", f"{owner}/{repo}", 1, "ok")
                    return resp.text[:8000]
        except Exception as e:
            logger.error(f"GitHub README fetch for {branch} failed: {e}")

    _log_research("github_readme", f"{owner}/{repo}", 0, "error", "Could not fetch")
    return "Could not fetch README."


async def fetch_github_repo_info(owner: str, repo: str) -> dict:
    """Fetch public repository information from GitHub API."""
    url = f"https://api.github.com/repos/{quote_plus(owner)}/{quote_plus(repo)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers={**_HEADERS, "Accept": "application/vnd.github.v3+json"})
            if resp.status_code == 200:
                data = resp.json()
                _log_research("github_repo", f"{owner}/{repo}", 1, "ok")
                return {
                    "name": data.get("name"),
                    "full_name": data.get("full_name"),
                    "description": data.get("description"),
                    "stars": data.get("stargazers_count"),
                    "forks": data.get("forks_count"),
                    "open_issues": data.get("open_issues_count"),
                    "language": data.get("language"),
                    "topics": data.get("topics", []),
                    "license": data.get("license", {}).get("spdx_id"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "homepage": data.get("homepage"),
                    "default_branch": data.get("default_branch"),
                }
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        _log_research("github_repo", f"{owner}/{repo}", 0, "error", str(e))
        return {"error": str(e)}


async def fetch_github_issues(owner: str, repo: str, state: str = "open", limit: int = 10) -> list[dict]:
    """Fetch recent issues from a GitHub repo."""
    url = f"https://api.github.com/repos/{quote_plus(owner)}/{quote_plus(repo)}/issues"
    params = {"state": state, "per_page": min(limit, 30), "sort": "updated"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, params=params, headers={**_HEADERS, "Accept": "application/vnd.github.v3+json"})
            if resp.status_code == 200:
                issues = []
                for item in resp.json():
                    if "pull_request" not in item:  # Filter out PRs
                        issues.append({
                            "number": item["number"],
                            "title": item["title"],
                            "state": item["state"],
                            "labels": [l["name"] for l in item.get("labels", [])],
                            "created_at": item["created_at"],
                            "updated_at": item["updated_at"],
                            "comments": item.get("comments", 0),
                        })
                _log_research("github_issues", f"{owner}/{repo}", len(issues), "ok")
                return issues
            return [{"error": f"HTTP {resp.status_code}"}]
    except Exception as e:
        _log_research("github_issues", f"{owner}/{repo}", 0, "error", str(e))
        return [{"error": str(e)}]


# ── Content Extraction ────────────────────────────────────

async def extract_emails_from_page(url: str) -> list[str]:
    """Extract email addresses from a webpage (for outreach research)."""
    text = await fetch_page(url, max_chars=50000)
    # Simple email regex — good enough for most pages
    emails = list(set(re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)))
    _log_research("extract_emails", url, len(emails), "ok")
    return emails[:50]


async def extract_social_links(url: str) -> dict[str, list[str]]:
    """Extract social media links from a webpage."""
    result = await fetch_page_structured(url)
    if "error" in result:
        return {"error": result["error"]}

    social = {
        "twitter": [],
        "linkedin": [],
        "github": [],
        "youtube": [],
        "discord": [],
        "reddit": [],
        "facebook": [],
    }

    for link in result.get("links", []):
        href = link.get("href", "").lower()
        for platform in social:
            if platform in href:
                social[platform].append(link["href"])

    # Deduplicate
    return {k: list(set(v)) for k, v in social.items() if v}


# ── Competitor Research ───────────────────────────────────

async def research_competitor(name: str) -> dict:
    """Research a competitor — search, fetch website, extract key info."""
    search_results = await web_search(f"{name} official website", num_results=5)

    competitor_info = {
        "name": name,
        "search_results": search_results,
        "website": None,
        "social_links": {},
    }

    # Try to fetch the first relevant result
    if search_results and search_results[0].get("url"):
        main_url = search_results[0]["url"]
        if not main_url.startswith(("http://", "https://")):
            main_url = "https://" + main_url
        try:
            page = await fetch_page_structured(main_url)
            competitor_info["website"] = {
                "url": main_url,
                "title": page.get("title", ""),
                "description": page.get("meta_description", ""),
                "headings": page.get("headings", [])[:10],
            }
            socials = await extract_social_links(main_url)
            competitor_info["social_links"] = socials
        except Exception as e:
            competitor_info["website"] = {"error": str(e)}

    _log_research("competitor_research", name, 1, "ok")
    return competitor_info


async def research_topic(topic: str, depth: int = 2) -> dict:
    """
    Deep research on a topic — search, read top pages, synthesize.
    
    depth controls how many sources to read (1-5).
    """
    depth = max(1, min(depth, 5))
    search_results = await web_search(topic, num_results=depth * 2)

    sources = []
    for result in search_results[:depth]:
        url = result.get("url", "")
        if not url:
            continue
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            text = await fetch_page(url, max_chars=5000)
            sources.append({
                "url": url,
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "content": text[:3000],
            })
        except Exception:
            pass

    _log_research("topic_research", topic, len(sources), "ok")
    return {
        "topic": topic,
        "search_results": search_results,
        "sources_read": len(sources),
        "sources": sources,
        "researched_at": datetime.now(timezone.utc).isoformat(),
    }


# ── RSS / News Monitoring ────────────────────────────────

async def fetch_rss(feed_url: str, limit: int = 10) -> list[dict]:
    """Fetch and parse an RSS/Atom feed."""
    feed_url = _validate_url(feed_url)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
            resp = await client.get(feed_url, headers=_HEADERS)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "xml")
        items = []

        # RSS 2.0
        for item in soup.find_all("item")[:limit]:
            items.append({
                "title": item.find("title").get_text(strip=True) if item.find("title") else "",
                "link": item.find("link").get_text(strip=True) if item.find("link") else "",
                "description": (item.find("description").get_text(strip=True)[:500]
                                if item.find("description") else ""),
                "published": item.find("pubDate").get_text(strip=True) if item.find("pubDate") else "",
            })

        # Atom
        if not items:
            for entry in soup.find_all("entry")[:limit]:
                link_tag = entry.find("link")
                items.append({
                    "title": entry.find("title").get_text(strip=True) if entry.find("title") else "",
                    "link": link_tag.get("href", "") if link_tag else "",
                    "description": (entry.find("summary").get_text(strip=True)[:500]
                                    if entry.find("summary") else ""),
                    "published": entry.find("updated").get_text(strip=True) if entry.find("updated") else "",
                })

        _log_research("rss", feed_url, len(items), "ok")
        return items
    except Exception as e:
        _log_research("rss", feed_url, 0, "error", str(e))
        return [{"error": str(e)}]


async def monitor_news(topics: list[str], num_per_topic: int = 3) -> dict[str, list[dict]]:
    """Search news for multiple topics. Returns results keyed by topic."""
    results = {}
    for topic in topics:
        news = await web_search(f"{topic} news latest 2026", num_results=num_per_topic)
        results[topic] = news
        await asyncio.sleep(0.5)  # be polite
    return results


# ── SEO Analysis ──────────────────────────────────────────

async def analyze_seo(url: str) -> dict:
    """Basic SEO analysis of a page — title, meta, headings, links count."""
    page = await fetch_page_structured(url)
    if "error" in page:
        return {"url": url, "error": page["error"]}

    title = page.get("title", "")
    desc = page.get("meta_description", "")
    headings = page.get("headings", [])

    h1_count = sum(1 for h in headings if h["level"] == 1)
    h2_count = sum(1 for h in headings if h["level"] == 2)
    h3_count = sum(1 for h in headings if h["level"] == 3)

    issues = []
    if not title:
        issues.append("Missing page title")
    elif len(title) > 60:
        issues.append(f"Title too long ({len(title)} chars, recommended: ≤60)")
    if not desc:
        issues.append("Missing meta description")
    elif len(desc) > 160:
        issues.append(f"Meta description too long ({len(desc)} chars, recommended: ≤160)")
    if h1_count == 0:
        issues.append("Missing H1 heading")
    elif h1_count > 1:
        issues.append(f"Multiple H1 headings ({h1_count})")

    _log_research("seo_analysis", url, 1, "ok")
    return {
        "url": url,
        "title": title,
        "title_length": len(title),
        "meta_description": desc,
        "meta_length": len(desc),
        "headings": {"h1": h1_count, "h2": h2_count, "h3": h3_count},
        "total_links": len(page.get("links", [])),
        "text_length": page.get("text_length", 0),
        "issues": issues,
        "score": max(0, 100 - len(issues) * 15),
    }


# ── Product Hunt ──────────────────────────────────────────

async def search_product_hunt(query: str) -> list[dict]:
    """Search Product Hunt via web search (no API key needed)."""
    results = await web_search(f"site:producthunt.com {query}", num_results=5)
    return results


# ── Technology Detection ──────────────────────────────────

async def detect_technologies(url: str) -> dict:
    """Detect technologies used on a website by analyzing HTML/headers."""
    url = _validate_url(url)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        technologies = {
            "frameworks": [],
            "analytics": [],
            "cms": [],
            "cdn": [],
            "server": [],
        }

        html = resp.text.lower()
        headers_lower = {k.lower(): v for k, v in resp.headers.items()}

        # Framework detection
        framework_sigs = {
            "React": ["react", "_next", "__next"],
            "Vue.js": ["vue.js", "vuejs", "__vue"],
            "Angular": ["angular", "ng-"],
            "Next.js": ["_next/static", "next.js"],
            "Nuxt": ["_nuxt", "nuxt"],
            "Svelte": ["svelte"],
            "Tailwind": ["tailwind"],
            "Bootstrap": ["bootstrap"],
        }
        for tech, sigs in framework_sigs.items():
            if any(sig in html for sig in sigs):
                technologies["frameworks"].append(tech)

        # Analytics
        if "google-analytics" in html or "gtag" in html or "ga(" in html:
            technologies["analytics"].append("Google Analytics")
        if "segment.com" in html or "analytics.js" in html:
            technologies["analytics"].append("Segment")
        if "hotjar" in html:
            technologies["analytics"].append("Hotjar")

        # Server
        server = headers_lower.get("server", "")
        if server:
            technologies["server"].append(server)
        powered_by = headers_lower.get("x-powered-by", "")
        if powered_by:
            technologies["server"].append(powered_by)

        # CDN
        if "cloudflare" in str(headers_lower):
            technologies["cdn"].append("Cloudflare")
        if "x-amz" in str(headers_lower) or "amazonaws" in html:
            technologies["cdn"].append("AWS")
        if "vercel" in str(headers_lower):
            technologies["cdn"].append("Vercel")

        _log_research("tech_detect", url, sum(len(v) for v in technologies.values()), "ok")
        return {"url": url, "technologies": technologies}
    except Exception as e:
        _log_research("tech_detect", url, 0, "error", str(e))
        return {"url": url, "error": str(e)}


# ── Analytics ─────────────────────────────────────────────

def get_browser_stats() -> dict:
    """Return web browsing statistics."""
    if not _research_log:
        return {"total_actions": 0, "cached_pages": 0}

    by_action = {}
    by_status = {}
    for entry in _research_log:
        action = entry["action"]
        by_action[action] = by_action.get(action, 0) + 1
        status = entry["status"]
        by_status[status] = by_status.get(status, 0) + 1

    return {
        "total_actions": len(_research_log),
        "by_action": by_action,
        "by_status": by_status,
        "cached_pages": len(_page_cache),
        "total_results_found": sum(e.get("results", 0) for e in _research_log),
    }


def get_research_log(limit: int = 50, action: str = "") -> list[dict]:
    """Return recent research log entries."""
    entries = _research_log
    if action:
        entries = [e for e in entries if e["action"] == action]
    return entries[-limit:]


def clear_cache():
    """Clear the page cache."""
    _page_cache.clear()
    logger.info("🗑️ Web page cache cleared")
