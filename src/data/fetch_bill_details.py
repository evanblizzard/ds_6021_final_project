"""
fetch_bill_details.py - download DETAIL record for each bill (sponsor, policy area, etc)"""


import json
import os
import time
import pandas as pd
import requests
import config
SAMPLE = False
    
def main():
    

    bills = pd.read_csv(config.PROCESSED_DIR / "bills.csv")
    if SAMPLE: # if setting at top is true
        bills = bills.groupby("type").sample(n=5, random_state=42)
        # group table by type, then take 5 random rows per group
    print("SAMPLE MODE" if SAMPLE else "FULL RUN", "-", len(bills), "bills")
    headers = {"X-API-Key": config.get_api_key()}
    params = {"format": "json"}

    # create data/raw/bill_details. exist_ok = True means no error if it's already there
    config.DETAIL_DIR.mkdir(parents=True, exist_ok=True)

    failed = []
    for i, bill in enumerate(bills.itertuples(), start=1): # using itertuples to pass me one row at a time as an object. enumerate as a counter starting at 1
        filename = config.DETAIL_DIR / f"{bill.bill_id}.json"  #output path
        if filename.exists():
            continue # already downloaded

        # the type must be lowercase in the URL (HR -> hr)
        url = f"{config.API_BASE}/{bill.congress}/{bill.type.lower()}/{bill.number}" # change url with each iter depending on bill object
        try: # this stupid ass .lower() line will not stop flagging itself as an error but i think it's just because 
            # python isn't sure what data type bill.type will be so it's not sure if .lower() can be used
            # should still work
            response = requests.get(url, params=params, headers=headers, timeout=60)  #  send request
            response.raise_for_status()
        except requests.HTTPError: # if error, tell me i've been rate limited
            if response.status_code == 429: # rate limited, stop, wait, rerun
                raise SystemExit("Rate Limited (429). Wait a minute, then re-run.")
            print("FAILED", bill.bill_id, response.status_code)
            failed.append(bill.bill_id)
            continue
        except requests.RequestException as e:
            print("FAILED", bill.bill_id, type(e).__name__)
            failed.append(bill.bill_id)
            time.sleep(5)
            continue


        # writing to a temporary name first, then renaming 
        # if computer dies mid-write only the .tmp file is left half finished and full file never gets created
        tmp = filename.with_suffix(".json.tmp")
        with open(tmp, 'w') as f:
            json.dump(response.json(), f) # dump write Python dict as json text
        for attempt in range(5):
            try:
                os.replace(tmp, filename)  # rename it to the real name
                break
            except PermissionError:
                time.sleep(0.5)  # file briefly locked by antivirus/OneDrive; wait and retry
        else:
            print("FAILED rename", bill.bill_id)
            failed.append(bill.bill_id)
            continue # rename it to the real name

        print(f"{i}/{len(bills)}", bill.bill_id, response.status_code) # progress printer
        time.sleep(1) # be nice to API

    print("done.", len(failed), "failed:", failed)

if __name__ == "__main__":
    main()