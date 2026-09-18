"""
rss_client.py
=============
Fetches adverse news from a curated list of official and press RSS feeds.

Strategy:
- Parse RSS/Atom feeds with feedparser (works on all gov/regulator sites)
- For non-RSS press sites, attempt HTML scraping with requests + BeautifulSoup
- Filter articles by bank name match (smart token-based, case-insensitive)
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
# Browser-like headers to reduce chance of being blocked
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
# Stop-words to strip from bank names before matching
# (so "Barclays PLC" matches on "barclays" not "plc")
# ---------------------------------------------------------------------------
BANK_NAME_STOPWORDS = {
    "bank", "plc", "ltd", "limited", "group", "uk", "holdings",
    "building", "society", "services", "financial", "insurance",
    "savings", "trust", "international", "co", "the", "of", "and",
    "asset", "management", "capital", "investments", "fund",
}

# ---------------------------------------------------------------------------
# Source registry — expanded with UK-focused adverse news sources
# Each entry: {"name": str, "url": str, "type": "rss" | "html"}
# ---------------------------------------------------------------------------
SOURCES = [
    # ── Official UK Regulators ───────────────────────────────────────────────
    {
        "name": "FCA",
        "url": "https://www.fca.org.uk/news/rss.xml",
        "type": "rss",
    },
    {
        "name": "Bank of England",
        "url": "https://www.bankofengland.co.uk/rss/news",
        "type": "rss",
    },
    {
        "name": "Bank of England PRA",
        "url": "https://www.bankofengland.co.uk/prudential-regulation/publication/rss",
        "type": "rss",
    },
    {
        "name": "HM Treasury",
        "url": "https://www.gov.uk/government/organisations/hm-treasury.atom",
        "type": "rss",
    },
    {
        "name": "OFSI",
        "url": "https://www.gov.uk/government/organisations/office-of-financial-sanctions-implementation.atom",
        "type": "rss",
    },
    {
        "name": "National Crime Agency",
        "url": "https://nationalcrimeagency.gov.uk/news?format=feed&type=rss",
        "type": "rss",
    },
    {
        "name": "UK Judiciary",
        "url": "https://www.judiciary.gov.uk/judgments/feed/",
        "type": "rss",
    },
    {
        "name": "SEC Press Releases",
        "url": "https://www.sec.gov/news/pressreleases.rss",
        "type": "rss",
    },
    # ── UK Financial Press ───────────────────────────────────────────────────
    {
        "name": "City A.M.",
        "url": "https://www.cityam.com/feed/",
        "type": "rss",
    },
    {
        "name": "The Guardian - Business",
        "url": "https://www.theguardian.com/uk/business/rss",
        "type": "rss",
    },
    {
        "name": "BBC News - Business",
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "type": "rss",
    },
    {
        "name": "This Is Money",
        "url": "https://www.thisismoney.co.uk/money/index.rss",
        "type": "rss",
    },
    {
        "name": "Finextra",
        "url": "https://www.finextra.com/rss/headlines.xml",
        "type": "rss",
    },
    {
        "name": "Investment Week",
        "url": "https://www.investmentweek.co.uk/rss",
        "type": "rss",
    },
    {
        "name": "Proactive Investors UK",
        "url": "https://www.proactiveinvestors.co.uk/rss/news",
        "type": "rss",
    },
    {
        "name": "Reuters Finance",
        "url": "https://feeds.reuters.com/reuters/financialsNews",
        "type": "rss",
    },
    {
        "name": "Sky News Business",
        "url": "https://feeds.skynews.com/feeds/rss/business.xml",
        "type": "rss",
    },
    {
        "name": "Yahoo Finance UK",
        "url": "https://finance.yahoo.com/rss/topstories",
        "type": "rss",
    },
    {
        "name": "Cybersecurity News",
        "url": "https://cybersecuritynews.com/feed/",
        "type": "rss",
    },
    {
        "name": "Compliance Week",
        "url": "https://www.complianceweek.com/rss/news",
        "type": "rss",
    },
    {
        "name": "Global Banking & Finance Review",
        "url": "https://www.globalbankingandfinance.com/feed/",
        "type": "rss",
    },
    # ── HTML scraping fallbacks ──────────────────────────────────────────────
    {
        "name": "NYDFS Press Releases",
        "url": "https://www.dfs.ny.gov/reports_and_publications/press_releases",
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
            # If no date found, include anyway (let Gemini filter by content)
            if pub_date and pub_date < cutoff:
                continue

            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()
            summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ")[:600]

            if title and link:
                articles.append({
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "source": source["name"],
                    "published": pub_date.isoformat() if pub_date else "unknown",
                })

        logger.info(f"[{source['name']}] {len(articles)} articles fetched.")
    except Exception as e:
        logger.warning(f"[{source['name']}] RSS fetch failed: {e}")

    return articles


def _fetch_html(source: dict, cutoff: datetime) -> List[Dict]:
    """Attempt to scrape article links/titles from an HTML news page."""
    articles = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=10)
        if resp.status_code in (403, 429):
            logger.warning(f"[{source['name']}] Blocked ({resp.status_code}). Skipping.")
            return []
        if resp.status_code != 200:
            logger.warning(f"[{source['name']}] HTTP {resp.status_code}. Skipping.")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        base = f"{urlparse(source['url']).scheme}://{urlparse(source['url']).netloc}"
        seen = set()
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text or len(text) < 20:
                continue
            if href.startswith("/"):
                href = base + href
            if not href.startswith("http") or href in seen:
                continue
            seen.add(href)
            articles.append({
                "title": text[:200],
                "url": href,
                "summary": "",
                "source": source["name"],
                "published": "unknown",
            })
        logger.info(f"[{source['name']}] {len(articles)} candidate links scraped.")
    except requests.Timeout:
        logger.warning(f"[{source['name']}] Timeout. Skipping.")
    except Exception as e:
        logger.warning(f"[{source['name']}] HTML scrape failed: {e}")

    return articles


def fetch_all_articles(lookback_days: int = 7) -> List[Dict]:
    """
    Fetch articles from all configured sources within the lookback window.
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

    logger.info(f"Total unique articles in pool: {len(unique)}")
    return unique


def _get_bank_tokens(bank_name: str) -> List[str]:
    """
    Extract meaningful tokens from a bank name for matching.
    Removes stopwords and short tokens, keeps the most distinctive terms.
    Returns at least the first significant word.
    """
    words = re.sub(r"[&',.\(\)]", " ", bank_name).lower().split()
    tokens = [w for w in words if w not in BANK_NAME_STOPWORDS and len(w) > 2]
    # Always keep at least the first word even if it's a stopword
    if not tokens:
        tokens = [words[0]] if words else []
    return tokens


def filter_articles_for_banks(articles: List[Dict], banks: List[str]) -> List[Dict]:
    """
    Filter articles to only those mentioning at least one bank in the batch.

    Matching strategy:
    - Extract significant tokens from each bank name (strip stopwords like 'plc', 'ltd')
    - Match ALL significant tokens present in title OR summary (case-insensitive)
    - Single-token names (e.g. "Barclays") only need that one token to match
    """
    matched = []
    for article in articles:
        haystack = f"{article['title']} {article['summary']}".lower()
        for bank in banks:
            tokens = _get_bank_tokens(bank)
            if not tokens:
                continue
            # For multi-token banks: ALL significant tokens must be present
            # For single-token banks: just that token
            if all(tok in haystack for tok in tokens):
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
