"""
Turning saved list pages into ONE table with one row per bill
"""

import json
import pandas as pd
import config


def load_all_bills():
    """Collect every bill dict from every saved page into one list"""
    all_bills = []
    for file in sorted(config.RAW_DIR.rglob("page_*.json")): # rglob to find any page #
        with open(file) as f:
            all_bills.extend(json.load(f)["bills"]) #.extend adds each item, not list itself

    return all_bills

def build_bills_table(all_bills):
    df = pd.DataFrame(all_bills)

    # latestAction is a dict per row: json_normalize to spread it into columns

    latest = pd.json_normalize(df['latestAction'])
    latest = latest.rename(
        columns={
            "actionDate": "label_latest_action_date",
            "text": "label_latest_action_text",
            "actionTime": "label_latest_action_time"
        }
    )

    df = pd.concat([df.drop(columns=["latestAction"]), latest], axis=1)

    # almost no bills have actionTime, so it isn't useful

    df = df.drop(columns=["label_latest_action_time"], errors="ignore")

    # bill number alone repeats across types and congresses so combine all three
    df["bill_id"] = df["congress"].astype(str) + "-" + df['type'].str.lower() + "-" + df['number'].astype(str)
    return df

def run_checks(df):
    """ setting up conditions to fail early if something is wrong"""
    assert df["bill_id"].is_unique, "duplicate bill_id - API pages overlapped?"
    print("rows:", len(df))
    print(df.groupby('type').size())
    print("missing values per column:")
    print(df.isna().sum())


def main():
    all_bills = load_all_bills()
    if not all_bills:
        raise SystemExit(f"No pages found under {config.RAW_DIR}. Run fetch_bill_list.py first")
    df = build_bills_table(all_bills)
    run_checks(df)

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = config.PROCESSED_DIR / "bills.csv"
    df.to_csv(out, index=False)
    print('saved', out)

if __name__ == "__main__":
    main()