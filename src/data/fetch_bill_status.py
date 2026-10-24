"""
fetch_bill_status.py - download govinfo BILLSTATUS xml files, one per bill
should be safe to re-run, files on desk should be skipped
"""

import os
import re
import time
import requests
import config


SAMPLE = False # to test before full run, just pull a few

BASE_URL = "https://www.govinfo.gov/bulkdata/BILLSTATUS"
CONGRESSES = [116, 117, 118]
BILL_TYPES = ['hr', 's', 'hjres', 'sjres'] # types that can become law
PAUSE = 0.2 # pause between downloads to be nice

OUT_DIR = config.RAW_DIR / "govinfo"


def list_files(congress, bill_type):
    """
    ask govinfo which XML files exist in one folder. EX: .../BILLSTATUS/118/hr
    """
    response = requests.get(f"{BASE_URL}/{congress}/{bill_type}", timeout=60)

    # folder page is html that mentions every file name; pull names out of it
    

    # \d+: regex to match one or more digits (bill number). 
    pattern = rf"BILLSTATUS-{congress}{bill_type}\d+\.xml"
    names = sorted(set(re.findall(pattern, response.text))) # casting to set will remove repeats

    return names

def main():
    print("Sample mode" if SAMPLE else "FULL RUN")
    session = requests.Session() # reuse on connection bc faster than requests.get() each time
    failed = []

    for congress in CONGRESSES:
        for bill_type in BILL_TYPES:
            names = list_files(congress, bill_type)
            print(f"{congress} {bill_type}: {len(names)} files listed")
            if SAMPLE:
                names = names[:5]

            folder = OUT_DIR / str(congress) / bill_type
            folder.mkdir(parents=True, exist_ok=True)

            for i, name in enumerate(names, start=1):
                filename = folder / name
                if filename.exists():
                    continue # already downloaded

                url = f"{BASE_URL}/{congress}/{bill_type}/{name}"

                try:
                    response = session.get(url, timeout=60)
                    response.raise_for_status()
                    #print(response.status_code, response.headers.get("Content-Type"), len(response.text))
                    #print(response.text[:500]) 
                except requests.HTTPError:
                    print("FAILED", name, response.status_code)
                    failed.append(name)
                    continue

                # write to temporary name first, then rename, so a crash can't leave a half-written xml
                tmp = filename.with_suffix(".xml.tmp")
                with open(tmp, "wb") as f: # 'wb' = write bytes, xml saved exactly as sent
                    f.write(response.content)
                os.replace(tmp, filename)

                if i % 500 == 0: # print a line every 500 files to verify still working
                    print(f" {congress} {bill_type}: {i}/{len(names)}")

                time.sleep(PAUSE)

        print("done.", len(failed), "failed:", failed[:20])


if __name__ == "__main__":
    main()