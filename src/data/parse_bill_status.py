"""
parse_bill_status.py - read downloaded XML files and make two tables
columns starting with label_ come from outcome, don't use as predictors
"""
import xml.etree.ElementTree as ET

import pandas as pd

import config

XML_DIR = config.RAW_DIR / "govinfo"

def parse_one(path):
    """Read ONE xml file. Return a dict for the bill and a list of dicts for its actions
    """
    bill = ET.parse(path).getroot().find("bill") 

    congress = bill.findtext("congress")
    bill_type = (bill.findtext('type') or bill.findtext('billType')).lower()
    number = (bill.findtext('number') or bill.findtext('billNumber'))
    bill_id = f"{congress}-{bill_type}-{number}" # like 118-hr-10

    # first get sponsor. find() returns none when bill has no sponsor so we have to test for that before asking it for text
    # as None has no.findtext
    sponsor = bill.find("sponsors/item")
    if sponsor is None:
        sponsor_id = sponsor_party = sponsor_state = sponsor_district = None
    else:
        sponsor_id = sponsor.findtext("bioguideId")
        sponsor_party = sponsor.findtext('party')
        sponsor_state = sponsor.findtext('state')
        sponsor_district = sponsor.findtext('district')

    # cosponsor who signed on when bill was introduced
    # cosponsors keep growing after introudction, they leak outcome; original sponsor count doesn't
    n_original = 0
    for c in bill.findall('cosponsors/item'):
        if (c.findtext('isOriginalCosponsor') or "").strip().lower() == 'true':
            n_original +=1


    bill_row = {
        "bill_id": bill_id,
        "congress": int(congress),
        'type': bill_type,
        'number': int(number),
        'origin_chamber': bill.findtext('originChamber'),
        'introduced_date': bill.findtext('introducedDate'),
        'title': bill.findtext('title'),
        'sponsor_bioguide': sponsor_id,
        'sponsor_party': sponsor_party,
        'sponsor_state': sponsor_state,
        'sponsor_district': sponsor_district,
        'policy_area': bill.findtext("policyArea/name"), # None when missing
        'n_original_cosponsors': n_original,
        'label_n_laws': len(bill.findall('laws/item')) # outcome!
    }

    action_rows = []
    for a in bill.findall('actions/item'):
        action_rows.append({
                "bill_id": bill_id,
                "action_code": a.findtext("actionCode"),       # text; can contain letters (E40000)
                "action_date": a.findtext("actionDate"),
                "source_system": a.findtext("sourceSystem/name"),
                "action_type": a.findtext("type"),
                "text": a.findtext("text"),
            })
    return bill_row, action_rows    

def main():
    files = sorted(XML_DIR.glob("*/*/*.xml")) # congress / type / file
    if not files:
        raise SystemExit(f"No XML files in {XML_DIR}. Run fetch_bill_status.py first")

    print("xml files found:", len(files))

    bills, actions, bad_files = [], [], []

    for i, path in enumerate(files, start=1):
        try:
            bill_row, action_rows = parse_one(path)
        except(ET.ParseError, AttributeError) as err:
            # ParseError = broken XML; AttributeError = a required tag (type) was missing
            print("COULD NOT PARSE", path.name, type(err).__name__)

            bad_files.append(path.name)
            continue
        bills.append(bill_row)
        actions.extend(action_rows) # extend adds each item; append would add the whole list
        if i % 5000 == 0:
            print(f" parsed {i}/{len(files)}")
    bills = pd.DataFrame(bills)
    actions = pd.DataFrame(actions)


        # checks
    assert not bills['bill_id'].duplicated().any(), "duplicate bill_id"
    print("bills:", len(bills), "| actions:", len(actions), "| unparseable files:", len(bad_files))

    print("bills with no sponsor:", bills['sponsor_bioguide'].isna().sum())
    print("bills with no policy area:", bills['policy_area'].isna().sum())
    print("bills per congress:\n", bills['congress'].value_counts().sort_index().to_string())

    print("most common action codes:\n", actions['action_code'].value_counts().head(10).to_string())

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    bills.to_csv(config.PROCESSED_DIR / "govinfo_bills.csv", index=False)
    actions.to_csv(config.PROCESSED_DIR / "govinfo_actions.csv", index=False)
    print('saved to', config.PROCESSED_DIR)

if __name__ == "__main__":
    main()