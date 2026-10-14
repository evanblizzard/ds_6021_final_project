"""
build_bill_sponsors.py - read saved bill details, pull out each bill's sponsor, and attach the sponsor's Voteview ideology scores

"""

import pandas as pd
import json
import config

def build_sponsor_table():
    """One row per downloaded bill: bill_id, sponsor Bioguide ID, party, state"""
    rows = []
    # for every json file of bill detail data
    for file in sorted(config.DETAIL_DIR.glob("*.json")):
        with open(file) as f: # open json and load it into python dict
            bill = json.load(f)['bill'] # ['bill'] because api wraps each record in top-level bill key, indexing inside it
        sponsors = bill.get("sponsors", []) # returns sponsors list or empty list if key is missing. .get won't crash on missing key
        sponsor = sponsors[0] if sponsors else {} # takes first sponsor, or empty dict if list is empty

        rows.append({
            "bill_id": file.stem, # filename - ".json"
            "sponsor_bioguide_id": sponsor.get("bioguideId"),
            "sponsor_party": sponsor.get("party"),
            "sponsor_state": sponsor.get("state"),
        })
    return pd.DataFrame(rows) # turn list of dicts into dataframe

def load_ideology():
    """Voteview scores, one row per (member, Congress)"""
    ideology = pd.read_csv(config.PROCESSED_DIR / "members_ideology.csv")
    ideology = ideology.rename(columns={"bioguide_id": "sponsor_bioguide_id"}) # rename id column to match sponsor table
    ideology = ideology[["sponsor_bioguide_id", "congress", "nominate_dim1", "nominate_dim2"]] # keep only four columns we need

    # some members appear twice in one congress (eg House to Senate move, party swap)
    # rule for now is keep first row
    n_before = len(ideology)
    ideology = ideology.drop_duplicates(subset=["sponsor_bioguide_id", "congress"], keep="first")
    print("Ideology rows dropped as duplicates:", n_before - len(ideology))
    return ideology

def main():
    # load bill list and build sponsor table
    # stop if no json files at all

    bills = pd.read_csv(config.PROCESSED_DIR / "bills.csv")
    sponsors = build_sponsor_table()
    if sponsors.empty:
        raise SystemExit(f"No detail files found in {config.DETAIL_DIR}. Run fetch_bill_details.py first")
    print("detail files read:", len(sponsors))


    # bills -> sponsor
    # attach sponsor info to each bill
    # left join to keep every bill 
    # one to one to raise error if any bill_id appears twice on either side
    df = bills.merge(sponsors, on="bill_id", how="left", validate="one_to_one")


    # sponsor -> ideology
    # attach ideology scores
    # indicator=True to add a _merge column to indicate whether each row found a match
    df = df.merge(
        load_ideology(),
        on=['sponsor_bioguide_id', "congress"],
        how="left",
        validate = "many_to_one", # many bills per member, one row per member-congress pair
        indicator=True 
    )

    # Match rate: only bills with a sponsor can be matched
    # count matches only among bills with a sponsor
    # bills with no sponsor can't match and would make rate look worse than it is
    has_sponsor = df[df['sponsor_bioguide_id'].notna()]
    
    print("bills with a sponsor:", len(has_sponsor), "of", len(df))
    # left only means bill had a sponsor id but voteview had no row
    print("Voteview match for those bills:\n", has_sponsor["_merge"].value_counts())
    unmatched = has_sponsor[has_sponsor["_merge"] == "left_only"]
    if len(unmatched):
        print("unmatched sponsors:\n", unmatched[["bill_id", "sponsor_bioguide_id"]])

    out = config.PROCESSED_DIR / "bills_with_sponsors.csv"
    # drop the _merge helper column and save result
    df.drop(columns="_merge").to_csv(out, index=False)
    print("saved", out)

if __name__ == "__main__":
    main()