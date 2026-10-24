"""
build_labels.py - turn each bill's list of actions into one outcome

outcome: 1 = died (never passed its own chamber)
         2 = passed its own chamber but did not become law
         3 = became law

Helper columns passed_house, passed_senate, law_by_codes, law_by_element are kept for label auditing, not as predictors.
"""
import numpy as np
import pandas as pd
import config

# 1. LOAD
bills = pd.read_csv(config.PROCESSED_DIR / "govinfo_bills.csv")
actions = pd.read_csv(config.PROCESSED_DIR / "govinfo_actions.csv", dtype={"action_code": str})

# keep only library of congress rows bc other sources use different codes
actions = actions[actions['source_system'] == "Library of Congress"].copy()

# mark milestones: 1 if this action row is that milestone, else 0
actions['passed_house'] = (actions['action_code'] == "8000").astype(int)
actions['passed_senate'] = (actions['action_code'] == "17000").astype(int)
actions['became_law'] = (actions['action_code'] == "36000").astype(int)

# one row per bill: max() means did any of this bill's actions hit the milestone (a 1 is the max of 0s)
flags = actions.groupby('bill_id')[['passed_house', 'passed_senate', 'became_law']].max().reset_index()

# attach to bills. left merge to keep bills with no actions; they just get NaN -> 0 
df = bills[['bill_id', 'origin_chamber']].merge(flags, on='bill_id', how='left')
df = df.fillna({'passed_house': 0, 'passed_senate': 0, 'became_law': 0})

# pick outcome

passed_own = (
    ((df['origin_chamber'] == 'House') & (df['passed_house'] == 1))
    | ((df['origin_chamber'] == 'Senate') & (df['passed_senate'] == 1))
)

df['outcome'] = np.select([df['became_law'] == 1, passed_own], [3,2], default=1)

# check and save
print(df['outcome'].value_counts().sort_index())
df[['bill_id', 'outcome']].to_csv(config.PROCESSED_DIR / 'labels.csv', index=False)
print('saved labels.csv:', len(df), 'bills' )