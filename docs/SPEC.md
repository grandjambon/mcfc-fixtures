# MCFC Fixtures Calendar — Specification

## Overview

A static single-page website displaying all Manchester City 2026-27 fixtures across all competitions, hosted on GitHub Pages at https://grandjambon.github.io/mcfc-fixtures/. Fixtures are updated daily via a GitHub Action that pulls data from the football-data.org API.

## Architecture

```
index.html              → Single-page app (vanilla HTML/CSS/JS)
fixtures.json           → Generated fixture data (written by fetch script + GitHub Action)
internationals.json     → Static international break fixture panels
fetch_fixtures.py       → Python script to pull data from football-data.org API
.github/workflows/update-fixtures.yml → Daily cron job to regenerate fixtures.json
```

No build step, no dependencies, no framework. The site fetches the two JSON files at load time and renders client-side.

## Data Model

### fixtures.json

Array of fixture objects, sorted by date:

```json
{
  "slotType": "weekend" | "midweek" | "break",
  "date": "YYYY-MM-DD",
  "dateEnd": "YYYY-MM-DD",      // optional: for multi-day events (cup rounds, international breaks)
  "category": "premier-league" | "champions-league" | "fa-cup" | "league-cup" | "international" | "community-shield",
  "label": "Opponent (H/A)" | "Competition Round Name",
  "kickoff": "HH:MM"            // optional: UK local time (BST/GMT), omitted if not yet confirmed
}
```

**slotType rules:**
- `weekend` = Saturday or Sunday
- `midweek` = Monday through Friday
- `break` = international breaks only

**dateEnd:** Present only for multi-day events. When present, the date column is left blank and the date range is shown in the label text instead.

**kickoff:** UK local time in 24-hour format. Omitted when the API returns placeholder times (00:00 or 12:00 UTC, which indicate "not yet confirmed").

### internationals.json

Static file, keyed by country:

```json
{
  "england": {
    "league": "A3",
    "fixtures": [
      {"date": "YYYY-MM-DD", "match": "Team v Team", "venue": "H" | "A"}
    ]
  }
}
```

Countries included: england, scotland, wales, northern-ireland, republic-of-ireland (Nations League 2026-27).

## Competitions & Categories

| Category | Colour | Source |
|----------|--------|--------|
| premier-league | Blue (#6cabdd) | API (live, 38 matches confirmed) |
| champions-league | Purple (#a366ff) | API when drawn; estimated dates as fallback |
| fa-cup | Green (#66ff8c) | API when drawn; estimated round dates as fallback |
| league-cup | Orange (#ffc966) | API when drawn; confirmed EFL round dates as fallback |
| community-shield | Pink (#ff66a3) | Static entry (confirmed: Arsenal, Aug 16, Cardiff, 15:00 BST) |
| international | Grey (#888) | Static entries with expandable panels |

## API Integration

**Provider:** football-data.org (free tier)
- Rate limit: 10 requests/minute
- Man City team ID: 65
- Endpoint: `GET /v4/teams/65/matches?status=SCHEDULED,TIMED`
- Auth: `X-Auth-Token` header
- Competition codes: PL, CL, FAC, ELC, CS

**Update strategy (fetch_fixtures.py):**
1. Pull all scheduled Man City matches from API
2. Convert UTC times to UK local time (BST Mar-Oct, GMT Oct-Mar)
3. Filter out placeholder kick-off times (00:00 and 12:00 UTC)
4. Check which competition categories the API returned data for
5. For categories NOT in API data, include estimated/static fallback entries
6. Always include international breaks and Community Shield (unless API provides them)
7. Sort by date, write to fixtures.json

**Key behaviour:** As draws happen (CL in Aug, cup rounds throughout season), real fixtures automatically replace the estimated placeholders because the API will return data for that category.

## GitHub Action

- **Schedule:** Daily at 08:00 UTC
- **Trigger:** Also manual via workflow_dispatch
- **Secret:** `FOOTBALL_DATA_API_KEY` stored in repo secrets
- **Behaviour:** Only commits if fixtures.json content has changed

## Display Rules

### Desktop
- Full layout: slot-type | date | label + kickoff | category tag
- Date column shows `Wed 23 Aug` format for single-date fixtures
- Multi-day events show date range in label: `"CL Matchday 1 (8 Sep – 10 Sep)"`

### Mobile (≤600px)
- Slot-type column hidden
- Labels shortened via JS (`shortenLabel()` function):
  - Champions League → CL, Matchday → MD
  - FA Cup → FAC, Third Round → R3, etc.
  - Carabao Cup → LC, Round → R
  - International Break → Int'l Break
- Rows wrap: date + tag on first line, label below

### International Breaks
- Clickable rows that expand a panel below
- Panel shows Nations League fixtures for England, Scotland, Wales, NI, ROI
- Grouped by country with H/A venue indicators

## Repository

- **GitHub:** https://github.com/grandjambon/mcfc-fixtures
- **Live site:** https://grandjambon.github.io/mcfc-fixtures/
- **Visibility:** Public (required for GitHub Pages free tier)
- **Write access:** Owner only; GitHub Actions bot via GITHUB_TOKEN
- **Branch:** main (single branch, Pages deploys from main)

## Data Sources

- Premier League fixtures: Sports Mole (confirmed Jun 19 2026)
- Champions League dates: UEFA (league phase matchdays + knockout schedule)
- FA Cup round dates: thefa.com
- Carabao Cup dates: Estimated from 2025-26 pattern (footnoted on site)
- International breaks: UEFA Nations League 2026-27
- Community Shield: thefa.com (confirmed Jun 4 2026)
- Live updates: football-data.org API

## Future Considerations

- Add scores/results for completed matches
- Mark unconfirmed kick-off times differently from confirmed ones
- Add calendar export (ICS)
- Handle fixture postponements gracefully
