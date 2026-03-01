#!/usr/bin/env python3
"""
Texas Vanity Plate Checker
==========================
Generates personalized vanity plate ideas and checks their availability
on myplates.com (Texas's official plate vendor).

Uses Playwright (headless browser) to handle myplates.com's Incapsula
bot protection, which blocks raw HTTP/urllib requests with 403 errors.

Setup:
    pip install playwright
    playwright install chromium

Usage:
    python3 plate_checker.py                    # Check all plates
    python3 plate_checker.py --max-plates 50    # Check first 50
    python3 plate_checker.py --delay 2.0        # Slower (safer)
    python3 plate_checker.py --list-only        # Just list plate ideas
    python3 plate_checker.py --add MYPLATE      # Add a custom plate to check
"""

import json
import time
import sys
import argparse
from datetime import datetime
from collections import OrderedDict


# ═══════════════════════════════════════════════════════════════
#  Configuration
# ═══════════════════════════════════════════════════════════════

PLATE_STYLES = {
    "classic-black-silver":          {"max_chars": 7, "name": "Classic Black & Silver"},
    "black-white-premium-embossed":  {"max_chars": 7, "name": "Black & White Premium Embossed"},
    "lone-star-black":               {"max_chars": 7, "name": "Lone Star Black"},
    "lone-star-red":                 {"max_chars": 7, "name": "Lone Star Red"},
}

DEFAULT_STYLE = "classic-black-silver"

# MyPlates.com API (undocumented, used by their frontend)
API_BASE = "https://www.myplates.com/api/licenseplates/passenger"
DESIGN_BASE = "https://www.myplates.com/design/personalized/passenger"

DEFAULT_DELAY = 1.5
MAX_CONSECUTIVE_BLOCKS = 5
REQUEST_TIMEOUT = 20000  # milliseconds for Playwright


# ═══════════════════════════════════════════════════════════════
#  Plate Idea Generation
# ═══════════════════════════════════════════════════════════════

def generate_plate_ideas():
    """
    Generate vanity plate ideas organized by category, each with a
    description and a "uniqueness" score (higher = more likely to be
    available because it's more niche).

    Personalized for: Jesus Mantas
    - IBM Global Managing Partner (retired 2025), Austin TX
    - Board member at Biogen, WEF AI Council member
    - Spanish heritage (Madrid), served in Spanish Air Force
    - Interests: AI, blockchain/Ethereum, IoT, home automation
    - Passionate about Hispanic diversity in tech (HITEC)
    - Pioneer of enterprise mobile solutions (before iPhone)
    - Master's in Telecom & Software Engineering
    """

    # Each entry: (plate_text, description, category, uniqueness_score)
    # Score: 1-5 (5 = very unique/niche, likely available)
    ideas = []

    # --- AI & Technology (his core career domain) ---
    ideas += [
        ("AIEXEC",  "AI Executive",                         "Tech/AI",    5),
        ("AIBOSS",  "AI Boss",                              "Tech/AI",    4),
        ("AI GURU", "AI Guru",                              "Tech/AI",    3),
        ("AI GUY",  "AI Guy",                               "Tech/AI",    3),
        ("GENAI",   "Generative AI",                        "Tech/AI",    4),
        ("GEN AI",  "Generative AI",                        "Tech/AI",    3),
        ("INNOV8",  "Innovate",                             "Tech/AI",    2),
        ("INNOV8R", "Innovator",                            "Tech/AI",    3),
        ("NVATOR",  "iNnovator",                            "Tech/AI",    5),
        ("DISRPT",  "Disrupt",                              "Tech/AI",    4),
        ("TECHGM",  "Tech General Manager",                 "Tech/AI",    5),
        ("TECHVP",  "Tech VP",                              "Tech/AI",    4),
        ("TEKEXEC", "Tech Executive",                       "Tech/AI",    5),
        ("NEURAL",  "Neural (networks)",                    "Tech/AI",    3),
        ("TENSOR",  "Tensor (deep learning)",               "Tech/AI",    4),
        ("DEEPML",  "Deep Machine Learning",                "Tech/AI",    5),
        ("MLOPS",   "ML Operations",                        "Tech/AI",    4),
        ("QUANTM",  "Quantum computing",                    "Tech/AI",    4),
        ("CLOUD9",  "Cloud Nine",                           "Tech/AI",    2),
        ("DATSCI",  "Data Science",                         "Tech/AI",    5),
        ("IOTECH",  "IoT + Tech",                           "Tech/AI",    5),
        ("BCHAIN",  "Blockchain",                           "Tech/AI",    4),
        ("PROMPT",  "Prompt engineering",                   "Tech/AI",    2),
        ("CODER",   "Coder",                                "Tech/AI",    2),
        ("TECHIE",  "Techie",                               "Tech/AI",    2),
        ("DEVOPS",  "DevOps",                               "Tech/AI",    3),
    ]

    # --- IBM / Career / Consulting ---
    ideas += [
        ("IBMER",   "IBMer",                                "Career",     4),
        ("BIGBLU",  "Big Blue (IBM)",                       "Career",     4),
        ("BIG BLU", "Big Blue (IBM)",                       "Career",     4),
        ("CONSUL",  "Consultant",                           "Career",     3),
        ("CONSLT",  "Consult",                              "Career",     5),
        ("STRTGY",  "Strategy",                             "Career",     5),
        ("MNGPRT",  "Managing Partner",                     "Career",     5),
        ("PARTNR",  "Partner",                              "Career",     3),
        ("BIZTRN",  "Business Transformation",              "Career",     5),
        ("ADVSOR",  "Advisor",                              "Career",     4),
        ("THINKR",  "Thinker (IBM Think)",                  "Career",     4),
        ("THINK",   "Think (IBM motto)",                    "Career",     2),
    ]

    # --- Spanish Heritage ---
    ideas += [
        ("MADRID",  "Madrid, Spain",                        "Heritage",   3),
        ("ESPANA",  "Spain",                                "Heritage",   3),
        ("MANTAS",  "Surname",                              "Heritage",   4),
        ("JMANTAS", "Full handle: J. Mantas",               "Heritage",   5),
        ("ARRIBA",  "Upward / Let's go!",                   "Heritage",   3),
        ("VAMOS",   "Let's go!",                            "Heritage",   3),
        ("GENIO",   "Genius (Spanish)",                     "Heritage",   4),
        ("JEFE",    "Boss (Spanish)",                       "Heritage",   3),
        ("EL JEFE", "The Boss (Spanish)",                   "Heritage",   3),
        ("LIDER",   "Leader (Spanish)",                     "Heritage",   4),
        ("EXITO",   "Success (Spanish)",                    "Heritage",   4),
        ("FUERZA",  "Strength (Spanish)",                   "Heritage",   3),
        ("BRAVO",   "Bravo",                                "Heritage",   2),
        ("FUEGO",   "Fire (Spanish)",                       "Heritage",   2),
        ("TORO",    "Bull (Spanish)",                       "Heritage",   3),
        ("SUENOS",  "Dreams (Spanish)",                     "Heritage",   4),
        ("AVANTE",  "Forward (Spanish)",                    "Heritage",   4),
        ("HOLA",    "Hello (Spanish)",                      "Heritage",   2),
        ("ORGULLO", "Pride (Spanish)",                      "Heritage",   4),
        ("LATINO",  "Latino",                               "Heritage",   2),
        ("HISPNC",  "Hispanic",                             "Heritage",   5),
    ]

    # --- Leadership / Executive ---
    ideas += [
        ("LEADR",   "Leader",                               "Leadership", 3),
        ("MENTOR",  "Mentor",                               "Leadership", 2),
        ("PIONR",   "Pioneer",                              "Leadership", 4),
        ("PIONYR",  "Pioneer",                              "Leadership", 5),
        ("VSNARY",  "Visionary",                            "Leadership", 4),
        ("MOGUL",   "Mogul",                                "Leadership", 2),
        ("TITAN",   "Titan",                                "Leadership", 2),
        ("ICONIC",  "Iconic",                               "Leadership", 2),
        ("LEGEND",  "Legend",                                "Leadership", 1),
        ("TRBLZR",  "Trailblazer",                          "Leadership", 4),
        ("CHMPN",   "Champion",                             "Leadership", 4),
        ("CHIEF",   "Chief",                                "Leadership", 2),
        ("EXECVP",  "Executive VP",                         "Leadership", 5),
        ("BOSS",    "Boss",                                 "Leadership", 1),
        ("CEO",     "CEO",                                  "Leadership", 1),
        ("CTO",     "CTO",                                  "Leadership", 2),
    ]

    # --- Ethereum / Crypto (GitHub interests) ---
    ideas += [
        ("ETHGUY",  "Ethereum Guy",                         "Crypto",     4),
        ("CRYPTO",  "Crypto",                               "Crypto",     1),
        ("HODLR",   "Hodler",                               "Crypto",     3),
        ("HODL",    "Hold On for Dear Life",                "Crypto",     2),
        ("DEFI",    "Decentralized Finance",                "Crypto",     3),
        ("ETHLDR",  "ETH Leader",                           "Crypto",     5),
        ("SATOSH",  "Satoshi",                              "Crypto",     3),
        ("WEB3",    "Web3",                                 "Crypto",     2),
        ("WEB3GM",  "Web3 Good Morning",                    "Crypto",     4),
        ("WAGMI",   "We're All Gonna Make It",              "Crypto",     3),
        ("GWEI",    "Gwei (ETH unit)",                      "Crypto",     4),
        ("TOMOON",  "To the Moon",                          "Crypto",     3),
    ]

    # --- Home Automation (GitHub repos) ---
    ideas += [
        ("SMTHOM",  "Smart Home",                           "HomeAuto",   5),
        ("SMRT HM", "Smart Home",                           "HomeAuto",   4),
        ("HASSIO",  "Home Assistant",                       "HomeAuto",   4),
        ("IOTHOM",  "IoT Home",                             "HomeAuto",   5),
        ("HOMLAB",  "Home Lab",                             "HomeAuto",   4),
        ("HMAUTM",  "Home Automation",                      "HomeAuto",   5),
    ]

    # --- Air Force (served as officer in Spanish Air Force) ---
    ideas += [
        ("FLYBOY",  "Fly Boy",                              "Aviation",   3),
        ("PILOTO",  "Pilot (Spanish)",                      "Aviation",   4),
        ("AVIATO",  "Aviator",                              "Aviation",   3),
        ("TOPGUN",  "Top Gun",                              "Aviation",   2),
        ("MACH1",   "Mach 1",                               "Aviation",   3),
        ("JETSET",  "Jet Set",                              "Aviation",   2),
        ("AIRFRC",  "Air Force",                            "Aviation",   4),
    ]

    # --- Austin / Texas ---
    ideas += [
        ("ATXTEK",  "ATX Tech",                             "Austin/TX",  5),
        ("ATX AI",  "ATX Artificial Intelligence",          "Austin/TX",  4),
        ("AUSTEX",  "Austin Texas",                         "Austin/TX",  4),
        ("TXTECH",  "Texas Tech",                           "Austin/TX",  3),
        ("TXEXEC",  "Texas Executive",                      "Austin/TX",  5),
        ("ATXCEO",  "ATX CEO",                              "Austin/TX",  4),
    ]

    # --- Diversity / Inclusion ---
    ideas += [
        ("INCLSN",  "Inclusion",                            "Diversity",  5),
        ("DIVRSE",  "Diverse",                              "Diversity",  4),
        ("HITEC",   "HITEC org",                            "Diversity",  4),
        ("UNITED",  "United",                               "Diversity",  1),
        ("UNIDOS",  "United (Spanish)",                     "Diversity",  4),
    ]

    # --- Aspirational ---
    ideas += [
        ("GENIUS",  "Genius",                               "Aspiration", 1),
        ("PHENOM",  "Phenomenon",                           "Aspiration", 3),
        ("IMPACT",  "Impact",                               "Aspiration", 2),
        ("LEGACY",  "Legacy",                               "Aspiration", 2),
        ("VISION",  "Vision",                               "Aspiration", 2),
        ("DRIVEN",  "Driven",                               "Aspiration", 2),
        ("THRIVE",  "Thrive",                               "Aspiration", 2),
        ("EVOLVE",  "Evolve",                               "Aspiration", 2),
        ("DYNAMO",  "Dynamo",                               "Aspiration", 3),
        ("MAESTRO", "Maestro",                              "Aspiration", 2),
        ("INSPIR",  "Inspire",                              "Aspiration", 3),
        ("XPLORE",  "Explore",                              "Aspiration", 3),
        ("MAVRCK",  "Maverick",                             "Aspiration", 4),
        ("VRTUSO",  "Virtuoso",                             "Aspiration", 5),
        ("PRODIGY", "Prodigy",                              "Aspiration", 2),
        ("MYTHIC",  "Mythic",                               "Aspiration", 3),
        ("EPIC",    "Epic",                                 "Aspiration", 1),
    ]

    # --- Name Variants ---
    ideas += [
        ("JMANTS",  "J. Mantas abbreviated",               "Name",       5),
        ("JESUSM",  "Jesus M.",                             "Name",       4),
        ("J MNTAS", "J. Mantas",                            "Name",       5),
    ]

    # Deduplicate while preserving order, and filter by max length
    seen = set()
    unique = []
    for text, desc, cat, score in ideas:
        key = text.upper().strip()
        if key not in seen and len(key) <= 7:
            seen.add(key)
            unique.append({
                "plate": key,
                "description": desc,
                "category": cat,
                "uniqueness": score,
            })

    # Sort by uniqueness score (most likely available first)
    unique.sort(key=lambda x: (-x["uniqueness"], x["plate"]))

    return unique


# ═══════════════════════════════════════════════════════════════
#  Browser-Based Availability Checker (Playwright)
# ═══════════════════════════════════════════════════════════════

def create_browser_checker(plate_style=DEFAULT_STYLE, headless=True):
    """
    Create a Playwright browser context for checking plates.

    Returns (playwright, browser, page) tuple. Caller must close them.

    Uses a real Chromium browser to bypass Incapsula bot protection,
    which blocks raw HTTP requests (urllib/requests) with 403 errors.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("\n  Playwright is required but not installed.")
        print("  Install it with:")
        print("    pip install playwright")
        print("    playwright install chromium")
        sys.exit(1)

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 720},
    )
    page = context.new_page()

    # Warm up: visit the homepage first to establish cookies and
    # pass any JavaScript challenges from Incapsula
    print("  Initializing browser session...")
    try:
        page.goto("https://www.myplates.com/", timeout=REQUEST_TIMEOUT,
                   wait_until="domcontentloaded")
        # Give Incapsula JS time to set cookies
        page.wait_for_timeout(3000)
        print("  Browser session ready.\n")
    except Exception as e:
        print(f"  Warning: Homepage load issue: {e}")
        print("  Continuing anyway...\n")

    return pw, browser, page


def check_plate_browser(page, plate_text, plate_style=DEFAULT_STYLE):
    """
    Check a single plate's availability using the browser page.

    Navigates to the API endpoint (which the browser can access since
    it has valid cookies/session from the homepage visit) and checks
    if the response contains '"available'.
    """
    result = {
        "plate": plate_text,
        "available": None,
        "blocked": False,
        "error": None,
        "order_url": f"{DESIGN_BASE}/{plate_style}/{plate_text}",
    }

    api_url = f"{API_BASE}/{plate_style}/{plate_text}"

    try:
        response = page.goto(api_url, timeout=REQUEST_TIMEOUT,
                             wait_until="domcontentloaded")

        if response is None:
            result["error"] = "No response received"
            return result

        status = response.status

        if status == 403:
            # Try reading body - might be Incapsula challenge page
            body = page.content()
            if "incapsula" in body.lower() or "_Incapsula_" in body:
                result["blocked"] = True
                result["error"] = "Blocked by Incapsula"
            else:
                result["error"] = f"HTTP 403 Forbidden"
            return result

        if status != 200:
            result["error"] = f"HTTP {status}"
            return result

        # Read the page body text
        body = page.content()

        if "incapsula" in body.lower():
            result["blocked"] = True
            result["error"] = "Blocked by Incapsula"
            return result

        # Check availability from API response
        if '"available' in body:
            result["available"] = True
        else:
            result["available"] = False

    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            result["error"] = "Request timed out"
        else:
            result["error"] = f"{type(e).__name__}: {error_msg[:60]}"

    return result


def check_plates_batch(plates, plate_style=DEFAULT_STYLE, delay=DEFAULT_DELAY,
                       headless=True):
    """
    Check a batch of plates using Playwright browser.
    """
    results = {
        "available": [],
        "unavailable": [],
        "blocked": [],
        "errors": [],
        "stopped_early": False,
    }
    consecutive_blocks = 0
    total = len(plates)

    pw, browser, page = create_browser_checker(plate_style, headless)

    try:
        for i, plate_info in enumerate(plates, 1):
            plate = plate_info["plate"]
            sys.stdout.write(
                f"\r  [{i:3d}/{total}] Checking: {plate:8s} "
                f"({plate_info['category']:10s}) ... "
            )
            sys.stdout.flush()

            result = check_plate_browser(page, plate, plate_style)
            result["description"] = plate_info["description"]
            result["category"] = plate_info["category"]
            result["uniqueness"] = plate_info["uniqueness"]

            if result["blocked"]:
                consecutive_blocks += 1
                results["blocked"].append(result)
                sys.stdout.write("BLOCKED\n")
                if consecutive_blocks >= MAX_CONSECUTIVE_BLOCKS:
                    print(f"\n  Stopped: {MAX_CONSECUTIVE_BLOCKS} consecutive "
                          f"Incapsula blocks.")
                    print("  Try: --delay 3 or --no-headless (visible browser)")
                    results["stopped_early"] = True
                    break
                # Wait longer after a block
                page.wait_for_timeout(5000)
            elif result["error"]:
                results["errors"].append(result)
                sys.stdout.write(f"ERROR: {result['error'][:45]}\n")
                consecutive_blocks = 0
            elif result["available"]:
                results["available"].append(result)
                sys.stdout.write("AVAILABLE!\n")
                consecutive_blocks = 0
            else:
                results["unavailable"].append(result)
                sys.stdout.write("Taken\n")
                consecutive_blocks = 0

            if i < total:
                # Use Playwright's wait instead of time.sleep for consistency
                page.wait_for_timeout(int(delay * 1000))
    finally:
        browser.close()
        pw.stop()

    return results


# ═══════════════════════════════════════════════════════════════
#  Output / Display
# ═══════════════════════════════════════════════════════════════

BANNER = """
 _____ __  __  ___  _  _ ___ _  _ ___
|_   _|  \\/  |/ _ \\| \\| | __| \\| / __|
  | | | |\\/| | (_) | .` | _|| .` \\__ \\
  |_| |_|  |_|\\___/|_|\\_|___|_|\\_|___/
    Texas Vanity Plate Checker
    myplates.com availability scanner
"""


def print_plate_list(plates):
    """Pretty-print the plate ideas grouped by category."""
    categories = OrderedDict()
    for p in plates:
        cat = p["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)

    print(f"\n  Generated {len(plates)} plate ideas across "
          f"{len(categories)} categories:\n")

    for cat, cat_plates in categories.items():
        print(f"  [{cat}]")
        for p in cat_plates:
            stars = "*" * p["uniqueness"]
            print(f"    {p['plate']:8s}  {p['description']:30s}  "
                  f"uniqueness: {stars}")
        print()


def save_results(results, plates, plate_style, output_file="results.json"):
    """Save detailed results to JSON."""
    style_info = PLATE_STYLES.get(plate_style, {"name": plate_style})

    output = {
        "timestamp": datetime.now().isoformat(),
        "plate_style": plate_style,
        "style_name": style_info.get("name", plate_style),
        "total_ideas": len(plates),
        "total_checked": (
            len(results["available"]) +
            len(results["unavailable"]) +
            len(results["blocked"]) +
            len(results["errors"])
        ),
        "summary": {
            "available": len(results["available"]),
            "unavailable": len(results["unavailable"]),
            "blocked": len(results["blocked"]),
            "errors": len(results["errors"]),
        },
        "available_plates": [
            {
                "plate": r["plate"],
                "description": r.get("description", ""),
                "category": r.get("category", ""),
                "order_url": r.get("order_url", ""),
            }
            for r in results["available"]
        ],
        "unavailable_plates": [r["plate"] for r in results["unavailable"]],
        "errors": [
            {"plate": r["plate"], "error": r.get("error", "")}
            for r in results["errors"]
        ],
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    return output_file


def print_results_summary(results):
    """Print a formatted results summary."""
    total = (
        len(results["available"]) +
        len(results["unavailable"]) +
        len(results["blocked"]) +
        len(results["errors"])
    )

    print(f"\n{'=' * 62}")
    print(f"  RESULTS SUMMARY")
    print(f"{'=' * 62}")
    print(f"  Total Checked  : {total}")
    print(f"  Available      : {len(results['available'])}")
    print(f"  Taken          : {len(results['unavailable'])}")
    print(f"  Blocked        : {len(results['blocked'])}")
    print(f"  Errors         : {len(results['errors'])}")

    if results["available"]:
        print(f"\n{'─' * 62}")
        count = min(20, len(results["available"]))
        print(f"  TOP {count} AVAILABLE PLATES")
        print(f"{'─' * 62}")
        for j, r in enumerate(results["available"][:20], 1):
            desc = r.get("description", "")
            cat = r.get("category", "")
            print(f"  {j:2d}. {r['plate']:8s}  {desc:25s}  [{cat}]")
            print(f"      Order: {r.get('order_url', 'N/A')}")
    else:
        print("\n  No available plates found in this batch.")
        if results["errors"]:
            print("  Check the errors above for details.")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Texas Vanity Plate Checker - "
                    "Check plate availability on myplates.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Setup:
  pip install playwright
  playwright install chromium

Examples:
  python3 plate_checker.py                     # Check all 130+ plates
  python3 plate_checker.py --max-plates 30     # Check top 30 most unique
  python3 plate_checker.py --delay 2.5         # Slower to avoid blocks
  python3 plate_checker.py --list-only         # Preview plate ideas
  python3 plate_checker.py --add "MY NAME"     # Add custom plate(s)
  python3 plate_checker.py --no-headless       # Show the browser window
        """
    )
    parser.add_argument(
        "--delay", type=float, default=DEFAULT_DELAY,
        help=f"Seconds between requests (default: {DEFAULT_DELAY})"
    )
    parser.add_argument(
        "--max-plates", type=int, default=None,
        help="Max plates to check (default: all). Plates are sorted by "
             "uniqueness score, so limiting checks the most niche first."
    )
    parser.add_argument(
        "--plate-style", type=str, default=DEFAULT_STYLE,
        choices=list(PLATE_STYLES.keys()),
        help=f"Plate design style (default: {DEFAULT_STYLE})"
    )
    parser.add_argument(
        "--list-only", action="store_true",
        help="List plate ideas without checking availability"
    )
    parser.add_argument(
        "--add", nargs="+", metavar="PLATE",
        help="Add custom plate text(s) to check"
    )
    parser.add_argument(
        "--no-headless", action="store_true",
        help="Show the browser window (useful for debugging blocks)"
    )
    parser.add_argument(
        "--output", type=str, default="results.json",
        help="Output JSON file (default: results.json)"
    )

    args = parser.parse_args()

    print(BANNER)

    # Generate plate ideas
    plates = generate_plate_ideas()

    # Add custom plates if provided
    if args.add:
        existing = {p["plate"] for p in plates}
        for custom in args.add:
            key = custom.upper().strip()
            if key not in existing and len(key) <= 7:
                plates.insert(0, {
                    "plate": key,
                    "description": "Custom plate",
                    "category": "Custom",
                    "uniqueness": 5,
                })

    if args.list_only:
        print_plate_list(plates)
        return

    # Apply max limit (plates already sorted by uniqueness)
    if args.max_plates:
        plates = plates[:args.max_plates]

    # Filter by character limit
    style_info = PLATE_STYLES.get(
        args.plate_style, {"name": args.plate_style, "max_chars": 7}
    )
    max_chars = style_info["max_chars"]
    plates = [p for p in plates if len(p["plate"].replace(" ", "")) <= max_chars]

    print(f"  Plate Style : {style_info['name']}")
    print(f"  Max Chars   : {max_chars}")
    print(f"  Checking    : {len(plates)} plates")
    print(f"  Delay       : {args.delay}s between requests")
    print(f"  Browser     : {'visible' if args.no_headless else 'headless'}")
    print(f"  Started     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  {'─' * 58}")

    # Run the checker
    results = check_plates_batch(
        plates,
        plate_style=args.plate_style,
        delay=args.delay,
        headless=not args.no_headless,
    )

    # Print summary
    print_results_summary(results)

    # Save results
    out_file = save_results(results, plates, args.plate_style, args.output)
    print(f"\n  Full results saved to: {out_file}")
    print()


if __name__ == "__main__":
    main()
