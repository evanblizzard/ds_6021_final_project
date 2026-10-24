"""
build_model_ready.py. one clean table.

outcome: 1=died, 2=passed its own chamber, 3=law
"""
import pandas as pd
import config
# congress number -> day that congress ended (last day to pass anything)
CONGRESS_END = {116: '2021-01-03', 117: '2023-01-03', 118: '2025-01-03'}

# titles containing these are naming/commemorative bills
COMMEM_PATTERN = "post office|designate the facility|outpatient clinic|commemorative coin|gold medal"

# load data
df = pd.read_csv(config.PROCESSED_DIR / "bills_full_FINAL.csv")
labels = pd.read_csv(config.PROCESSED_DIR / "labels.csv")
n_start = len(df)



# add target (one_to_one each bill id must appear once on both sides)
df = df.merge(labels, on="bill_id", how="left", validate="one_to_one")
assert df['outcome'].notna().all(), "some bills have no label"

# new columns
# days left: how much time bill had. bill introduce late has small chance
end_date = df['congress'].map(CONGRESS_END)
df['days_left_in_congress'] = (pd.to_datetime(end_date) - pd.to_datetime(df['introduced_date'])).dt.days

# commemorative: 1 if title looks like post office or coin or naming bill
df['commemorative'] = df['title'].str.contains(COMMEM_PATTERN, case=False, na=False).astype(int)


# abs_nominate_dim1: how far from center, ignoring left v right
df['abs_nominate_dim1'] = df['nominate_dim1'].abs()

# ficing up columns
df['policy_area'] = df['policy_area'].fillna("Unknown")

# lagged LES is empty for freshmen. flag then fill with 0 to keep those bills
df['lagged_les_missing'] = df['lagged_les'].isna().astype(int)
df['lagged_les'] = df['lagged_les'].fillna(0)

# sponsor_majority = is sponsor in majority party
df['sponsor_majority'] = df['majority']

# senate independents who caucus with the majority count as majority in the 117th/118th
indep = (df["sponsor_party"] == "I") & (df["origin_chamber"] == "Senate") & df["congress"].isin([117, 118])

df.loc[indep, 'sponsor_majority'] = 1
df['sponsor_party'] = df['sponsor_party'].replace({'I': 'Other', 'L': 'Other'}) # tiny parties -> 1 group


# easier names
df = df.rename(columns={
    'committee_chair': 'chair', 'subcommittee_chair': 'subchair', 
    'power_committee': 'power_cmte', 'majority_leadership': 'maj_leader', 
    'minority_leadership': 'min_leader'
})

# drop bills we can't model (sponsor features delegates placeholder bills)

needed = ['sponsor_majority', 'nominate_dim1', 'vote_share', 'seniority']

n_before = len(df)
df = df.dropna(subset=needed)

# keep only columns model should see
# so leaving out label_n_laws and anyhting with actions (reveals outcome)

keep = [
    "bill_id", "congress", "type", "origin_chamber", "introduced_date", "title",
    "sponsor_bioguide_id", "sponsor_party", "sponsor_state", "policy_area",
    "n_original_cosponsors", "days_left_in_congress", "commemorative",
    "sponsor_majority", "icpsr", "nominate_dim1", "nominate_dim2", "abs_nominate_dim1",
    "seniority", "freshman", "chair", "subchair", "power_cmte", "maj_leader", "min_leader",
    "vote_share", "state_leg", "delegation_size", "lagged_les", "lagged_les_missing",
    "outcome",
]

# demographics only exist 
for col in ['female', 'african_american', 'latino']:
    if col in df.columns:
        keep.append(col)
    else:
        print(f"WARNING: no '{col}' column (add to build_les_features)")
df = df[keep]


# check and save
assert not df['bill_id'].duplicated().any()
print("missing values per column:")
print(df.isna().sum()[df.isna().sum()>0].to_string() or "None")
print("\noutcome counts:\n", df['outcome'].value_counts().sort_index().to_string())
df.to_csv(config.PROCESSED_DIR / 'model_ready_billz.csv', index=False)
print('saved model_ready_billz.csv:', df.shape)