"""
Download every page of Congress.gov bill LIST endpoint and save each page as a JSON file
Safe to re-run: pages on disk are skipped.
"""

import json
import time

import requests

import config

def load_page(filename):
    """Return saved page, or None if its missing or half-written"""
    if not filename.exists():
        return None
    else:
        with open(filename) as f:
            return json.load(f)

def main():
    headers = {"X-API-Key": config.get_api_key()}

    for congress in config.CONGRESSES:
        for bill_type in config.BILL_TYPES:
            folder = config.RAW_DIR / str(congress) / bill_type
            folder.mkdir(parents=True, exist_ok=True)

            offset = 0
            while True:
                filename = folder / f"page_{offset}.json"
                data = load_page(filename)

                if data is None:
                    url = f"{config.API_BASE}/{congress}/{bill_type}"
                    params = {"offset": offset, "limit": config.PAGE_SIZE, "format": "json"}

                    response = requests.get(url, params=params, headers=headers, timeout=30)

                    response.raise_for_status() # this will stop loudly at error codes 401, 429, 500

                    data = response.json()
                    with open(filename, "w") as f:
                        json.dump(data, f)
                    time.sleep(1) # be nice to api

                print(congress, bill_type, "offset", offset, "of", data["pagination"]["count"])

                if "next" not in data["pagination"]:
                    break
                offset += config.PAGE_SIZE

if __name__ == "__main__":
    main()