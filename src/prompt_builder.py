"""
prompt_builder.py
=================
Builds the Gemini prompt for each batch of banks,
faithful to the SOP Section 5 - Model A template.
"""

from datetime import date, timedelta
from typing import List


SYSTEM_ROLE = """You are an expert Risk Intelligence Specialist performing an \
Adverse News Screening for UK-regulated financial institutions. \
Your output will be reviewed by senior compliance officers and executives."""


TASK_TEMPLATE = """
=== UK BANKS ADVERSE NEWS SCREENING ===

DATE RANGE: {date_from} to {date_to} (last 7 days)
BATCH: {batch_num} of {total_batches}

INSTITUTIONS TO SCREEN:
{bank_list}

=== TASK INSTRUCTIONS ===

1. You are provided with a list of recent news articles in the section below. Read THESE SPECIFIC ARTICLES and extract any material adverse news regarding the listed institutions.

2. EXCLUSION FILTER — Do NOT include:
   - Routine earnings/results announcements
   - Product launches or new service announcements
   - Positive ESG or sustainability news
   - Neutral market commentary
   - Executive promotions or marketing content

3. For each ADVERSE finding, map it to ONE of the following 5 Pillars:

   PILLAR 1 — Enforcement & Regulatory Action
   Triggers: FCA/PRA/BoE enforcement actions, fines, settlements, \
licence revocations, class-action lawsuits, litigation.
   Source standard: Link to FCA, NYDFS, SEC, PRA, or High Court filings.

   PILLAR 2 — Financial Crime & Integrity
   Triggers: AML/KYC failures, OFAC/OFSI sanctions violations, fraud, \
market manipulation, bribery.
   Source standard: Link to regulatory notices, NCA, or investigative financial press.

   PILLAR 3 — Key Person & Leadership Risk
   Triggers: Governance conflicts, professional misconduct, regulatory \
bans/prohibitions, conflicts of interest, forced CEO/CFO departures.
   Source standard: Link to company statements or mainstream press investigations.

   PILLAR 4 — Operational & Security Risk
   Triggers: Major outages, cyberattacks, ransomware incidents, data breaches, \
reserve/collateral doubts.
   Source standard: Link to status pages, Pay.UK, BoE, or security advisories.

   PILLAR 5 — Financial Health & Stability
   Triggers: Credit rating downgrades, liquidity crises, emergency capital raises, \
mass layoffs (>15% workforce).
   Source standard: Link to Moody's/S&P, LSE filings, or financial press.

4. MANDATORY SOURCE LINKS:
   Each adverse finding MUST include a Markdown hyperlink to the primary source.
   Use the EXACT URL provided in the article metadata below.
   Format: [Source Name](URL)

5. Only include findings that meet the adverse criteria. If no material adverse news is found for a specific institution, do not list it.

=== PROVIDED NEWS ARTICLES ===
{articles_text}

=== FORMATTING RULES ===

- Use **bold** for: entity names, fines/monetary values, regulator names, key dates
- Use *italic* for: legal frameworks, court titles, regulatory consultation names
- Bullet points: direct, impersonal, concise (max 2 sentences per bullet)
- Group findings by Pillar, then by institution within each Pillar
- Do NOT include a summary section — findings only

=== OUTPUT FORMAT ===

## ⚖️ Pillar 1 — Enforcement & Regulatory Action
- **[Bank Name]** — [Concise finding with **bold** key data]. [[Source]](url)

## 🔍 Pillar 2 — Financial Crime & Integrity
...

## 👤 Pillar 3 — Key Person & Leadership Risk
...

## ⚙️ Pillar 4 — Operational & Security Risk
...

## 💰 Pillar 5 — Financial Health & Stability
...

If a Pillar has no findings, omit that Pillar section entirely.
"""


def build_bank_list_str(banks: List[str]) -> str:
    """Format a list of banks as a numbered string for the prompt."""
    return "\n".join(f"- {bank}" for bank in banks)


def build_prompt(
    banks: List[str],
    batch_num: int,
    total_batches: int,
    articles_text: str,
    lookback_days: int = 7,
    reference_date: date = None,
) -> str:
    """
    Build the full prompt for a single batch of banks.

    Args:
        banks: List of bank names in this batch.
        batch_num: Current batch number (1-indexed).
        total_batches: Total number of batches.
        articles_text: The formatted text of articles retrieved from Silobreaker.
        lookback_days: Number of days to look back from reference_date.
        reference_date: The end date of the analysis window (defaults to today).

    Returns:
        Full prompt string ready to send to Gemini.
    """
    if reference_date is None:
        reference_date = date.today()

    date_to = reference_date.strftime("%d %B %Y")
    date_from = (reference_date - timedelta(days=lookback_days)).strftime("%d %B %Y")

    bank_list_str = build_bank_list_str(banks)

    task = TASK_TEMPLATE.format(
        date_from=date_from,
        date_to=date_to,
        batch_num=batch_num,
        total_batches=total_batches,
        bank_list=bank_list_str,
        articles_text=articles_text,
    )

    return f"{SYSTEM_ROLE}\n\n{task}"


def split_into_batches(banks: List[str], batch_size: int) -> List[List[str]]:
    """Split the full bank list into batches of batch_size."""
    return [banks[i:i + batch_size] for i in range(0, len(banks), batch_size)]
