"""
rss_client.py
=============
Fetches adverse news from a curated list of official and press RSS feeds.

Strategy:
- Parse RSS/Atom feeds with feedparser (works on all gov/regulator sites)
- For non-RSS press sites, attempt HTML scraping with requests + BeautifulSoup
- Filter articles by bank name match (case-insensitive)
- Silently skip any source that blocks access (403, timeout, etc.)
- Returns only articles published within the lookback window
"""

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Browser-like headers to reduce chance of being blocked on press sites
# ---------------------------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Source registry
# Each entry: {"name": str, "url": str, "type": "rss" | "html"}
# ---------------------------------------------------------------------------
SOURCES = [
    # --- Official Regulators (reliable RSS/Atom) ---
    {
        "name": "FCA Enforcement",
        "url": "https://www.fca.org.uk/news/rss.xml",
        "type": "rss",
    },
    {
        "name": "Bank of England News",
        "url": "https://www.bankofengland.co.uk/rss/news",
        "type": "rss",
    },
    {
        "name": "Bank of England PRA",
        "url": "https://www.bankofengland.co.uk/rss/prudential-regulation",
        "type": "rss",
    },
    {
        "name": "HM Treasury",
        "url": "https://www.gov.uk/government/organisations/hm-treasury.atom",
        "type": "rss",
    },
    {
        "name": "SEC Press Releases",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=&dateb=&owner=include&count=40&search_text=&action=getcompany",
        "type": "rss",
    },
    {
        "name": "SEC Press Releases RSS",
        "url": "https://www.sec.gov/news/pressreleases.rss",
        "type": "rss",
    },
    {
        "name": "NYDFS Press Releases",
        "url": "https://www.dfs.ny.gov/reports_and_publications/press_releases",
        "type": "html",
    },
    {
        "name": "National Crime Agency",
        "url": "https://nationalcrimeagency.gov.uk/news?format=feed&type=rss",
        "type": "rss",
    },
    {
        "name": "UK Judiciary Judgments",
        "url": "https://www.judiciary.gov.uk/feed/",
        "type": "rss",
    },
    # --- Financial Press (attempt HTML scraping — may be blocked) ---
    {
        "name": "Investment Week",
        "url": "https://www.investmentweek.co.uk/feed",
        "type": "rss",
    },
    {
        "name": "Financial Times",
        "url": "https://www.ft.com/rss/home/uk",
        "type": "rss",
    },
    {
        "name": "Reuters Finance",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "type": "rss",
    },
    {
        "name": "London Stock Exchange News",
        "url": "https://www.londonstockexchange.com/news",
        "type": "html",
    },
]

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _parse_date(entry) -> Optional[datetime]:
    """Extract a timezone-aware datetime from a feedparser entry."""
    for field in ("published_parsed", "updated_parsed"):
        t = getattr(entry, field, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def _fetch_rss(source: dict, cutoff: datetime) -> List[Dict]:
    """Parse an RSS/Atom feed and return recent articles."""
    articles = []
    try:
        feed = feedparser.parse(source["url"])
        if feed.bozo and not feed.entries:
            logger.warning(f"[{source['name']}] Feed parse error: {feed.bozo_exception}")
            return []

        for entry in feed.entries:
            pub_date = _parse_date(entry)
            if pub_date and pub_date < cutoff:
                continue  # Too old

            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            # Strip HTML tags from summary
            summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ")[:500]

            if title and link:
                articles.append({
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "source": source["name"],
                    "published": pub_date.isoformat() if pub_date else "",
                })

        logger.info(f"[{source['name']}] Fetched {len(articles)} articles from RSS.")
    except Exception as e:
        logger.warning(f"[{source['name']}] RSS fetch failed: {e}")

    return articles


def _fetch_html(source: dict, cutoff: datetime) -> List[Dict]:
    """Attempt to scrape article links/titles from an HTML news page."""
    articles = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=10)
        if resp.status_code == 403:
            logger.warning(f"[{source['name']}] Blocked (403). Skipping.")
            return []
        if resp.status_code != 200:
            logger.warning(f"[{source['name']}] HTTP {resp.status_code}. Skipping.")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        # Generic link extraction: find anchors with a meaningful title
        base = f"{urlparse(source['url']).scheme}://{urlparse(source['url']).netloc}"
        seen = set()
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 20:
                continue
            if href.startswith("/"):
                href = base + href
            if href in seen:
                continue
            seen.add(href)
            articles.append({
                "title": text[:200],
                "url": href,
                "summary": "",
                "source": source["name"],
                "published": "",
            })
        logger.info(f"[{source['name']}] Scraped {len(articles)} candidate links from HTML.")
    except requests.Timeout:
        logger.warning(f"[{source['name']}] Timeout. Skipping.")
    except Exception as e:
        logger.warning(f"[{source['name']}] HTML scrape failed: {e}")

    return articles


def fetch_all_articles(lookback_days: int = 7) -> List[Dict]:
    """
    Fetch articles from all configured sources published within the lookback window.
    Silently skips any source that is unavailable or blocked.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    all_articles: List[Dict] = []

    for source in SOURCES:
        try:
            if source["type"] == "rss":
                articles = _fetch_rss(source, cutoff)
            else:
                articles = _fetch_html(source, cutoff)
            all_articles.extend(articles)
        except Exception as e:
            logger.warning(f"[{source['name']}] Unexpected error: {e}")

    # Deduplicate by URL
    seen_urls: set = set()
    unique = []
    for a in all_articles:
        if a["url"] not in seen_urls:
            seen_urls.add(a["url"])
            unique.append(a)

    logger.info(f"Total unique articles fetched across all sources: {len(unique)}")
    return unique


def filter_articles_for_banks(articles: List[Dict], banks: List[str]) -> List[Dict]:
    """
    Filter articles to only those that mention at least one bank in the batch.
    Uses case-insensitive whole-word matching for precision.
    """
    matched = []
    for article in articles:
        haystack = f"{article['title']} {article['summary']}".lower()
        for bank in banks:
            # Match the most distinctive part of the bank name (first 2 words)
            key = " ".join(bank.lower().split()[:2])
            if key and key in haystack:
                matched.append(article)
                break
    return matched


def format_articles_for_prompt(articles: List[Dict]) -> str:
    """Format a list of article dicts into a clean string for the Gemini prompt."""
    if not articles:
        return "No relevant articles found for these institutions in the monitored sources."

    lines = []
    for art in articles:
        lines.append(
            f"--- ARTICLE ---\n"
            f"TITLE: {art['title']}\n"
            f"SOURCE: {art['source']}\n"
            f"URL: {art['url']}\n"
            f"SUMMARY: {art['summary']}\n"
        )
    return "\n".join(lines)
