"""
build_model_ready.py. one clean table.

outcome: 1=died, 2=passed its own chamber, 3=law
"""
import pandas as pd
import config
# congress number -> day that congress ended (last day to pass anything)


# titles containing these are naming/commemorative bills
COMMEM_PATTERN = "post office|designate the facility|outpatient clinic|commemorative coin|gold medal"


# engineering some unified government features
# who controlled each arm of government in each congress
GOV = {
    109: ("R", "R", "R"), 110: ("R", "D", "D"), 111: ("D", "D", "D"), 112: ("D", "R", "D"),
    113: ("D", "R", "D"), 114: ("D", "R", "R"), 115: ("R", "R", "R"), 116: ("R", "D", "R"),
    117: ("D", "D", "D"), 118: ("D", "R", "D"),
}

# engineering some title related features
TITLE_FLAGS = {
    "t_amend":        r"\bto amend\b",                    # modifies existing law
    "t_reauth":       r"reauthoriz",                      # renews existing programs
    "t_approp":       r"appropriation",
    "t_extend":       r"\bto extend\b",
    "t_establish":    r"\bto establish\b",                # creates something new
    "t_prohibit":     r"\bto prohibit\b",
    "t_require":      r"\bto require\b",
    "t_repeal":       r"\brepeal",
    "t_tax":          r"internal revenue code",
    "t_veterans":     r"veteran",
    "t_designate":    r"\bdesignate\b|\bto name\b|\brename",
    "t_constitution": r"amendment to the constitution",   # essentially never pass
    "t_disapproval":  r"congressional disapproval",       # Congressional Review Act resolutions
    "t_relief":       r"for the relief of",               # private bills
}
# load data
df = pd.read_csv(config.PROCESSED_DIR / "bills_full_FINAL.csv")
labels = pd.read_csv(config.PROCESSED_DIR / "labels.csv")
n_start = len(df)
end_date = pd.to_datetime((1789 + 2 * df["congress"]).astype(str) + "-01-03") # apparently each congress ends on january 3 of year 1789 + 2c (c being congress number)

# creating gov dataframe from dict at top and merging into main dataset
gov = pd.DataFrame.from_dict(GOV, orient="index", columns=["pres_party", "house_maj", "senate_maj"])
df = df.merge(gov, left_on="congress", right_index=True, how="left", validate="many_to_one")

# senate independents caucus with Dems 
is_senate_independent = (df["sponsor_party"] == "I") & (df["origin_chamber"] == "Senate")
caucus = df["sponsor_party"].mask(is_senate_independent, "D")

# majority party of chamber the bill did not start in
other_maj = df["senate_maj"].where(df["origin_chamber"] == "House", df["house_maj"])

df["unified_gov"] = ((df["pres_party"] == df["house_maj"]) & (df["house_maj"] == df["senate_maj"])).astype(int)
df["sponsor_pres_party"] = (caucus == df["pres_party"]).astype(int)
df["other_chamber_same_party"] = (caucus == other_maj).astype(int)
df["sponsor_trifecta"] = ((df["unified_gov"] == 1) & (caucus == df["pres_party"])).astype(int)


# add target (one_to_one each bill id must appear once on both sides)
df = df.merge(labels, on="bill_id", how="left", validate="one_to_one")
assert df['outcome'].notna().all(), "some bills have no label"

# new columns
# days left: how much time bill had. bill introduce late has small chance
end_date = pd.to_datetime((1789 + 2 * df["congress"]).astype(str) + "-01-03")
df['days_left_in_congress'] = (end_date - pd.to_datetime(df['introduced_date'])).dt.days

# commemorative: 1 if title looks like post office or coin or naming bill
df['commemorative'] = df['title'].str.contains(COMMEM_PATTERN, case=False, na=False).astype(int)


# abs_nominate_dim1: how far from center, ignoring left v right
df['abs_nominate_dim1'] = df['nominate_dim1'].abs()


title = df["title_intro"].fillna(df["title"])
df["title_intro_missing"] = df["title_intro"].isna().astype(int)

# binary columns for each category in the TITLE_FLAGS dictionary
for col, pattern in TITLE_FLAGS.items():
    df[col] = title.str.contains(pattern, case=False, regex=True, na=False).astype(int)

df['title_n_words'] = title.str.split().str.len()
df['has_short_title'] = (df["n_short_titles_intro"] > 0).astype(int)



# ficing up columns
df['policy_area'] = df['policy_area'].fillna("Unknown")



# sponsor_majority = is sponsor in majority party
df['sponsor_majority'] = df['majority']

SWITCHES = [ # bioguide, congress, switch_date, majority_after
    ("S000709", 111, "2009-04-30", 1), # specter R -> D
    ("G000557", 111, "2009-12-22", 0), # parker griffith d -> R
    ("V000133", 116, "2019-12-19", 0) # Van Drew D-> R
    
    ]
intro = pd.to_datetime(df["introduced_date"])
for bio, cong, date, after, in SWITCHES: # unpack the tuples into four variables
    rows = (df["sponsor_bioguide_id"] == bio) & (df["congress"] == cong) # identify all bills in specified congress from a sponsor
    df.loc[rows, "sponsor_majority"] = (intro[rows] >= date).map({True: after, False: 1 - after}) # intro date of only selected bills compared with switch date: results in series where True if bill was introduced after switch, False if before
    # then write those values into sponsor_majority columns for selected rows


# senate independents who caucus with the majority count as majority
indep = (df["sponsor_party"] == "I") & (df["origin_chamber"] == "Senate") & df["congress"].isin([110, 111, 112, 113, 114, 115, 116, 117, 118])

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

# Engineered Feature - at start of each congress, first ten bills are reserved for house majority leadership's priority bills
df["leadership_number"] = (df["number"] <= 10).astype(int)

# Engineered Feature - has cosponsors
df["has_cosponsors"] = (df["n_original_cosponsors"] > 0).astype(int) # bill with no cosponsors signals messaging bill


# Engineered Feature - was bill introduced early in the Congress? bills more likely to pass in this period
df["early_intro"] = (df["days_left_in_congress"] > 700).astype(int)

# Engineered Feature - Ideological Distance from chamber's center
chamber_median = df.groupby(["congress", "origin_chamber"])["nominate_dim1"].transform("median")
df["dist_from_median"] = (df["nominate_dim1"] - chamber_median).abs()

# engineered feature - does a bill have cosponsors from opposite party?
df["is_bipartisan"] = (df["n_original_bipartisan"] > 0).astype(int)


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

keep += list(TITLE_FLAGS) + ["title_n_words", "has_short_title", "title_intro_missing"]
keep += ["leadership_number", "has_cosponsors", "early_intro", "dist_from_median", "n_original_bipartisan", "is_bipartisan"]



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
print(df['days_left_in_congress'].describe()) # just checking no day counts are negative