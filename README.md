# Texas Vanity Plate Checker

Generates personalized vanity plate ideas and checks their availability on
[myplates.com](https://www.myplates.com) — Texas's official plate vendor.

Uses **Playwright** (headless Chromium browser) to bypass myplates.com's
Incapsula bot protection, which blocks raw HTTP requests with 403 errors.

## Quick Start

```bash
./run.sh
```

That's it. The script creates a Python virtual environment, installs
Playwright + Chromium, and runs the checker automatically.

All arguments are forwarded, e.g. `./run.sh --max-plates 30`

## Features

- **Generate 500 plates from any description** — give it a paragraph about your
  interests and get 500 creative vanity plate candidates
- **131+ built-in plate ideas** across 11 categories (Tech/AI, Heritage,
  Leadership, Crypto, Aviation, and more)
- **Wow factor scoring** — plates ranked by creativity, readability, and uniqueness
- **Playwright browser engine** — uses a real browser to bypass Incapsula WAF
- **Rate-limited requests** — respects myplates.com with configurable delays
- **Incapsula bot detection** — auto-stops when blocked, avoids bans
- **JSON export** — results sorted by wow factor saved to `results.json`

## Usage

```bash
# ── Generate plates from a description ──────────────────────
# Produces 500 plate ideas and saves them to input.json
python3 plate_checker.py --generate "I love technology, AI, fast cars, and aviation"

# ── Check plates from a file ───────────────────────────────
# Loads input.json and checks availability on myplates.com
python3 plate_checker.py --input input.json

# Check only the top 50 (sorted by wow factor)
python3 plate_checker.py --input input.json --max-plates 50

# ── Built-in plates (original mode) ────────────────────────
python3 plate_checker.py                    # Check all 131+ built-in plates
python3 plate_checker.py --max-plates 30    # Top 30 most unique
python3 plate_checker.py --list-only        # Preview without checking

# ── Options (work with any mode) ───────────────────────────
python3 plate_checker.py --delay 3.0                                # Slower
python3 plate_checker.py --add "MYPLATE" "COOL1"                    # Add custom plates
python3 plate_checker.py --plate-style black-white-premium-embossed # Plate design
python3 plate_checker.py --no-headless                              # Show browser
```

### Two-Step Workflow

1. **Generate** plate ideas from a paragraph describing your interests:
   ```bash
   ./run.sh --generate "Retired tech executive, Spanish heritage, Austin TX,
   passionate about AI, Ethereum, and home automation"
   ```
   This creates `input.json` with 500 plate candidates scored by wow factor.

2. **Check** availability on myplates.com:
   ```bash
   ./run.sh --input input.json --max-plates 100
   ```
   Results are saved to `results.json`, sorted by wow factor.

## How It Works

The app uses Playwright to launch a headless Chromium browser that:

1. **Visits myplates.com** first to establish cookies and pass Incapsula's
   JavaScript challenges
2. **Queries the API** endpoint for each plate:
   ```
   https://www.myplates.com/api/licenseplates/passenger/{style}/{plate-text}
   ```
3. **Parses the response** — if it contains `"available`, the plate is open

This approach is necessary because myplates.com uses [Imperva Incapsula](https://www.imperva.com/products/bot-management/)
bot protection, which blocks raw HTTP requests (urllib, requests, curl) with
403 Forbidden errors. A real browser handles the JS challenges automatically.

If you still get blocked, try:
- Increasing `--delay` to 3-5 seconds
- Using `--no-headless` to show the browser (sometimes helps)
- Changing your IP / using a VPN
- Waiting a few minutes before retrying

## Plate Categories

| Category | Examples | Description |
|----------|----------|-------------|
| Tech/AI | AIEXEC, GENAI, DEEPML | AI, machine learning, cloud computing |
| Career | BIGBLU, MNGPRT, BIZTRN | IBM, consulting, business leadership |
| Heritage | MADRID, ESPANA, EL JEFE | Spanish language and culture |
| Leadership | PIONR, VSNARY, TRBLZR | Executive and leadership themes |
| Crypto | HODLR, ETHGUY, WEB3GM | Ethereum, blockchain, DeFi |
| HomeAuto | HASSIO, SMTHOM, HOMLAB | Smart home and IoT |
| Aviation | PILOTO, FLYBOY, TOPGUN | Air Force and aviation |
| Austin/TX | ATXTEK, TXEXEC, ATX AI | Austin and Texas pride |
| Diversity | INCLSN, HITEC, UNIDOS | Diversity and inclusion |
| Aspiration | MAESTRO, DYNAMO, VRTUSO | Aspirational and cool |
| Name | JMANTAS, JESUSM, JMANTS | Personal name variants |

## Texas Plate Rules

- Maximum 7 characters (letters and numbers)
- Spaces, hyphens, periods allowed
- Special symbols: hearts (@), stars (&), Texas silhouette (*)
- All messages reviewed by TxDMV — vulgar/offensive plates will be declined
