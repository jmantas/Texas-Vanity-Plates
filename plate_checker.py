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
import re
import argparse
import itertools
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
#  Paragraph-Based Plate Generator
# ═══════════════════════════════════════════════════════════════

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "this", "that",
    "these", "those", "i", "me", "my", "we", "our", "you", "your", "he",
    "she", "it", "they", "them", "its", "his", "her", "their", "who",
    "whom", "which", "what", "where", "when", "how", "not", "no", "nor",
    "as", "if", "so", "than", "too", "very", "just", "about", "also",
    "into", "over", "such", "am", "up", "out", "like", "more", "most",
    "own", "same", "other", "each", "every", "both", "few", "all", "any",
    "some", "many", "much", "us", "been", "then", "there", "here",
}

LEET_MAP = {"A": "4", "E": "3", "I": "1", "O": "0", "S": "5", "T": "7", "B": "8"}

NUMBER_SUBS = {
    "one": "1", "won": "1", "two": "2", "to": "2", "too": "2",
    "three": "3", "for": "4", "four": "4", "fore": "4", "five": "5",
    "six": "6", "seven": "7", "ate": "8", "eight": "8", "nine": "9",
    "ten": "10",
}

PLATE_SUFFIXES = ["R", "RX", "GUY", "MAN", "PRO", "GM", "TX", "1", "GO", "NUT"]
PLATE_PREFIXES = ["MR", "DR", "TX", "MY", "GO", "LUV", "NO1"]


def _extract_keywords(paragraph):
    """Extract meaningful keywords from a paragraph."""
    text = re.sub(r"[^\w\s-]", " ", paragraph.lower())
    words = text.split()
    keywords = []
    seen = set()
    for w in words:
        w = w.strip("-_")
        if w and w not in STOP_WORDS and len(w) >= 2 and w not in seen:
            seen.add(w)
            keywords.append(w)
    return keywords


def _drop_vowels(word):
    """Remove vowels from a word, keeping the first letter."""
    if len(word) <= 1:
        return word
    return word[0] + "".join(c for c in word[1:] if c.upper() not in "AEIOU")


def _leetspeak(word):
    """Apply leetspeak substitutions."""
    return "".join(LEET_MAP.get(c.upper(), c) for c in word)


def _partial_leet(word):
    """Leetspeak only on vowels."""
    return "".join(
        LEET_MAP[c.upper()] if c.upper() in LEET_MAP and c.upper() in "AEIOU" else c
        for c in word
    )


def _truncate_smart(word, max_len=7):
    """Truncate at a consonant boundary for readability."""
    word = word[:max_len]
    if len(word) > 3 and word[-1].upper() in "AEIOU":
        word = word[:-1]
    return word[:max_len]


def _score_plate(plate_text, technique_score=3):
    """
    Score a plate for wow factor (1–10).
    Higher = more creative, readable, and likely available.
    """
    score = technique_score
    text = plate_text.replace(" ", "")

    # Length bonus: short plates are punchy
    if len(text) <= 4:
        score += 2
    elif len(text) <= 5:
        score += 1

    # Readability: good vowel-to-consonant ratio
    vowels = sum(1 for c in text if c in "AEIOU0134")  # digits that read as vowels
    ratio = vowels / max(len(text), 1)
    if 0.25 <= ratio <= 0.50:
        score += 1

    # Clever number+letter mix
    has_num = any(c.isdigit() for c in text)
    has_alpha = any(c.isalpha() for c in text)
    if has_num and has_alpha:
        score += 1

    # Penalty: all consonants = unreadable
    real_vowels = sum(1 for c in text if c in "AEIOU")
    if real_vowels == 0 and len(text) > 4:
        score -= 2

    return max(1, min(10, score))


def generate_plates_from_description(paragraph, target_count=500):
    """
    Generate vanity plate ideas from a freeform paragraph.

    Uses truncation, vowel-dropping, leetspeak, word combinations,
    prefixes/suffixes, and creative encoding to produce up to
    target_count plates, sorted by wow factor.
    """
    keywords = _extract_keywords(paragraph)

    if not keywords:
        print("  Warning: No usable keywords found in description.")
        return []

    # Extract bigrams (adjacent non-stop-word pairs)
    raw_words = [w.strip(".,!?;:\"'()") for w in paragraph.lower().split()]
    bigrams = []
    for i in range(len(raw_words) - 1):
        a, b = raw_words[i], raw_words[i + 1]
        if (a not in STOP_WORDS and b not in STOP_WORDS
                and len(a) >= 2 and len(b) >= 2):
            bigrams.append((a, b))

    candidates = {}  # plate_text → dict

    def add(plate, desc, tech_score=3):
        p = plate.upper().strip()
        cleaned = re.sub(r"[^A-Z0-9 .\-]", "", p)
        if cleaned != p or len(p) > 7 or len(p) < 2:
            return
        if p not in candidates:
            candidates[p] = {
                "plate": p,
                "description": desc,
                "wow_score": _score_plate(p, tech_score),
            }

    # ── Per-keyword transforms ───────────────────────────────
    for kw in keywords:
        u = kw.upper()

        add(u, kw.title(), 3)
        add(_truncate_smart(u), f"{kw.title()} (abbr)", 4)
        add(_drop_vowels(u), f"{kw.title()} (no vowels)", 5)
        add(_leetspeak(u)[:7], f"{kw.title()} (leet)", 4)
        add(_partial_leet(u)[:7], f"{kw.title()} (num sub)", 4)

        # Compressed: first 3 + last letter
        if len(u) > 4:
            add(u[:3] + u[-1], f"{kw.title()} (short)", 5)
            add(u[:4] + u[-1], f"{kw.title()} (short)", 4)

        # Spaced in middle
        if 4 <= len(u) <= 6:
            mid = len(u) // 2
            add(u[:mid] + " " + u[mid:], f"{kw.title()} (spaced)", 3)

        # With suffixes
        for sfx in PLATE_SUFFIXES:
            room = 7 - len(sfx)
            add(_drop_vowels(u)[:room] + sfx, f"{kw.title()} + {sfx}", 5)
            add(u[:room] + sfx, f"{kw.title()} + {sfx}", 4)

        # With prefixes
        for pfx in PLATE_PREFIXES:
            room = 7 - len(pfx)
            add(pfx + u[:room], f"{pfx} + {kw.title()}", 4)
            add(pfx + _drop_vowels(u)[:room], f"{pfx} + {kw.title()} (dv)", 5)

        # Number substitutions within the word
        for word, num in NUMBER_SUBS.items():
            if word in kw:
                add(kw.replace(word, num).upper()[:7], f"{kw.title()} ({word}→{num})", 6)

    # ── Bigram transforms ────────────────────────────────────
    for a, b in bigrams:
        au, bu = a.upper(), b.upper()

        add((au + bu)[:7], f"{a.title()} {b.title()}", 3)
        add(au[0] + bu[:6], f"{a[0].upper()}.{b.title()}", 4)
        add(au[:6] + bu[0], f"{a.title()}.{b[0].upper()}", 4)
        add((_drop_vowels(au) + _drop_vowels(bu))[:7],
            f"{a.title()} {b.title()} (dv)", 5)

        # Split combos
        for s1, s2 in [(3, 4), (4, 3), (3, 3), (2, 5), (5, 2), (2, 4), (4, 2)]:
            if s1 + s2 <= 7:
                add(au[:s1] + bu[:s2], f"{a.title()}+{b.title()}", 4)

        # Vowel-dropped splits
        add(_drop_vowels(au)[:3] + bu[:4], f"{a.title()}(dv)+{b.title()}", 5)
        add(au[:4] + _drop_vowels(bu)[:3], f"{a.title()}+{b.title()}(dv)", 5)

        # Spaced combos
        for s1, s2 in [(3, 3), (2, 4), (4, 2), (2, 3), (3, 2)]:
            if s1 + s2 + 1 <= 7:
                add(au[:s1] + " " + bu[:s2], f"{a.title()} {b.title()}", 4)

        # Leet combos
        add(_leetspeak(au)[:3] + bu[:4], f"{a.title()}(l)+{b.title()}", 5)
        add(au[:4] + _leetspeak(bu)[:3], f"{a.title()}+{b.title()}(l)", 5)

    # ── Trigram transforms ───────────────────────────────────
    for i in range(len(raw_words) - 2):
        ws = [raw_words[j].strip(".,!?;:\"'()") for j in range(i, i + 3)]
        if all(w not in STOP_WORDS and len(w) >= 2 for w in ws):
            initials = "".join(w[0].upper() for w in ws)
            add(initials, ".".join(w[0].upper() for w in ws), 6)
            add(ws[0].upper()[:4] + initials[1:], f"{ws[0].title()} + initials", 5)

            # 2+2+3 and 3+2+2 combos
            for s1, s2, s3 in [(2, 2, 3), (3, 2, 2), (2, 3, 2)]:
                if s1 + s2 + s3 <= 7:
                    c = ws[0][:s1].upper() + ws[1][:s2].upper() + ws[2][:s3].upper()
                    add(c, f"{ws[0].title()} {ws[1].title()} {ws[2].title()}", 5)

    # ── Cross-keyword combinations (all pairs) ───────────────
    kw_limit = min(len(keywords), 40)
    for a, b in itertools.combinations(keywords[:kw_limit], 2):
        au, bu = a.upper(), b.upper()
        add((au[:3] + bu[:4])[:7], f"{a.title()}+{b.title()}", 3)
        add((au[:4] + bu[:3])[:7], f"{a.title()}+{b.title()}", 3)
        add((_drop_vowels(au)[:4] + _drop_vowels(bu)[:3])[:7],
            f"{a.title()}+{b.title()} (dv)", 4)
        add((au[:3] + " " + bu[:3])[:7], f"{a.title()} {b.title()}", 3)
        add((au[0] + bu)[:7], f"{a[0].upper()}.{b.title()}", 4)
        add((au + bu[0])[:7], f"{a.title()}.{b[0].upper()}", 4)
        if len(candidates) >= target_count * 2:
            break

    # ── Digit suffix padding (if still under target) ─────────
    if len(candidates) < target_count:
        for plate in list(candidates.keys()):
            if 3 <= len(plate) <= 6:
                base = candidates[plate]
                for n in "0123456789":
                    add(plate + n, f"{base['description']}+{n}",
                        max(1, base["wow_score"] - 1))
                if len(candidates) >= target_count * 2:
                    break

    # ── Second-pass suffix padding with 2-digit ──────────────
    if len(candidates) < target_count:
        for plate in list(candidates.keys()):
            if 3 <= len(plate) <= 5:
                base = candidates[plate]
                for n in ["01", "11", "22", "33", "42", "69", "77", "88", "99"]:
                    add(plate + n, f"{base['description']}+{n}",
                        max(1, base["wow_score"] - 2))
                if len(candidates) >= target_count * 2:
                    break

    # Sort by wow factor, take top N
    plates = sorted(candidates.values(), key=lambda x: (-x["wow_score"], x["plate"]))
    plates = plates[:target_count]

    result = []
    for p in plates:
        result.append({
            "plate": p["plate"],
            "description": p["description"],
            "category": "Generated",
            "uniqueness": max(1, min(5, (p["wow_score"] + 1) // 2)),
            "wow_score": p["wow_score"],
        })

    return result


def save_generated_plates(plates, output_file="input.json"):
    """Save generated plates to a JSON file for later checking."""
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_plates": len(plates),
        "plates": plates,
    }
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    return output_file


def load_plates_from_file(input_file):
    """Load plates from a JSON file (e.g., input.json from --generate)."""
    with open(input_file, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        raw_plates = data
    elif "plates" in data:
        raw_plates = data["plates"]
    else:
        raise ValueError(f"Unrecognized JSON format in {input_file}. "
                         f"Expected a list or {{\"plates\": [...]}}.")

    result = []
    for p in raw_plates:
        if isinstance(p, str):
            result.append({
                "plate": p.upper().strip(),
                "description": "",
                "category": "Input",
                "uniqueness": 3,
                "wow_score": 5,
            })
        elif isinstance(p, dict):
            result.append({
                "plate": p.get("plate", "").upper().strip(),
                "description": p.get("description", ""),
                "category": p.get("category", "Input"),
                "uniqueness": p.get("uniqueness", 3),
                "wow_score": p.get("wow_score", 5),
            })

    return [p for p in result if 2 <= len(p["plate"]) <= 7]


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
            result["wow_score"] = plate_info.get("wow_score",
                                                  plate_info["uniqueness"] * 2)

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
                "uniqueness": r.get("uniqueness", 3),
                "wow_score": r.get("wow_score", 5),
                "order_url": r.get("order_url", ""),
            }
            for r in sorted(results["available"],
                            key=lambda x: (-x.get("wow_score", 0),
                                           -x.get("uniqueness", 0),
                                           x["plate"]))
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
        # Sort by wow factor for display
        ranked = sorted(results["available"],
                        key=lambda x: (-x.get("wow_score", 0),
                                       -x.get("uniqueness", 0),
                                       x["plate"]))
        print(f"\n{'─' * 62}")
        count = min(20, len(ranked))
        print(f"  TOP {count} AVAILABLE PLATES (by wow factor)")
        print(f"{'─' * 62}")
        for j, r in enumerate(ranked[:20], 1):
            desc = r.get("description", "")
            cat = r.get("category", "")
            wow = r.get("wow_score", "?")
            print(f"  {j:2d}. {r['plate']:8s}  {desc:25s}  [{cat}]  wow:{wow}")
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
  python3 plate_checker.py                                 # Check all built-in plates
  python3 plate_checker.py --generate "I love AI and cars" # Generate 500 ideas → input.json
  python3 plate_checker.py --input input.json              # Check plates from file
  python3 plate_checker.py --max-plates 30                 # Check top 30 most unique
  python3 plate_checker.py --delay 2.5                     # Slower to avoid blocks
  python3 plate_checker.py --list-only                     # Preview plate ideas
  python3 plate_checker.py --add "MY NAME"                 # Add custom plate(s)
  python3 plate_checker.py --no-headless                   # Show the browser window
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
    parser.add_argument(
        "--generate", type=str, metavar="DESCRIPTION",
        help="Generate 500 plate ideas from a paragraph description "
             "and save to input.json. Does not check availability."
    )
    parser.add_argument(
        "--input", type=str, metavar="FILE",
        help="Load plates from a JSON file (e.g., input.json created "
             "by --generate) instead of using built-in plate ideas"
    )

    args = parser.parse_args()

    print(BANNER)

    # ── Generate mode: create input.json and exit ─────────────
    if args.generate:
        print(f"  Generating plate ideas from description...\n")
        print(f"  Description: \"{args.generate[:80]}{'...' if len(args.generate) > 80 else ''}\"\n")
        plates = generate_plates_from_description(args.generate, target_count=500)
        out = save_generated_plates(plates, "input.json")
        print(f"  Generated {len(plates)} plate ideas.")
        print(f"  Saved to: {out}")
        print(f"\n  Next step: check availability with:")
        print(f"    python3 plate_checker.py --input input.json")
        print()

        # Also show a preview of the top plates
        top = plates[:15]
        print(f"  Top {len(top)} plates by wow factor:")
        print(f"  {'─' * 50}")
        for i, p in enumerate(top, 1):
            print(f"  {i:3d}. {p['plate']:8s}  wow:{p['wow_score']:2d}  {p['description']}")
        print()
        return

    # ── Load plates from file or generate built-in list ───────
    if args.input:
        print(f"  Loading plates from: {args.input}")
        plates = load_plates_from_file(args.input)
        print(f"  Loaded {len(plates)} plates.\n")
    else:
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
                    "wow_score": 8,
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
