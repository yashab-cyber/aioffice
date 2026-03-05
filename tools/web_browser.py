"""Web browsing tool — search the web and scrape pages."""

from __future__ import annotations

import logging
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

logger = logging.getLogger("aioffice")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

_TIMEOUT = 15.0


async def web_search(query: str, num_results: int = 5) -> list[dict]:
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
                    "url": (link_el.get_text(strip=True) if link_el else ""),
                })
        return results
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return [{"title": "Search failed", "snippet": str(e), "url": ""}]


async def fetch_page(url: str, max_chars: int = 5000) -> str:
    """Fetch a page and return cleaned text content."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        # Remove script/style/nav
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:max_chars]
    except Exception as e:
        logger.error(f"Page fetch failed for {url}: {e}")
        return f"Failed to fetch {url}: {e}"


async def fetch_github_readme(repo_url: str) -> str:
    """Fetch the README from a GitHub repo."""
    # Convert github.com URL to raw URL
    parts = repo_url.rstrip("/").split("/")
    if len(parts) >= 2:
        owner, repo = parts[-2], parts[-1]
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=_TIMEOUT) as client:
                resp = await client.get(raw_url, headers=_HEADERS)
                if resp.status_code == 200:
                    return resp.text[:5000]
                # Try master branch
                raw_url2 = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                resp2 = await client.get(raw_url2, headers=_HEADERS)
                if resp2.status_code == 200:
                    return resp2.text[:5000]
        except Exception as e:
            logger.error(f"GitHub README fetch failed: {e}")
    return "Could not fetch README."
