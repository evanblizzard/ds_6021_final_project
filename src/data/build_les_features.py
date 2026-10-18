"""
Cleaning up LES data and preventing data leakage.
"""

import pandas as pd
import config

HOUSE_RENAME = {
    "icpsr number, according to poole and rosenthal": "icpsr",
    "1 = majority party member": "majority",
    "seniority, number of terms served counting current": "seniority",
    "1 = committee chair, according to almanac of american politics": "committee_chair",
    "1 = subcommittee chair (or vice chair), according to almanac of american politic": "subcommittee_chair",
    "1 = member of appropriation, rules, or ways and means": "power_committee",
    "dummy = 1 if in first partial or full term, nonconsecutive": "freshman",
    "percent vote received to enter this congress": "vote_share",
    "1 = served in state legislature": "state_leg",
    "1 = majority party leadership": "majority_leadership",
    "1 = minority party leadership": "minority_leadership",
    "size of house delegation from member's state": "delegation_size",
    "lagged les 1.0": "lagged_les",
}

SENATE_RENAME = {
    "icpsr number": "icpsr",
    "1 if senator is in majority party": "majority",
    "seniority": "seniority",
    "1 if senator is a committee chair": "committee_chair",
    "1 if senator is a subcommittee chair": "subcommittee_chair",
    "1 if sit on power committee": "power_committee",
    "1 if freshman senator": "freshman",
    "vote share in last election": "vote_share",
    "1 if senator ever served in state legislature": "state_leg",
    "1 if senator is majority party leader": "majority_leadership",
    "1 if senator is minority party leader": "minority_leadership",
    "number of members in state congressional delegation": "delegation_size",
    "lagged les 1.0": "lagged_les",
}

KEYS = ["icpsr", "congress", "chamber"]
FEATURES = [c for c in HOUSE_RENAME.values() if c != "icpsr"]


# this is necessary because when i combined the House and Senate LES data, columns were named differently so now EVERY version of EVERY column is in the data
# renaming and keeping common ones
def prep_one_chamber(les, chamber, rename):
    """Take on chamber's rows, rename its columns, keep only the common ones"""
    part = les[les['chamber'] == chamber] # boolean mask keeping only rows of whatever chamber was passed in
    # select FIRST, rename SECOND. stacked table has both chamber's columns
    # so renaming everything would create 2 columns w/ same name
    part = part[['congress', 'chamber'] + list(rename)] #list rename to turn dict into list of keys and combine it with the two actual keys
    return part.rename(columns=rename)[KEYS+FEATURES] # swap long names with the ones in the dictionaries above
# [KEYS+FEATURES] puts them in the same order for both chambers
   
def check(df):

    bad = df[df["lagged_les"].isna() != (df["freshman"] == 1)]
    print(bad[["icpsr", "congress", "chamber", "freshman", "lagged_les"]].to_string(index=False))
    print(bad.groupby(["congress", "chamber"]).size())
    """Just something to loudly complain if something goes wrong"""
    assert not df.duplicated(KEYS).any(), "duplicate icpsr, congress, or chamber"

    if len(bad):
        print(f"WARNING: {len(bad)} rows where missing lagged_les doesn't match the freshman flag (likely returning members or special elections)")
    leaky = [c for c in df.columns if "les" in c and c != "lagged_les"] # collect every column containing les except lagged les, if list empty it passes
    assert not leaky, f"leaky columns: {leaky}"


    print("all checks passed")

def check_voteview_match(df):
    """How many LES members in the Voteview table as well?"""
    ideo = pd.read_csv(config.PROCESSED_DIR / "members_ideology.csv")
    ideo = ideo[["icpsr", "congress", "chamber"]].drop_duplicates()
    merged = df.merge(ideo, on=KEYS, how="left", indicator=True)
    matched = (merged["_merge"] == "both").sum()
    print(f"LES rows found in Voteview: {matched}/{len(df)}")
    print("LES rows NOT in Voteview")
    print(merged.loc[merged["_merge"] != "both", KEYS].to_string(index=False))


def main():
    les = pd.read_csv(config.PROCESSED_DIR / "les.csv")

    house = prep_one_chamber(les, "House", HOUSE_RENAME)
    senate = prep_one_chamber(les, "Senate", SENATE_RENAME)

    df = pd.concat([house, senate], ignore_index=True)

    # one House member has no icpsr in the LES file so they can't be joined, dropping them
    print("dropping rows with missing icpsr:", df['icpsr'].isna().sum())
    df = df.dropna(subset=['icpsr'])
    df['icpsr'] = df['icpsr'].astype(int)


    check(df)
    check_voteview_match(df)

    print(df.shape)
    print(df.isna().sum()[lambda s: s > 0 ]) # lambda to show which columns still have NaNs

    out = config.PROCESSED_DIR / "les_features.csv"
    df.to_csv(out, index=False)
    print("wrote", out)


if __name__ == "__main__":
    main()