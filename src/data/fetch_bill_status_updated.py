"""fetch_bill_status_updated.py - download govinfo BILLSTATUS zips (one per congress + bill type)"""

import os
import zipfile
import requests
import config

BASE_URL = "https://www.govinfo.gov/bulkdata/BILLSTATUS"
OUT_DIR = config.RAW_DIR / "govinfo"
ZIP_DIR = config.RAW_DIR / "govinfo_zips"

# claude assisted zip download: verified via manual checking of zips and xmls and commenting code manually to ensure understanding
def download(url, dest):
    """stream large file to disk in chunks; write to .tmp then rename so crashes don't break everything"""
    tmp = dest.with_suffix(".zip.tmp")
    with requests.get(url, stream=True, timeout=300) as r: # with as r so streamed connection closes automatically when block ends. stream=True loads bit by bit instead of all at once
        r.raise_for_status()
        with open(tmp, "wb") as f: # open temp file for writing in binary mode
            for chunk in r.iter_content(chunk_size=1 <<20): # specifying one MB at a time. iter_content yields response bit by bit. 
                f.write(chunk)
    os.replace(tmp, dest) # rename the .tmp zip to .zip once complete


def main():
    ZIP_DIR.mkdir(parents=True, exist_ok=True) # create zip directory for zips
    failed = [] # track zips that failed to download
    for congress in config.CONGRESSES: # double for loop to run over every combo: 10 congresses x 4 types = 40 passes
        for bill_type in config.BILL_TYPES:
            name = f"BILLSTATUS-{congress}-{bill_type}.zip" # build the naming pattern EX: BILLSTATUS-110-hr.zip
            zip_path = ZIP_DIR / name
            if not zip_path.exists(): # only download if it doesn't already exist
                try:
                    download(f"{BASE_URL}/{congress}/{bill_type}/{name}", zip_path) # build full url using congress, bill_type, name
                except requests.HTTPError as err: # catches error raise by raise for status and prints why file failed, continue skips to next zip
                    print("FAILED", name, err)
                    failed.append(name)
                    continue
            folder = OUT_DIR / str(congress) / bill_type # build data/raw/govinfo/110/hr
            folder.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path) as z: # open zipfile for reading, with block to close when done
                z.extractall(folder)
            print(f"{congress} {bill_type}: {len(list(folder.glob('*xml')))} xml files")
        print("done.", len(failed), "failed:", failed)


if __name__ == "__main__":
    main()