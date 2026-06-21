"""Fetch Man City fixtures from football-data.org and output fixtures.json"""
import urllib.request
import json
import os
import sys

API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
TEAM_ID = 65  # Manchester City

CATEGORY_MAP = {
    "PL": "premier-league",
    "CL": "champions-league",
    "FAC": "fa-cup",
    "ELC": "league-cup",
    "CS": "community-shield",
}

STATIC_ENTRIES = [
    {"slotType": "weekend", "date": "2026-08-16", "category": "community-shield", "label": "Arsenal (N \u2013 Principality Stadium, Cardiff)"},
    {"slotType": "break", "date": "2026-09-21", "dateEnd": "2026-10-06", "category": "international", "label": "International Break"},
    {"slotType": "break", "date": "2026-11-09", "dateEnd": "2026-11-17", "category": "international", "label": "International Break"},
    {"slotType": "break", "date": "2027-03-22", "dateEnd": "2027-03-30", "category": "international", "label": "International Break"},
]

# Estimated cup dates (used until real fixtures appear from API)
ESTIMATED_CUP_ENTRIES = [
    {"slotType": "midweek", "date": "2026-09-15", "dateEnd": "2026-09-16", "category": "league-cup", "label": "Carabao Cup Round 3"},
    {"slotType": "midweek", "date": "2026-10-27", "dateEnd": "2026-10-28", "category": "league-cup", "label": "Carabao Cup Round 4"},
    {"slotType": "midweek", "date": "2026-12-15", "dateEnd": "2026-12-16", "category": "league-cup", "label": "Carabao Cup Quarter-Final"},
    {"slotType": "midweek", "date": "2027-01-12", "dateEnd": "2027-01-13", "category": "league-cup", "label": "Carabao Cup Semi-Final 1st Leg"},
    {"slotType": "midweek", "date": "2027-02-02", "dateEnd": "2027-02-03", "category": "league-cup", "label": "Carabao Cup Semi-Final 2nd Leg"},
    {"slotType": "weekend", "date": "2027-03-21", "category": "league-cup", "label": "Carabao Cup Final (Wembley)"},
    {"slotType": "weekend", "date": "2027-01-09", "dateEnd": "2027-01-10", "category": "fa-cup", "label": "FA Cup Third Round"},
    {"slotType": "weekend", "date": "2027-02-13", "dateEnd": "2027-02-14", "category": "fa-cup", "label": "FA Cup Fourth Round"},
    {"slotType": "weekend", "date": "2027-03-06", "dateEnd": "2027-03-07", "category": "fa-cup", "label": "FA Cup Fifth Round"},
    {"slotType": "weekend", "date": "2027-04-03", "dateEnd": "2027-04-04", "category": "fa-cup", "label": "FA Cup Quarter-Final"},
    {"slotType": "weekend", "date": "2027-04-24", "dateEnd": "2027-04-25", "category": "fa-cup", "label": "FA Cup Semi-Final"},
    {"slotType": "weekend", "date": "2027-05-22", "category": "fa-cup", "label": "FA Cup Final"},
    {"slotType": "midweek", "date": "2026-09-08", "dateEnd": "2026-09-10", "category": "champions-league", "label": "Champions League Matchday 1"},
    {"slotType": "midweek", "date": "2026-10-13", "dateEnd": "2026-10-14", "category": "champions-league", "label": "Champions League Matchday 2"},
    {"slotType": "midweek", "date": "2026-10-20", "dateEnd": "2026-10-21", "category": "champions-league", "label": "Champions League Matchday 3"},
    {"slotType": "midweek", "date": "2026-11-03", "dateEnd": "2026-11-04", "category": "champions-league", "label": "Champions League Matchday 4"},
    {"slotType": "midweek", "date": "2026-11-24", "dateEnd": "2026-11-25", "category": "champions-league", "label": "Champions League Matchday 5"},
    {"slotType": "midweek", "date": "2026-12-08", "dateEnd": "2026-12-09", "category": "champions-league", "label": "Champions League Matchday 6"},
    {"slotType": "midweek", "date": "2027-01-19", "dateEnd": "2027-01-20", "category": "champions-league", "label": "Champions League Matchday 7"},
    {"slotType": "midweek", "date": "2027-01-27", "category": "champions-league", "label": "Champions League Matchday 8"},
    {"slotType": "midweek", "date": "2027-02-16", "dateEnd": "2027-02-17", "category": "champions-league", "label": "Champions League Knockout Play-off 1st Leg"},
    {"slotType": "midweek", "date": "2027-02-23", "dateEnd": "2027-02-24", "category": "champions-league", "label": "Champions League Knockout Play-off 2nd Leg"},
    {"slotType": "midweek", "date": "2027-03-09", "dateEnd": "2027-03-10", "category": "champions-league", "label": "Champions League Round of 16 1st Leg"},
    {"slotType": "midweek", "date": "2027-03-16", "dateEnd": "2027-03-17", "category": "champions-league", "label": "Champions League Round of 16 2nd Leg"},
    {"slotType": "midweek", "date": "2027-04-06", "dateEnd": "2027-04-07", "category": "champions-league", "label": "Champions League Quarter-Final 1st Leg"},
    {"slotType": "midweek", "date": "2027-04-13", "dateEnd": "2027-04-14", "category": "champions-league", "label": "Champions League Quarter-Final 2nd Leg"},
    {"slotType": "midweek", "date": "2027-04-27", "dateEnd": "2027-04-28", "category": "champions-league", "label": "Champions League Semi-Final 1st Leg"},
    {"slotType": "midweek", "date": "2027-05-04", "dateEnd": "2027-05-05", "category": "champions-league", "label": "Champions League Semi-Final 2nd Leg"},
    {"slotType": "weekend", "date": "2027-06-05", "category": "champions-league", "label": "Champions League Final"},
]


def fetch_api(url):
    req = urllib.request.Request(url, headers={"X-Auth-Token": API_KEY})
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def is_weekend(date_str):
    from datetime import date
    d = date.fromisoformat(date_str)
    return d.weekday() >= 5  # Sat=5, Sun=6


def utc_to_uk(utc_date_str):
    """Convert UTC datetime string to UK time (BST/GMT) and return HH:MM or None if midnight."""
    from datetime import datetime, timedelta
    dt = datetime.fromisoformat(utc_date_str.replace("Z", "+00:00"))
    # BST: last Sunday in March to last Sunday in October
    year = dt.year
    # Find last Sunday in March
    mar31 = datetime(year, 3, 31, 1, 0)
    bst_start = mar31 - timedelta(days=(mar31.weekday() + 1) % 7)
    bst_start = bst_start.replace(tzinfo=dt.tzinfo)
    # Find last Sunday in October
    oct31 = datetime(year, 10, 31, 1, 0)
    bst_end = oct31 - timedelta(days=(oct31.weekday() + 1) % 7)
    bst_end = bst_end.replace(tzinfo=dt.tzinfo)
    if bst_start <= dt.replace(tzinfo=None) < bst_end:
        dt += timedelta(hours=1)
    time_str = dt.strftime("%H:%M")
    return time_str if time_str != "00:00" else None


def build_fixture(match):
    date = match["utcDate"][:10]
    is_home = match["homeTeam"]["id"] == TEAM_ID
    opponent = (match["awayTeam"]["shortName"] or match["awayTeam"]["name"]) if is_home else (match["homeTeam"]["shortName"] or match["homeTeam"]["name"])
    comp_code = match["competition"]["code"]
    category = CATEGORY_MAP.get(comp_code, comp_code.lower())

    if category == "premier-league":
        label = f"{opponent} ({'H' if is_home else 'A'})"
    elif category == "community-shield":
        label = f"{opponent} (N – Principality Stadium, Cardiff)"
    else:
        stage = (match.get("stage") or "").replace("_", " ").title()
        md = match.get("matchday")
        label = f"{match['competition']['name']} {f'Matchday {md}' if md else stage}"

    fixture = {
        "slotType": "weekend" if is_weekend(date) else "midweek",
        "date": date,
        "category": category,
        "label": label,
    }

    kickoff = utc_to_uk(match["utcDate"])
    if kickoff:
        fixture["kickoff"] = kickoff

    return fixture


def main():
    if not API_KEY:
        print("Error: FOOTBALL_DATA_API_KEY environment variable not set")
        sys.exit(1)

    print("Fetching Man City fixtures...")
    data = fetch_api(f"https://api.football-data.org/v4/teams/{TEAM_ID}/matches?status=SCHEDULED,TIMED")
    matches = data.get("matches", [])
    print(f"  API returned {len(matches)} scheduled matches")

    # Build fixtures from API
    api_fixtures = [build_fixture(m) for m in matches]
    api_categories = {f["category"] for f in api_fixtures}

    # Only include estimated cup entries for categories NOT yet in API data
    estimates = [e for e in ESTIMATED_CUP_ENTRIES if e["category"] not in api_categories]
    if estimates:
        print(f"  Adding {len(estimates)} estimated entries (categories not yet in API: {set(e['category'] for e in estimates)})")

    # Static entries: always include internationals, only include community-shield if not from API
    statics = [e for e in STATIC_ENTRIES if e["category"] == "international" or e["category"] not in api_categories]

    # Merge
    merged = api_fixtures + statics + estimates
    merged.sort(key=lambda f: f["date"])

    os.makedirs(os.path.dirname(os.path.abspath("fixtures.json")), exist_ok=True)
    with open("fixtures.json", "w") as f:
        json.dump(merged, f, indent=2)
        f.write("\n")

    print(f"  Written {len(merged)} entries to fixtures.json")


if __name__ == "__main__":
    main()
