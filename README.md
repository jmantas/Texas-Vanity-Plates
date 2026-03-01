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

- **131+ personalized plate ideas** across 11 categories (Tech/AI, Heritage,
  Leadership, Crypto, Aviation, and more)
- **Uniqueness scoring** — plates sorted by likelihood of availability (most
  niche first)
- **Playwright browser engine** — uses a real browser to bypass Incapsula WAF
- **Rate-limited requests** — respects myplates.com with configurable delays
- **Incapsula bot detection** — auto-stops when blocked, avoids bans
- **JSON export** — full results saved to `results.json`

## Usage

```bash
# Check all 131+ plates (takes ~5 minutes at default 1.5s delay)
python3 plate_checker.py

# Check the top 30 most unique/niche plates
python3 plate_checker.py --max-plates 30

# Preview all plate ideas without checking availability
python3 plate_checker.py --list-only

# Slower checking to avoid Incapsula blocks
python3 plate_checker.py --delay 3.0

# Add your own custom plates to check
python3 plate_checker.py --add "MYPLATE" "COOL1"

# Use a specific plate style
python3 plate_checker.py --plate-style black-white-premium-embossed

# Show the browser window (useful for debugging)
python3 plate_checker.py --no-headless
```

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
