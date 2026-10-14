"""
build_bill_table.py - attach LES features to each bill via its sponsor.

"""
import pandas as pd
import config


# three columns that ID one LES row. merge on all three
KEYS = ['icpsr', 'congress', 'chamber']

def load_crosswalk():
    # read members_ideology.csv, keep bioguide_id, congress, icpsr
    crosswalk = pd.read_csv(config.PROCESSED_DIR / 'members_ideology.csv')
    # only keeping the three columns necessary to translate ids
    crosswalk = crosswalk[['bioguide_id', 'congress', 'icpsr']]
    crosswalk = crosswalk.rename(columns={'bioguide_id': "sponsor_bioguide_id"})


    # manchin has two rows with different icpsr (40915 = Democrat, 90915 = independent)
    # les file only knows 40915 so im dropping the other one
    bad_row = (crosswalk['sponsor_bioguide_id'] == "M001183") & (crosswalk['icpsr'] == 90915)
    crosswalk = crosswalk[~bad_row] # ~ inverts truth so this will keep everything but bad row

    # schiff and kim have a house row and senate row with same icpsr
    # doesn't really matter which one we keep
    crosswalk  = crosswalk.drop_duplicates(subset=['sponsor_bioguide_id', 'congress'], keep='first')

    # stop the script if the table isn't one-row-per-pair
    assert not crosswalk.duplicated(['sponsor_bioguide_id', 'congress']).any() # final check for duplicates


    return crosswalk

def main():
    bills = pd.read_csv(config.PROCESSED_DIR / 'bills_with_sponsors.csv')
    n_bills = len(bills) # doing a left merge, don't want this to change
    # add icpsr to each bill


    # add each bill's sponsor icpsr to bills
    df = bills.merge(
        load_crosswalk(),
        on=['sponsor_bioguide_id', 'congress'], # match on id and congress
        how='left', # keep every bill even if no icpsr found
        validate='many_to_one', # many bills per sponsor, one crosswalk row each
    )

    # sponsor sits in chamber bill started in
    # copy originChamber into a column named like one in LES table
    df['chamber'] = df['originChamber']

    # add les features
    les = pd.read_csv(config.PROCESSED_DIR / 'les_features.csv')
    df = df.merge(
        les,
        on=KEYS, # icpsr + congress + chamber must match
        how='left', # bills without match get NaN in les column
        validate='many_to_one', # one LES row per member congress chamber
        indicator=True # add a _merge column where "both" = matched, "left_only" = not
    )

    # checks: left merge shouldn't change number of bills
    assert len(df) == n_bills, f"row count changed: {n_bills} -> {len(df)}"
    assert not df['bill_id'].duplicated().any()

    # report!
    has_icpsr = df['icpsr'].notna() # true for bills whose sponsor could be translated

    print("bills:", n_bills) # total num bills
    print("bills witha sponsor icpsr:", has_icpsr.sum()) # count the trues
    print("bills with LES features:     ", (df['_merge'] == "both").sum())
    # sponsors we translated but LES didn't know: has an icpsr but merge said not "both"
    lost = df[has_icpsr & (df['_merge'] != "both")]
    lost = lost[['sponsor_bioguide_id', 'chamber']].drop_duplicates() # one line per person
    print(f"sponsors with an icpsr but no les row: {len(lost)} (first 20 below)")
    print(lost.head(20).to_string(index=False))

    # save to csv, dropping _merge column bc it was just a helper
    out = config.PROCESSED_DIR / "bills_full.csv"
    df.drop(columns="_merge").to_csv(out, index=False)
    print("saved", out)



if __name__ == "__main__":
    main()