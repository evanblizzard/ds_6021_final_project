RUN ORDER:

1. load_members.py. Reads Voteview and LES downloads in data/ideology_data and data/les_data. Writes data/processed/members_ideology.csv, les.csv

2. build_les_features.py. Reads les.csv and writes les_features.csv with sponsor power/seniority features

3. fetch_bill_status.py. Reads govinfo.gov BILLSTATUS folders. Writes raw bill xml files

4. parse_bill_status.py. Reads the XML files and writes two CSVs: govinfo_bills.csv and govinfo_actions.csv

5. build_bill_table.py. Reads bills + member_ideology.csv + les_features.csvto create bills_full_FINAL.csv

6. build_labels.py. Reads govinfo_actions.csv and creates labels.csv with bill_id and outcome

7. build_model_ready.py. Reads bills_full_FINAL.csv + labels.csv to create model_ready_bills.csv