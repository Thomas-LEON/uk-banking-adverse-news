"""
silobreaker_client.py
=====================
Client for interacting with the Silobreaker API (v2).
Handles HMAC-SHA1 authentication and fetches relevant documents.
"""

import base64
import hashlib
import hmac
import json
import logging
import urllib.parse
import urllib.request
from typing import List, Dict

logger = logging.getLogger(__name__)

BASE_URL = "https://api.silobreaker.com/"


def _build_full_url(relative_url: str) -> str:
    """Constructs the full URL with the source=ApiKey parameter."""
    url = BASE_URL + relative_url
    separator = "&" if "?" in url else "?"
    return url + separator + "source=ApiKey"


def _sign(relative_url: str, api_key: str, shared_key: str, verb: str = "GET") -> str:
    """Signs the URL with HMAC-SHA1 and returns the authenticated URL."""
    full_url = _build_full_url(relative_url)
    message = f"{verb} {full_url}".encode("utf-8")
    
    digest = base64.b64encode(
        hmac.new(shared_key.encode("utf-8"), message, digestmod=hashlib.sha1).digest()
    ).decode("utf-8")
    
    return full_url + "&apiKey=" + api_key + "&digest=" + urllib.parse.quote(digest)


def fetch_adverse_news(
    api_key: str, 
    shared_key: str, 
    banks: List[str], 
    risk_keywords: str,
    from_date: str, 
    to_date: str, 
    page_size: int = 150
) -> List[Dict]:
    """
    Search Silobreaker for adverse news relating to a batch of banks.
    
    Returns a list of parsed article dictionaries.
    """
    if not banks:
        return []

    # Build the OR condition for the banks
    bank_query = " OR ".join(f'"{bank}"' for bank in banks)
    
    # Combine with risk keywords
    full_query = f"({bank_query}) AND {risk_keywords} AND fromdate:\"{from_date}\" AND todate:\"{to_date}\""
    
    params = urllib.parse.urlencode({
        'query': full_query,
        'pageSize': page_size,
    })
    
    relative_url = f"v2/documents/search?{params}"
    signed_url = _sign(relative_url, api_key, shared_key)
    
    logger.info(f"Querying Silobreaker for {len(banks)} banks (from {from_date} to {to_date})")
    
    try:
        req = urllib.request.Request(signed_url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("Items", [])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logger.error(f"Silobreaker HTTP Error {e.code}: {error_body}")
        return []
    except Exception as e:
        logger.error(f"Silobreaker API error: {e}")
        return []


def format_articles_for_prompt(articles: List[Dict]) -> str:
    """
    Takes raw Silobreaker items and formats them into a clean string
    to be injected into the Gemini prompt.
    """
    if not articles:
        return "No relevant articles found for these institutions."
        
    formatted = []
    # Deduplicate by URL just in case
    seen_urls = set()
    
    for doc in articles:
        url = doc.get("SourceUrl")
        if not url or url in seen_urls:
            continue
            
        seen_urls.add(url)
        
        # Depending on Silobreaker's exact return fields, we pull the most relevant text
        title = doc.get("Description") or doc.get("Title", "No Title")
        publisher = doc.get("Publisher", "Unknown Source")
        teaser = doc.get("Teaser", "")
        
        article_text = (
            f"--- ARTICLE ---\n"
            f"TITLE: {title}\n"
            f"SOURCE: {publisher}\n"
            f"URL: {url}\n"
            f"SUMMARY: {teaser}\n"
        )
        formatted.append(article_text)
        
    return "\n".join(formatted)
