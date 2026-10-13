''' settings that I think every script in this folder will use'''

import os
from pathlib import Path
from dotenv import load_dotenv


# using this instead of ../data so scripts work from any wd
ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
IDEOLOGY_DIR = ROOT / "data" / "ideology_data"
LES_DIR = ROOT / "data" / "les_data"
DETAIL_DIR = RAW_DIR / "bill_details"

CONGRESSES = [118]
BILL_TYPES = ["hr", "s", "hjres", "sjres"]

API_BASE = "https://api.congress.gov/v3/bill"
PAGE_SIZE = 250

def get_api_key() -> str:
    """Read CONGRESS_API_KEY from .env"""
    load_dotenv(ROOT / ".env")
    key = os.environ.get("CONGRESS_API_KEY")
    if not key:
        raise SystemExit(
            f"CONGRESS_API_KEY not found. Put a line CONGRESS_API_KEY=yourkey in .env"
        )
    return key