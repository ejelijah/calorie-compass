# Neo_Cal

Neo_Cal is a small calorie-awareness MVP for recording calories in (food and
drinks), calories out (activity estimates), and the daily net:

**Net = calories in − calories out**

## Features

- Choose a date and record food, drinks, or an activity estimate.
- Look up packaged foods by barcode using the Open Food Facts database.
- Estimate activity calories from activity type, duration, and body weight.
- See daily calories in, calories out, and net totals.
- Review a seven-day overview, including days with no entries.
- Remove an entry if it was added by mistake.
- Store data locally in SQLite so it remains available after restarting the app.

This MVP has no account system or cloud sync. Its SQLite database is local to
the machine running Streamlit. Calorie and activity values are estimates, not
medical guidance or a prescribed target.

Food barcode lookups require an internet connection and send the barcode to
Open Food Facts. The product database may contain incomplete or user-submitted
nutrition values, so compare estimates with the package label. Activity
estimates use a simple MET formula and are not measurements from a wearable.

## Run locally

```bash
cd ~/developer/Neo_Cal
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

By default, the database is created at `data/calorie_log.db` and is ignored by
Git. To use a different local database file, set `NEO_CAL_DB_PATH`.

## Run tests

```bash
python -m pytest
```
