"""Fetch Man City fixtures from football-data.org and output fixtures.json + results.json"""
import urllib.request
import json
import os
import sys
import time

API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY")
TEAM_ID = 65  # Manchester City

# Competition code -> site category.
# NOTE: On the free football-data.org tier, only PL and CL are accessible for Man City.
#   - FAC (FA Cup), CS (Community Shield) return 403 (not on free tier)
#   - EFL Cup / Carabao Cup is NOT covered by the API at all
#   - "ELC" in this API is the EFL *Championship* (2nd tier league), NOT the League Cup,
#     so it must not be mapped here. City don't play in it anyway.
# FA Cup, League Cup and Community Shield are therefore maintained manually via
# ESTIMATED_CUP_ENTRIES / STATIC_ENTRIES and will not auto-update from the API.
CATEGORY_MAP = {
    "PL": "premier-league",
    "CL": "champions-league",
    "FAC": "fa-cup",          # not on free tier; kept in case of future upgrade
    "CS": "community-shield",  # not on free tier; kept in case of future upgrade
}

STATIC_ENTRIES = [
    {"slotType": "weekend", "date": "2026-08-16", "category": "community-shield", "label": "Arsenal (N \u2013 Principality Stadium, Cardiff)", "kickoff": "15:00"},
    {"slotType": "break", "date": "2026-09-21", "dateEnd": "2026-10-06", "category": "international", "label": "International Break"},
    {"slotType": "break", "date": "2026-11-09", "dateEnd": "2026-11-17", "category": "international", "label": "International Break"},
    {"slotType": "break", "date": "2027-03-22", "dateEnd": "2027-03-30", "category": "international", "label": "International Break"},
]

# ---------------------------------------------------------------------------
# MANUAL CUP ENTRIES — FA Cup & Carabao (League) Cup
# ---------------------------------------------------------------------------
# These competitions are NOT available on the free football-data.org tier, so
# they are maintained BY HAND here. As each round is drawn, update the relevant
# entry with the confirmed opponent, date, venue (H/A/N) and kickoff.
#
# Format options:
#   Confirmed tie:   {"slotType", "date", "category", "label": "Opponent (H) \u00b7 Carabao Cup R3", "kickoff": "19:30"}
#   Unknown/TBC slot: {"slotType", "date", "dateEnd", "category", "label": "Carabao Cup Round 4 (TBC)"}
#
# Use a single "date" + "kickoff" once a tie is confirmed; use "date"+"dateEnd"
# (a window) with no kickoff while the round is still an estimated slot.
MANUAL_CUP_ENTRIES = [
    # --- Carabao Cup ---
    {"slotType": "midweek", "date": "2026-09-17", "category": "league-cup", "label": "Norwich (H) \u00b7 Carabao Cup R3", "kickoff": "19:30"},
    {"slotType": "midweek", "date": "2026-10-27", "dateEnd": "2026-10-28", "category": "league-cup", "label": "Carabao Cup Round 4 (TBC)"},
    {"slotType": "midweek", "date": "2026-12-15", "dateEnd": "2026-12-16", "category": "league-cup", "label": "Carabao Cup Quarter-Final (TBC)"},
    {"slotType": "midweek", "date": "2027-01-12", "dateEnd": "2027-01-13", "category": "league-cup", "label": "Carabao Cup Semi-Final 1st Leg (TBC)"},
    {"slotType": "midweek", "date": "2027-02-02", "dateEnd": "2027-02-03", "category": "league-cup", "label": "Carabao Cup Semi-Final 2nd Leg (TBC)"},
    {"slotType": "weekend", "date": "2027-03-21", "category": "league-cup", "label": "Carabao Cup Final (Wembley, TBC)"},
    # --- FA Cup ---
    {"slotType": "weekend", "date": "2027-01-09", "dateEnd": "2027-01-10", "category": "fa-cup", "label": "FA Cup Third Round (TBC)"},
    {"slotType": "weekend", "date": "2027-02-13", "dateEnd": "2027-02-14", "category": "fa-cup", "label": "FA Cup Fourth Round (TBC)"},
    {"slotType": "weekend", "date": "2027-03-06", "dateEnd": "2027-03-07", "category": "fa-cup", "label": "FA Cup Fifth Round (TBC)"},
    {"slotType": "weekend", "date": "2027-04-03", "dateEnd": "2027-04-04", "category": "fa-cup", "label": "FA Cup Quarter-Final (TBC)"},
    {"slotType": "weekend", "date": "2027-04-24", "dateEnd": "2027-04-25", "category": "fa-cup", "label": "FA Cup Semi-Final (TBC)"},
    {"slotType": "weekend", "date": "2027-05-22", "category": "fa-cup", "label": "FA Cup Final (TBC)"},
]

# Estimated Champions League dates — REPLACED automatically once the API returns
# the real fixtures (CL is on the free tier). Kept as a fallback only.
ESTIMATED_CUP_ENTRIES = [
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
    return d.weekday() in (0, 4, 5, 6)  # Mon=0, Fri=4, Sat=5, Sun=6


def utc_to_uk(utc_date_str):
    """Convert UTC datetime string to UK time (BST/GMT) and return HH:MM or None if time is a placeholder."""
    from datetime import datetime, timedelta
    dt = datetime.fromisoformat(utc_date_str.replace("Z", "+00:00")).replace(tzinfo=None)
    # Treat 00:00 and 12:00 UTC as "no time confirmed"
    if (dt.hour, dt.minute) in [(0, 0), (12, 0)]:
        return None
    year = dt.year
    # BST: last Sunday in March 01:00 UTC to last Sunday in October 01:00 UTC
    mar31 = datetime(year, 3, 31, 1, 0)
    bst_start = mar31 - timedelta(days=(mar31.weekday() + 1) % 7)
    oct31 = datetime(year, 10, 31, 1, 0)
    bst_end = oct31 - timedelta(days=(oct31.weekday() + 1) % 7)
    if bst_start <= dt < bst_end:
        dt += timedelta(hours=1)
    return dt.strftime("%H:%M")


def build_fixture(match):
    date = match["utcDate"][:10]
    is_home = match["homeTeam"]["id"] == TEAM_ID
    opponent = (match["awayTeam"]["shortName"] or match["awayTeam"]["name"]) if is_home else (match["homeTeam"]["shortName"] or match["homeTeam"]["name"])
    comp_code = match["competition"]["code"]
    category = CATEGORY_MAP.get(comp_code, comp_code.lower())

    if category == "premier-league":
        label = f"{opponent} ({'H' if is_home else 'A'})"
    elif category == "community-shield":
        label = f"{opponent} (N \u2013 Principality Stadium, Cardiff)"
    else:
        # Cup competitions (CL, FA Cup, League Cup): show opponent + round context
        stage = (match.get("stage") or "").replace("_", " ").title()
        md = match.get("matchday")
        if category == "champions-league" and md:
            context = f"CL MD{md}"
        elif category == "champions-league":
            context = f"CL {stage}" if stage else "Champions League"
        elif category == "fa-cup":
            context = f"FA Cup {stage}" if stage else "FA Cup"
        elif category == "league-cup":
            context = f"Carabao Cup {stage}" if stage else "Carabao Cup"
        else:
            context = match["competition"]["name"]
        home_away = "H" if is_home else "A"
        label = f"{opponent} ({home_away}) \u00b7 {context}"

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


def build_result(match):
    """Extract result data from a finished match."""
    date = match["utcDate"][:10]
    is_home = match["homeTeam"]["id"] == TEAM_ID
    home_team = match["homeTeam"]
    away_team = match["awayTeam"]

    result = {
        "date": date,
        "matchId": match["id"],
        "homeTeam": home_team.get("shortName") or home_team["name"],
        "awayTeam": away_team.get("shortName") or away_team["name"],
        "isHome": is_home,
        "score": {
            "fullTime": match["score"]["fullTime"],
            "halfTime": match["score"]["halfTime"],
        },
    }

    # Goals
    goals = []
    for g in match.get("goals") or []:
        goal = {
            "minute": g["minute"],
            "scorer": g["scorer"]["name"] if g.get("scorer") else "Unknown",
            "team": "home" if g["team"]["id"] == home_team["id"] else "away",
            "type": g.get("type", "REGULAR"),
        }
        if g.get("injuryTime"):
            goal["injuryTime"] = g["injuryTime"]
        goals.append(goal)
    result["goals"] = goals

    # Lineups (starting XI with formation)
    for side, team_data in [("home", home_team), ("away", away_team)]:
        lineup_data = {
            "formation": team_data.get("formation"),
            "startingXI": [],
            "substitutions": [],
        }
        for player in team_data.get("lineup") or []:
            lineup_data["startingXI"].append({
                "name": player["name"],
                "shirtNumber": player.get("shirtNumber"),
                "position": player.get("position"),
            })
        result[f"{side}Lineup"] = lineup_data

    # Substitutions
    for sub in match.get("substitutions") or []:
        side = "home" if sub["team"]["id"] == home_team["id"] else "away"
        result[f"{side}Lineup"]["substitutions"].append({
            "minute": sub["minute"],
            "playerIn": sub["playerIn"]["name"],
            "playerOut": sub["playerOut"]["name"],
        })

    return result


def main():
    if not API_KEY:
        print("Error: FOOTBALL_DATA_API_KEY environment variable not set")
        sys.exit(1)

    # --- Fetch scheduled fixtures ---
    print("Fetching Man City scheduled fixtures...")
    data = fetch_api(f"https://api.football-data.org/v4/teams/{TEAM_ID}/matches?status=SCHEDULED,TIMED")
    scheduled_matches = data.get("matches", [])
    print(f"  API returned {len(scheduled_matches)} scheduled matches")

    # --- Fetch finished fixtures (so they remain in the fixture list) ---
    print("Fetching Man City finished matches...")
    time.sleep(6)  # Respect rate limit
    data = fetch_api(f"https://api.football-data.org/v4/teams/{TEAM_ID}/matches?status=FINISHED&limit=100")
    finished_matches = data.get("matches", [])
    print(f"  API returned {len(finished_matches)} finished matches")

    # Build fixtures from both scheduled and finished
    all_api_matches = scheduled_matches + finished_matches
    api_fixtures = [build_fixture(m) for m in all_api_matches]
    api_categories = {f["category"] for f in api_fixtures}

    # Only include estimated CL entries for categories NOT yet in API data
    estimates = [e for e in ESTIMATED_CUP_ENTRIES if e["category"] not in api_categories]
    if estimates:
        print(f"  Adding {len(estimates)} estimated entries (categories not yet in API: {set(e['category'] for e in estimates)})")

    # Manual cup entries (FA Cup, League Cup) — always included; never come from the API.
    # Skip only if the API somehow provides that category (future-proof for a paid tier).
    manual_cups = [e for e in MANUAL_CUP_ENTRIES if e["category"] not in api_categories]
    print(f"  Adding {len(manual_cups)} manual cup entries (FA Cup / League Cup)")

    # Static entries: always include internationals, only include community-shield if not from API
    statics = [e for e in STATIC_ENTRIES if e["category"] == "international" or e["category"] not in api_categories]

    # Merge
    merged = api_fixtures + statics + estimates + manual_cups
    merged.sort(key=lambda f: f["date"])

    with open("fixtures.json", "w") as f:
        json.dump(merged, f, indent=2)
        f.write("\n")
    print(f"  Written {len(merged)} entries to fixtures.json")

    # --- Build detailed results from finished matches ---
    print("Building results data...")
    results = {}
    for match in finished_matches:
        result = build_result(match)
        key = f"{result['date']}_{result['homeTeam']}_v_{result['awayTeam']}"
        results[key] = result

    # Also load any existing results to preserve history across seasons
    existing_results = {}
    if os.path.exists("results.json"):
        with open("results.json") as f:
            existing_results = json.load(f)

    # Merge: new data overwrites existing for same key
    existing_results.update(results)

    with open("results.json", "w") as f:
        json.dump(existing_results, f, indent=2)
        f.write("\n")
    print(f"  Written {len(existing_results)} results to results.json")


if __name__ == "__main__":
    main()
