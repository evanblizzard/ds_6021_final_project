| Source | Grain | Rows | Key | Joins to |
|---|---|---|---|---|
| Congress.gov bills | 1 bill | 16,565 | `bill_id` | sponsor `bioguideId` (detail endpoint; 20 pilot bills pulled so far) |
| Voteview ideology | 1 member per congress | 556 | `bioguide_id`, `icpsr` | bills via `bioguide_id`, LES via `icpsr` |
| CEL LES | 1 member per congress | 550 | `icpsr` | Voteview via `icpsr` |



# Source 1: Congress.gov bills (label)
* list endpoint for 118th Congress with about 16,565 bills for 118th Congress
* **keep for modeling** `originChamber`, `type`, `introductionDate`, and `title`
* **Label Source**: `label_latest_action_text` is the bill's last action.
* this could be a problem because latest action is only the last event - A House bill that passed and then sat in the Senate shows 'Received in the Senate and referred to committee` which makes it look like a bill that died. We could use the actions endpoint of the API
* **potential leakage** `actions`, `textVersions`, `summaries`, and `cosponsors` counts from the detail endpoint are measured AFTER the outcome

# Source 2: Voteview Ideology
* one row per member per Congress. `nominate_dim1` is liberal to conservative and `nominate_dim2` is a secondary dimension. `nokken_poole_*` is the same thing but fit one Congress at a time. 
* Party codes: 100 is Democrat, 200 is Republican, 328 is independent

# Source 3: Legislative Effectiveness Scores
* one row per member for the 118th. built from counts of a member's bills at five stages (sponsored, committee action, beyond committee, passed chamber, became law), weighted 1/5/10 by bill type so the average member scores 1
* `lagged les 1.0` is the member's score from the previous congress. Means that freshman Congress members will have no score.
* **potential leakage**: can't use `les 1.0` or `les 2.0` because they use bill outcome data
