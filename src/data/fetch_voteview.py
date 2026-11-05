""" fetch_voteview.py - new script to download Voteview member ideology instead of doing it manually. one csv per congress"""

import pandas as pd
import config

URL = "https://voteview.com/static/data/out/members/HSall_members.csv"

def main():
    config.IDEOLOGY_DIR.mkdir(parents=True, exist_ok=True)
    allm = pd.read_csv(URL)
    for c in config.CONGRESSES:
        allm[allm["congress"] == c].to_csv(config.IDEOLOGY_DIR / f"congress_{c}_ideology.csv", index=False)
        print("saved congress", c)


if __name__ == "__main__":
    main()