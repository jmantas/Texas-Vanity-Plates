# Texas Vanity Plate Checker

Generates personalized vanity plate ideas and checks their availability on
[myplates.com](https://www.myplates.com) — Texas's official plate vendor.

## Quick Start

```bash
# No dependencies needed — uses Python standard library only
python3 plate_checker.py
```

## Features

- **131+ personalized plate ideas** across 11 categories (Tech/AI, Heritage,
  Leadership, Crypto, Aviation, and more)
- **Uniqueness scoring** — plates sorted by likelihood of availability (most
  niche first)
- **Rate-limited requests** — respects myplates.com with configurable delays
- **Incapsula bot detection** — auto-stops when blocked, avoids bans
- **Concurrent mode** — check multiple plates at once (use cautiously)
- **JSON export** — full results saved to `results.json`

## Usage

```bash
# Check all 131+ plates (takes ~4 minutes at default 1.5s delay)
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

# Check 2 plates concurrently (faster, but higher block risk)
python3 plate_checker.py --concurrent 2
```

## How It Works

The app queries the undocumented myplates.com API endpoint:
```
https://www.myplates.com/api/licenseplates/passenger/{style}/{plate-text}
```

If the response contains `"available`, the plate is available for purchase.

**Important:** myplates.com uses Incapsula bot protection. The app uses
Python's `urllib` (not `requests`) which avoids detection, per findings from
the [txVanityPlateChecker](https://github.com/bestadamdagoat/txVanityPlateChecker)
project. If you get blocked, try:
- Increasing `--delay` to 3-5 seconds
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
