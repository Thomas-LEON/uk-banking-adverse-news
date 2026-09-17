"""Tests for prompt_builder.py"""
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from prompt_builder import build_prompt, split_into_batches, build_bank_list_str

class TestSplitIntoBatches:
    def test_exact_split(self):
        banks = [f"Bank {i}" for i in range(90)]
        batches = split_into_batches(banks, 30)
        assert len(batches) == 3
        assert all(len(b) == 30 for b in batches)

    def test_remainder_batch(self):
        banks = [f"Bank {i}" for i in range(131)]
        batches = split_into_batches(banks, 30)
        assert len(batches) == 5
        assert len(batches[-1]) == 11

    def test_single_batch(self):
        banks = ["Bank A", "Bank B"]
        batches = split_into_batches(banks, 30)
        assert len(batches) == 1

    def test_empty(self):
        assert split_into_batches([], 30) == []

class TestBuildPrompt:
    def test_contains_bank_names(self):
        banks = ["Barclays PLC", "HSBC UK", "Lloyds Bank plc"]
        prompt = build_prompt(banks, batch_num=1, total_batches=1, articles_text="mock", reference_date=date(2026, 9, 17))
        for bank in banks:
            assert bank in prompt

    def test_contains_date_range(self):
        prompt = build_prompt(["Barclays PLC"], 1, 1, articles_text="mock", lookback_days=7, reference_date=date(2026, 9, 17))
        assert "17 September 2026" in prompt
        assert "10 September 2026" in prompt

    def test_contains_5_pillars(self):
        prompt = build_prompt(["Barclays PLC"], 1, 1, articles_text="mock", reference_date=date(2026, 9, 17))
        assert "Pillar 1" in prompt
        assert "Pillar 2" in prompt
        assert "Pillar 3" in prompt
        assert "Pillar 4" in prompt
        assert "Pillar 5" in prompt

    def test_build_prompt_basic(self):
        banks = ["Barclays", "HSBC"]
        articles = "--- ARTICLE ---\nTITLE: Barclays fined\nSOURCE: Reuters\nURL: http://a.com\nSUMMARY: Fine."
        prompt = build_prompt(
            banks=banks,
            batch_num=1,
            total_batches=2,
            articles_text=articles,
            lookback_days=7,
            reference_date=date(2026, 9, 17)
        )
        assert "Barclays" in prompt
        assert "Barclays fined" in prompt
        assert "BATCH: 1 of 2" in prompt

    def test_batch_info(self):
        prompt = build_prompt(["Bank A"], batch_num=2, total_batches=5, articles_text="mock", reference_date=date(2026, 9, 17))
        assert "2 of 5" in prompt

    def test_mandatory_source_links_instruction(self):
        prompt = build_prompt(["Bank A"], 1, 1, articles_text="mock", reference_date=date(2026, 9, 17))
        assert "MANDATORY SOURCE LINKS" in prompt
