""" Load Voteview (ideology) and CEL (LES) files, clean, and save"""


import pandas as pd

import config

def load_ideology():
    files = sorted(config.IDEOLOGY_DIR.glob("congress_*_ideology.csv"))
    if not files:
        raise SystemExit(f"No Voteview files found in {config.IDEOLOGY_DIR}")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

    # voteview also lists president and he ain't sponsoring bills
    return df[df["chamber"].isin(["House", "Senate"])]


def load_les():
    house = pd.read_excel(config.LES_DIR / "house_les_all.xlsx")
    senate = pd.read_excel(config.LES_DIR / "senate_les_all.xls") # needs xlrd package?

    # 2 files share most column names, clean them same way

    for df in (house, senate):
        df.columns = df.columns.astype(str).str.strip().str.lower()
    house["chamber"] = "House"
    senate["chamber"] = "Senate"

    # stacking house on top of senate. columns only in one file will be NaN
    les = pd.concat([house, senate], ignore_index=True)

    # renaming silently does nothing if no match, so check it worked
    les = les.rename(columns={"congress number": "congress"})
    if "congress" not in les.columns:
        raise KeyError(f"no congress column in LES files: {list(les.columns)}")
    return les[les["congress"].isin(config.CONGRESSES)]


def main():
    ideology = load_ideology()
    les = load_les()

    print("ideology:", ideology.shape, " | les", les.shape)
    print("ideology missing nominate_dim1:", ideology["nominate_dim1"].isna().sum())
    print("les chamber counts:\n", les["chamber"].value_counts())

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ideology.to_csv(config.PROCESSED_DIR / "members_ideology.csv", index=False)
    les.to_csv(config.PROCESSED_DIR / "les.csv", index=False)
    print("saved to", config.PROCESSED_DIR)


if __name__ == "__main__":
    main()