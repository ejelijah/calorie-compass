from datetime import date

import pandas as pd
import streamlit as st

from calorie_store import (
    add_entry,
    delete_entry,
    get_daily_history,
    get_daily_totals,
    get_database_path,
    get_entries,
    initialize_database,
)

st.set_page_config(
    page_title="Neo_Cal | Daily calorie tracker",
    page_icon=":material/local_fire_department:",
    layout="wide",
)

DB_PATH = get_database_path()
initialize_database(DB_PATH)

st.title("Neo_Cal")
st.caption("A simple daily view of calories logged in, calories logged out, and your net.")

with st.sidebar:
    st.subheader("Choose a day")
    selected_date = st.date_input("Log date", value=date.today(), key="selected_date")
    st.divider()
    st.caption(
        "Calorie counts—especially activity estimates—are approximate. "
        "This tracker is for personal awareness, not medical advice."
    )

totals = get_daily_totals(selected_date, DB_PATH)

with st.container(horizontal=True):
    st.metric("Calories in", f"{totals['calories_in']:,}", border=True)
    st.metric("Calories out", f"{totals['calories_out']:,}", border=True)
    st.metric("Net for the day", f"{totals['net']:,}", border=True)

st.caption("Net = calories in − calories out. A negative net is shown as logged; it is not a goal.")

with st.container(border=True):
    st.subheader("Add an entry")
    with st.form("add_calorie_entry", clear_on_submit=True):
        entry_type = st.selectbox(
            "Entry type",
            options=["in", "out"],
            format_func=lambda value: (
                "Calories in · food or drink" if value == "in"
                else "Calories out · activity estimate"
            ),
        )
        description = st.text_input(
            "Description",
            placeholder="For example, lunch or a walk",
            max_chars=120,
        )
        calories = st.number_input(
            "Calories",
            min_value=1,
            max_value=100_000,
            value=100,
            step=10,
        )
        submitted = st.form_submit_button(
            "Save entry",
            type="primary",
            icon=":material/add:",
        )

    if submitted:
        if not description.strip():
            st.error("Add a short description before saving.")
        else:
            add_entry(
                selected_date,
                entry_type,  # type: ignore[arg-type]
                description,
                int(calories),
                DB_PATH,
            )
            st.success("Entry saved.")
            st.rerun()

st.subheader(f"Entries for {selected_date.strftime('%A, %B %-d')}")
entries = get_entries(selected_date, DB_PATH)

if not entries:
    st.info("No entries for this day yet. Add food, drinks, or an activity estimate above.")
else:
    display_entries = pd.DataFrame(
        [
            {
                "Type": "In" if entry["entry_type"] == "in" else "Out",
                "Description": entry["description"],
                "Calories": entry["calories"],
            }
            for entry in entries
        ]
    )
    st.dataframe(display_entries, hide_index=True)

    entry_labels = {
        int(entry["id"]): (
            f"{'In' if entry['entry_type'] == 'in' else 'Out'} · "
            f"{entry['description']} · {int(entry['calories']):,} cal "
            f"(entry #{entry['id']})"
        )
        for entry in entries
    }
    with st.expander("Remove an entry"):
        selected_entry_id = st.selectbox(
            "Entry to remove",
            options=list(entry_labels),
            format_func=entry_labels.__getitem__,
        )
        if st.button("Delete selected entry", type="secondary"):
            if delete_entry(selected_entry_id, DB_PATH):
                st.success("Entry removed.")
                st.rerun()
            st.error("That entry could not be found.")

st.subheader("Seven-day overview")
history = pd.DataFrame(get_daily_history(selected_date, days=7, db_path=DB_PATH))
history["date"] = pd.to_datetime(history["date"])
chart_data = history.set_index("date")[["calories_in", "calories_out", "net"]]
chart_data.columns = ["Calories in", "Calories out", "Net"]
st.bar_chart(chart_data)
st.caption("Days with no entries appear as zero. Past days can be selected in the sidebar.")
