"""
output_formatter.py
===================
Merges batch responses from Gemini into a single structured Markdown briefing.
Deduplicates findings and assembles the final 5-Pillar document.
"""

import re
from datetime import date, timedelta
from typing import List


PILLAR_ORDER = [
    ("⚖️ Pillar 1 — Enforcement & Regulatory Action",   r"##\s*⚖️\s*Pillar 1[^\n]*"),
    ("🔍 Pillar 2 — Financial Crime & Integrity",        r"##\s*🔍\s*Pillar 2[^\n]*"),
    ("👤 Pillar 3 — Key Person & Leadership Risk",       r"##\s*👤\s*Pillar 3[^\n]*"),
    ("⚙️ Pillar 4 — Operational & Security Risk",        r"##\s*⚙️\s*Pillar 4[^\n]*"),
    ("💰 Pillar 5 — Financial Health & Stability",       r"##\s*💰\s*Pillar 5[^\n]*"),
]


def extract_pillar_content(text: str, header_pattern: str) -> str:
    """
    Extract the bullet content under a pillar heading from a batch response.
    Returns the content between this pillar heading and the next ## heading.
    """
    pattern = rf"({header_pattern})(.*?)(?=\n##|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(2).strip()
    return ""


def deduplicate_bullets(bullets: str) -> str:
    """Remove duplicate bullet lines (same bank + same first ~60 chars)."""
    seen = set()
    result = []
    for line in bullets.splitlines():
        key = line.strip()[:80]
        if key and key not in seen:
            seen.add(key)
            result.append(line)
    return "\n".join(result)


def merge_pillar(pillar_header: str, pattern: str, batch_responses: List[str]) -> str:
    """
    Merge content from all batches for a single pillar.
    Returns the full pillar section or empty string if no findings.
    """
    all_content = []
    for response in batch_responses:
        content = extract_pillar_content(response, pattern)
        if content:
            all_content.append(content)

    if not all_content:
        return ""

    merged = "\n".join(all_content)
    merged = deduplicate_bullets(merged)

    if not merged.strip():
        return ""

    return f"## {pillar_header}\n\n{merged}\n"


def build_header(
    model_used: str,
    reference_date: date,
    lookback_days: int,
    total_banks: int,
) -> str:
    """Build the briefing header block."""
    date_to = reference_date.strftime("%d %B %Y")
    date_from = (reference_date - timedelta(days=lookback_days)).strftime("%d %B %Y")
    generated_at = reference_date.strftime("%Y-%m-%d")

    return f"""# 🇬🇧 UK Banks — Weekly Adverse News Briefing

| Field | Value |
|---|---|
| **Period** | {date_from} – {date_to} |
| **Generated** | {generated_at} |
| **Model used** | `{model_used}` |
| **Institutions screened** | {total_banks} |

> **Scope**: All adverse news only. Neutral and positive coverage excluded per SOP.
> Sources: FCA, BoE, PRA, HM Treasury, Reuters, Bloomberg, Financial Times, Hansard.

---
"""


FOOTER = """
---
*No adverse news was identified for the remaining institutions in the monitoring \
universe during the reference period.*

*This briefing was generated automatically via the [uk-banking-adverse-news](https://github.com/Thomas-LEON/uk-banking-adverse-news) \
pipeline using Gemini API with Google Search Grounding.*
"""


def format_briefing(
    batch_responses: List[str],
    model_used: str,
    reference_date: date,
    lookback_days: int,
    total_banks: int,
) -> str:
    """
    Assemble the final Markdown briefing from all batch responses.

    Args:
        batch_responses: List of raw Gemini response strings, one per batch.
        model_used: The Gemini model that produced the responses.
        reference_date: The end date of the analysis window.
        lookback_days: Number of days in the lookback window.
        total_banks: Total number of institutions screened.

    Returns:
        Complete Markdown briefing as a string.
    """
    header = build_header(model_used, reference_date, lookback_days, total_banks)

    sections = []
    for pillar_header, pattern in PILLAR_ORDER:
        section = merge_pillar(pillar_header, pattern, batch_responses)
        if section:
            sections.append(section)

    if not sections:
        body = "> ✅ **No adverse news identified** for any monitored institution during this period.\n"
    else:
        body = "\n".join(sections)

    return header + body + FOOTER
