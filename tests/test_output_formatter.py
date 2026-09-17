"""Tests for output_formatter.py"""
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from output_formatter import format_briefing, merge_pillar, PILLAR_ORDER


SAMPLE_BATCH_RESPONSE = """
## ⚖️ Pillar 1 — Enforcement & Regulatory Action

- **Barclays PLC** — The **FCA** issued a [£50 million fine](https://fca.org.uk/example) for *CASS rules* failures.
- **NatWest Bank** — Ongoing [FCA investigation](https://fca.org.uk/example2) into AML controls.

## 🔍 Pillar 2 — Financial Crime & Integrity

- **Santander UK Plc** — [NCA referral](https://nationalcrimeagency.gov.uk/example) for suspected *KYC* deficiencies.
"""

EMPTY_RESPONSE = ""


class TestMergePillar:
    def test_extracts_content(self):
        pillar_header, pattern = PILLAR_ORDER[0]
        result = merge_pillar(pillar_header, pattern, [SAMPLE_BATCH_RESPONSE])
        assert "Barclays PLC" in result
        assert "NatWest Bank" in result

    def test_returns_empty_if_no_findings(self):
        pillar_header, pattern = PILLAR_ORDER[4]  # Pillar 5 - not in sample
        result = merge_pillar(pillar_header, pattern, [SAMPLE_BATCH_RESPONSE])
        assert result == ""

    def test_deduplication(self):
        duplicate = SAMPLE_BATCH_RESPONSE + "\n" + SAMPLE_BATCH_RESPONSE
        pillar_header, pattern = PILLAR_ORDER[0]
        result = merge_pillar(pillar_header, pattern, [duplicate])
        # Barclays should appear only once
        assert result.count("Barclays PLC") == 1


class TestFormatBriefing:
    def test_header_present(self):
        result = format_briefing(
            batch_responses=[SAMPLE_BATCH_RESPONSE],
            model_used="gemini-3.7-flash",
            reference_date=date(2026, 9, 17),
            lookback_days=7,
            total_banks=131,
        )
        assert "UK Banks — Weekly Adverse News Briefing" in result
        assert "gemini-3.7-flash" in result
        assert "131" in result

    def test_pillar1_present(self):
        result = format_briefing(
            batch_responses=[SAMPLE_BATCH_RESPONSE],
            model_used="gemini-3.7-flash",
            reference_date=date(2026, 9, 17),
            lookback_days=7,
            total_banks=131,
        )
        assert "Pillar 1" in result
        assert "Barclays PLC" in result

    def test_empty_briefing_message(self):
        result = format_briefing(
            batch_responses=[EMPTY_RESPONSE],
            model_used="gemini-3.7-flash",
            reference_date=date(2026, 9, 17),
            lookback_days=7,
            total_banks=131,
        )
        assert "No adverse news identified" in result

    def test_footer_present(self):
        result = format_briefing(
            batch_responses=[SAMPLE_BATCH_RESPONSE],
            model_used="gemini-3.7-flash",
            reference_date=date(2026, 9, 17),
            lookback_days=7,
            total_banks=131,
        )
        assert "remaining institutions" in result
