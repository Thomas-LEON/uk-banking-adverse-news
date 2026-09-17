# 🇬🇧 UK Banking Adverse News — Automated Executive Briefing

Automated weekly **Adverse News Screening** for 131 UK-regulated financial institutions,
powered by **Gemini API** with **Google Search Grounding** and **GitHub Actions**.

## How it works

```
GitHub Actions (cron: Mon 07:00 UTC)
         │
         ▼
run_briefing.py
         │
         ├── Load 131 banks (config/banks.json)
         ├── Split into batches of 30
         │
         └── For each batch:
               │
               ├── Build SOP-compliant prompt (prompt_builder.py)
               ├── Call Gemini API + Search Grounding (gemini_client.py)
               │     └── Model cascade: gemini-3.7-flash → gemini-3.6-flash → gemini-3.5-flash
               └── Collect response
         │
         ├── Merge & format 5-Pillar Markdown (output_formatter.py)
         └── Save to briefings/YYYY-MM-DD.md → commit to main
```

## Adverse News Framework — 5 Pillars (per SOP)

| Pillar | Category | Key Triggers |
|--------|----------|-------------|
| ⚖️ 1 | Enforcement & Regulatory Action | FCA/PRA fines, licence revocations, litigation |
| 🔍 2 | Financial Crime & Integrity | AML/KYC failures, OFAC/OFSI violations, fraud |
| 👤 3 | Key Person & Leadership Risk | Misconduct, regulatory bans, governance conflicts |
| ⚙️ 4 | Operational & Security Risk | Outages, cyberattacks, data breaches |
| 💰 5 | Financial Health & Stability | Credit downgrades, liquidity crises, mass layoffs |

## Setup

### 1. Fork or clone this repository

```bash
git clone https://github.com/YOUR_USERNAME/uk-banking-adverse-news.git
cd uk-banking-adverse-news
```

### 2. Add your Gemini API key as a GitHub Secret

Go to: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `GEMINI_API_KEY` | Your Gemini API key from [Google AI Studio](https://aistudio.google.com) |

### 3. Enable GitHub Actions

Actions are automatically enabled for public repositories.
The workflow runs every **Monday at 07:00 UTC** and generates `briefings/YYYY-MM-DD.md`.

### 4. Manual trigger

Go to **Actions → UK Banks Adverse News Briefing → Run workflow**.
Optionally set a `date_override` (YYYY-MM-DD) to generate a backdated briefing.

## Local development

```bash
# Install dependencies
pip install -r requirements.txt

# Dry run (no API call — shows prompts only)
python src/run_briefing.py --dry-run

# Run for a specific date
GEMINI_API_KEY=your_key python src/run_briefing.py --date 2026-09-10

# Run tests
pytest tests/ -v
```

## Configuration

Edit `config/settings.yaml` to adjust:

| Setting | Default | Description |
|---------|---------|-------------|
| `models.primary` | `gemini-3.7-flash` | Primary Gemini model |
| `models.fallback1` | `gemini-3.6-flash` | First fallback |
| `models.fallback2` | `gemini-3.5-flash` | Second fallback |
| `batch_size` | `30` | Banks per API call |
| `lookback_days` | `7` | Rolling window in days |
| `max_retries` | `3` | Retries per model before cascading |

## Output

Briefings are saved to `briefings/YYYY-MM-DD.md` and versioned in `main`.

Subject line convention (for email forwarding):
```
UK Banks Weekly Adverse News Briefing (DD-DD Month YYYY)
```

## Monitored institutions

131 UK-regulated financial institutions tracked in `config/banks.json`,
including Tier-1 clearing banks, challenger banks, building societies,
international subsidiaries, and insurance groups.
