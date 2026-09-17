"""
run_briefing.py
===============
Main orchestrator for the UK Banking Adverse News briefing pipeline.

Usage:
    python src/run_briefing.py                    # Normal run (today)
    python src/run_briefing.py --dry-run          # Print prompts, no API call
    python src/run_briefing.py --date 2026-09-10  # Override reference date
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

# Force UTF-8 stdout (required on Windows for emoji in prompts)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import yaml

# ---------------------------------------------------------------------------
# Ensure src/ is on the path when called from repo root
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))

from gemini_client import call_with_cascade
from prompt_builder import build_prompt, split_into_batches
from output_formatter import format_briefing

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_briefing")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
CONFIG_DIR = REPO_ROOT / "config"
BANKS_FILE = CONFIG_DIR / "banks.json"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"


def load_config() -> dict:
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_banks() -> list[str]:
    with open(BANKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UK Banks Adverse News Briefing")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without calling the Gemini API",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Reference date override in YYYY-MM-DD format (defaults to today)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # ------------------------------------------------------------------ config
    cfg = load_config()
    banks = load_banks()

    batch_size = cfg.get("batch_size", 30)
    lookback_days = cfg.get("lookback_days", 7)
    max_retries = cfg.get("max_retries", 3)
    retry_delay = cfg.get("retry_delay_seconds", 60)
    inter_batch_delay = cfg.get("inter_batch_delay_seconds", 65)
    output_dir = REPO_ROOT / cfg.get("output_dir", "briefings")

    # ---------------------------------------------------------- reference date
    if args.date:
        reference_date = date.fromisoformat(args.date)
    else:
        env_date = os.environ.get("DATE_OVERRIDE", "").strip()
        reference_date = date.fromisoformat(env_date) if env_date else date.today()

    logger.info(f"Reference date: {reference_date}")
    logger.info(f"Banks to screen: {len(banks)}")

    # ----------------------------------------------------------- API key check
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and not args.dry_run:
        logger.error("GEMINI_API_KEY environment variable is not set.")
        sys.exit(1)

    # --------------------------------------------------------------- batching
    batches = split_into_batches(banks, batch_size)
    total_batches = len(batches)
    logger.info(f"Split into {total_batches} batches of up to {batch_size} banks each.")
    logger.info(f"Inter-batch delay: {inter_batch_delay}s | Retry base delay: {retry_delay}s")

    # ---------------------------------------------------------- per-batch call
    batch_responses: list[str] = []
    model_used = cfg["models"]["primary"]  # will be updated to actual model used

    for i, batch in enumerate(batches, start=1):
        prompt = build_prompt(
            banks=batch,
            batch_num=i,
            total_batches=total_batches,
            lookback_days=lookback_days,
            reference_date=reference_date,
        )

        if args.dry_run:
            print(f"\n{'='*60}")
            print(f"BATCH {i}/{total_batches} — DRY RUN PROMPT:")
            print(f"{'='*60}")
            print(prompt)
            batch_responses.append(f"[DRY RUN — no API call for batch {i}]")
            continue

        logger.info(f"Processing batch {i}/{total_batches} ({len(batch)} banks)...")
        try:
            response_text, used_model = call_with_cascade(
                prompt=prompt,
                api_key=api_key,
                max_retries=max_retries,
                retry_delay=float(retry_delay),
            )
            model_used = used_model  # track last model actually used
            batch_responses.append(response_text)
            logger.info(f"Batch {i} complete. Model used: {used_model}")
        except RuntimeError as e:
            logger.error(f"Batch {i} failed permanently: {e}")
            batch_responses.append(f"[ERROR — batch {i} failed: {e}]")

        # Pause between batches to stay within Gemini RPM quota (skip after last batch)
        if i < total_batches:
            logger.info(f"Waiting {inter_batch_delay}s before next batch (rate limit protection)...")
            time.sleep(inter_batch_delay)

    # --------------------------------------------------------- format & save
    briefing_md = format_briefing(
        batch_responses=batch_responses,
        model_used=model_used,
        reference_date=reference_date,
        lookback_days=lookback_days,
        total_banks=len(banks),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{reference_date.isoformat()}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(briefing_md)

    logger.info(f"Briefing saved to: {output_file}")

    if args.dry_run:
        print(f"\n[DRY RUN] Output would be saved to: {output_file}")

    # Output path for GitHub Actions to reference
    print(f"OUTPUT_FILE={output_file}")


if __name__ == "__main__":
    main()
