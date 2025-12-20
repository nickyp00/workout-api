# Workout API - Claude Integration

This repository enables conversational workout tracking with Claude via GitHub Actions and Supabase.

## How It Works

1. **Claude commits a request file** to `requests/` folder
2. **GitHub Action triggers** automatically on commit
3. **Python script processes** the request and interacts with Supabase
4. **Results are committed** back to `results/` folder
5. **Claude reads the results** and responds to you

## Folder Structure

```
requests/          # Claude writes workout/query requests here
results/           # GitHub Actions write results here
scripts/           # Python processing scripts
.github/workflows/ # GitHub Actions workflows
```

## Workflows

- **add-workout.yml** - Triggers when `requests/workout_*.json` is committed
- **query-workouts.yml** - Triggers when `requests/query_*.json` is committed

## Request File Formats

### Workout Request (`requests/workout_001.json`)
```json
{
  "exercise": "bench press",
  "sets": [
    {"weight": 120, "reps": 10},
    {"weight": 120, "reps": 10},
    {"weight": 120, "reps": 8}
  ],
  "weight_type": "barbell",
  "notes": "Felt strong today"
}
```

### Query Request (`requests/query_001.json`)
```json
{
  "query_type": "max_weight",
  "exercise": "bench press",
  "days_back": 90
}
```

Query types:
- `max_weight` - Get max weight progression
- `volume` - Calculate total volume
- `history` - Get complete workout history
- `recent_workouts` - Get all recent workouts

## Setup

1. Add Supabase credentials to GitHub Secrets:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

2. Ensure exercises exist in Supabase `exercises` table

3. Claude handles the rest!
