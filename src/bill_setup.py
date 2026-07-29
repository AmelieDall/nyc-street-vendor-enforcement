import pandas as pd
import time
import re
import requests
import os
from dotenv import load_dotenv

# Setup
load_dotenv()
TOKEN = os.environ.get("LEGISTAR_TOKEN")
BASE = "https://webapi.legistar.com/v1/nyc"

if TOKEN is None:
    raise ValueError("LEGISTAR_TOKEN not found — check your .env file")


def get(endpoint, params=None):
    if params is None:
        params = {}
    params["token"] = TOKEN
    r = requests.get(f"{BASE}{endpoint}", params=params)
    r.raise_for_status()
    return r.json()


# Regex for identifying floor-vote actions in MatterHistoryActionName
FLOOR_ACTIONS = re.compile(r"Approved|Adopted|Passed|Enacted", re.IGNORECASE)


# Pulling votes for a single bill
def pull_bill_votes(matter_id, file_number, direction):
    """
    Route: /matters/{id}/histories
        -> filter to floor-vote actions with an attached EventId
        -> /events/{eventId}/eventitems  (find item matching our MatterId)
        -> /eventitems/{eventItemId}/votes  (individual member votes)
    """
    histories = get(f"/matters/{matter_id}/histories")
    if not histories:
        return []

    floor_histories = [
        h for h in histories
        if h.get("MatterHistoryEventId")
        and FLOOR_ACTIONS.search(h.get("MatterHistoryActionName", ""))
    ]
    if not floor_histories:
        return []

    all_votes = []
    seen_events = set()

    for h in floor_histories:
        event_id = h["MatterHistoryEventId"]
        action = h["MatterHistoryActionName"]
        action_date = h["MatterHistoryActionDate"]
        if event_id in seen_events:
            continue
        seen_events.add(event_id)

        items = get(f"/events/{event_id}/eventitems")
        if not items:
            continue

        our_items = [i for i in items if i.get("EventItemMatterId") == matter_id]
        if not our_items:
            continue

        eid = our_items[0]["EventItemId"]
        votes = get(f"/eventitems/{eid}/votes")
        if not votes:
            continue

        sample = votes[0]
        pid_col = next((c for c in ["VotePersonId", "PersonId"] if c in sample), None)
        name_col = next((c for c in ["VotePersonName", "PersonName"] if c in sample), None)
        val_col = next((c for c in ["VoteValueName", "VoteName", "ValueName"] if c in sample), None)
        if not all([pid_col, name_col, val_col]):
            continue

        for v in votes:
            all_votes.append({
                "file_number": file_number,
                "matter_id": matter_id,
                "direction": direction,
                "action": action,
                "action_date": action_date,
                "event_id": event_id,
                "event_item_id": eid,
                "person_id": v.get(pid_col),
                "person_name": v.get(name_col),
                "vote_value": v.get(val_col),
            })

    return all_votes


# Pulling votes for all enacted bills
def pull_all_votes(enacted_bills, sleep_time=0.2):
    vote_records = []
    for _, row in enacted_bills.iterrows():
        vote_records.extend(
            pull_bill_votes(row['MatterId'], row['MatterFile'], row['direction'])
        )
        time.sleep(sleep_time)
    return pd.DataFrame(vote_records)


# Pull office records to match person to a district
def pull_office_records(sleep_time=0.2):
    office_records = []
    skip = 0
    while True:
        batch = get("/officerecords", {
            "$top": 1000,
            "$skip": skip,
            "$filter": "OfficeRecordBodyName eq 'City Council'"
        })
        if not batch:
            break
        office_records.extend(batch)
        if len(batch) < 1000:
            break
        skip += 1000
        time.sleep(sleep_time)

    offices_df = pd.DataFrame(office_records)
    offices_df["District"] = (
        offices_df["OfficeRecordTitle"]
        .str.extract(r"(\d+)")
        .astype("Int64")
    )
    return offices_df


def build_member_district(offices_df):
    return (
        offices_df
        .sort_values("OfficeRecordStartDate", ascending=False)
        .drop_duplicates(subset="OfficeRecordPersonId")
        [["OfficeRecordPersonId", "OfficeRecordFullName", "District"]]
        .rename(columns={
            "OfficeRecordPersonId": "person_id",
            "OfficeRecordFullName": "member_name"
        })
    )


def build_council_votes(votes_raw, member_district):
    return (
        votes_raw
        .drop_duplicates(subset=["file_number", "event_item_id", "person_id"])
        .merge(member_district, on="person_id", how="left")
        .assign(
            voted_yes=lambda x: x["vote_value"].str.contains(
                "Affirmative|Yea|Yes", case=False, na=False
            ),
            voted_no=lambda x: x["vote_value"].str.contains(
                "Negative|Nay|No", case=False, na=False
            ),
            aligned=lambda x: (
                ((x["direction"] == "pro_vendor") & x["voted_yes"]) |
                ((x["direction"] == "anti_vendor") & x["voted_no"])
            )
        )
        [[
            "file_number", "direction",
            "action", "action_date",
            "person_id", "person_name", "member_name", "District",
            "vote_value", "voted_yes", "voted_no", "aligned"
        ]]
        .sort_values(["file_number", "District", "person_name"])
        .reset_index(drop=True)
    )