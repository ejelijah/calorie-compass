from datetime import date

import pandas as pd
import streamlit as st

from calorie_estimates import ACTIVITY_MET, estimate_activity_calories
from calorie_store import (
    add_entry,
    add_workout,
    delete_entry,
    delete_workout,
    get_daily_history,
    get_daily_totals,
    get_database_path,
    get_entries,
    get_workouts,
    initialize_database,
)
from nutrition_lookup import FoodLookupError, calories_for_amount, lookup_product

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
    st.subheader("Look up packaged food")
    st.caption(
        "Enter the barcode from a packaged product to look up its nutrition data. "
        "Values come from Open Food Facts and may be user-submitted."
    )
    with st.form("food_barcode_lookup"):
        barcode = st.text_input(
            "Product barcode",
            placeholder="8–14 digits on the package",
            max_chars=14,
        )
        serving_grams = st.number_input(
            "Amount eaten (grams)",
            min_value=1.0,
            max_value=10_000.0,
            value=100.0,
            step=10.0,
        )
        lookup_submitted = st.form_submit_button(
            "Look up food",
            icon=":material/search:",
        )

    if lookup_submitted:
        st.session_state.pop("food_lookup_result", None)
        try:
            product = lookup_product(barcode)
            st.session_state["food_lookup_result"] = {
                **product,
                "serving_grams": serving_grams,
                "calories": calories_for_amount(
                    product["calories_per_100g"], serving_grams
                ),
            }
        except FoodLookupError as exc:
            st.error(str(exc))

    product_result = st.session_state.get("food_lookup_result")
    if product_result:
        brand = f" · {product_result['brand']}" if product_result["brand"] else ""
        st.write(
            f"**{product_result['name']}**{brand} — "
            f"{product_result['calories']} estimated calories for "
            f"{product_result['serving_grams']:g} g"
        )
        st.caption(
            f"Database value: {product_result['calories_per_100g']:.0f} calories per 100 g. "
            "Check the package label; serving estimates may differ."
        )
        if product_result["calories"] == 0:
            st.info("This portion rounds to zero calories; increase the amount to log it.")
        if st.button(
            "Log this food",
            type="primary",
            key="log_barcode_food",
            disabled=product_result["calories"] == 0,
        ):
            add_entry(
                selected_date,
                "in",
                f"{product_result['name']} ({product_result['serving_grams']:g} g)",
                max(1, product_result["calories"]),
                DB_PATH,
            )
            st.session_state.pop("food_lookup_result", None)
            st.success("Food entry saved.")
            st.rerun()

with st.container(border=True):
    st.subheader("Estimate activity calories")
    st.caption(
        "This rough estimate uses activity type, duration, and body weight. "
        "It is not a measurement from a wearable."
    )
    with st.form("activity_calorie_estimate"):
        activity = st.selectbox("Activity", options=list(ACTIVITY_MET))
        duration_minutes = st.number_input(
            "Duration (minutes)",
            min_value=1,
            max_value=1_440,
            value=30,
            step=5,
        )
        weight_unit = st.selectbox("Weight unit", options=["kg", "lb"])
        weight = st.number_input(
            f"Body weight ({weight_unit})",
            min_value=1.0,
            max_value=700.0 if weight_unit == "lb" else 300.0,
            value=150.0 if weight_unit == "lb" else 68.0,
            step=1.0,
        )
        estimate_submitted = st.form_submit_button(
            "Estimate calories",
            icon=":material/calculate:",
        )

    if estimate_submitted:
        weight_kg = weight / 2.20462 if weight_unit == "lb" else weight
        estimated_calories = estimate_activity_calories(
            weight_kg, int(duration_minutes), ACTIVITY_MET[activity]
        )
        st.session_state["activity_estimate"] = {
            "activity": activity,
            "duration_minutes": int(duration_minutes),
            "calories": estimated_calories,
        }

    activity_result = st.session_state.get("activity_estimate")
    if activity_result:
        st.metric(
            "Estimated activity calories above rest",
            f"{activity_result['calories']:,} cal",
        )
        if st.button("Log this activity", type="primary", key="log_activity"):
            add_entry(
                selected_date,
                "out",
                f"{activity_result['activity']} · "
                f"{activity_result['duration_minutes']} min (estimate)",
                max(1, activity_result["calories"]),
                DB_PATH,
            )
            st.session_state.pop("activity_estimate", None)
            st.success("Activity estimate saved.")
            st.rerun()

with st.container(border=True):
    st.subheader("Strength workout log")
    st.caption(
        "Record exercises, sets, reps, and load. This is training history; "
        "strength workouts are not automatically converted into calories burned."
    )
    with st.form("strength_workout_log", clear_on_submit=True):
        exercise = st.text_input(
            "Exercise",
            placeholder="For example, barbell squat",
            max_chars=120,
        )
        sets, reps = st.columns(2)
        with sets:
            set_count = st.number_input(
                "Sets",
                min_value=1,
                max_value=100,
                value=3,
                step=1,
            )
        with reps:
            rep_count = st.number_input(
                "Reps per set",
                min_value=1,
                max_value=1_000,
                value=10,
                step=1,
            )
        load_col, unit_col = st.columns(2)
        with load_col:
            load = st.number_input(
                "Load (use 0 for bodyweight)",
                min_value=0.0,
                max_value=2_000.0,
                value=0.0,
                step=2.5,
            )
        with unit_col:
            load_unit = st.selectbox("Load unit", options=["kg", "lb"])
        workout_submitted = st.form_submit_button(
            "Save workout",
            type="primary",
            icon=":material/fitness_center:",
        )

    if workout_submitted:
        if not exercise.strip():
            st.error("Enter an exercise name before saving.")
        else:
            add_workout(
                selected_date,
                exercise,
                int(set_count),
                int(rep_count),
                load,
                load_unit,  # type: ignore[arg-type]
                DB_PATH,
            )
            st.success("Workout saved.")
            st.rerun()

    workouts = get_workouts(selected_date, DB_PATH)
    if workouts:
        workout_table = pd.DataFrame(
            [
                {
                    "Exercise": workout["exercise"],
                    "Sets": workout["sets"],
                    "Reps / set": workout["reps"],
                    "Load": (
                        f"{workout['weight']:g} {workout['weight_unit']}"
                        if workout["weight"]
                        else "Bodyweight"
                    ),
                }
                for workout in workouts
            ]
        )
        st.dataframe(workout_table, hide_index=True)
        workout_labels = {
            int(workout["id"]): (
                f"{workout['exercise']} · {workout['sets']} × {workout['reps']} "
                f"(entry #{workout['id']})"
            )
            for workout in workouts
        }
        with st.expander("Remove a workout"):
            selected_workout = st.selectbox(
                "Workout to remove",
                options=list(workout_labels),
                format_func=workout_labels.__getitem__,
                key="workout_to_remove",
            )
            if st.button("Delete selected workout", key="delete_workout"):
                if delete_workout(selected_workout, DB_PATH):
                    st.success("Workout removed.")
                    st.rerun()
                st.error("That workout could not be found.")
    else:
        st.info("No strength exercises logged for this day yet.")

with st.expander("Movement tracking integrations"):
    st.markdown(
        """
        **Connection status: not connected.** This prototype does not monitor
        movement in the background or read wearable sensors.

        - **Apple Watch / HealthKit:** a future iPhone app could request
          permission to import Apple Health active-energy and workout records.
        - **Android / Health Connect:** a future Android app could request
          permission to import compatible activity and energy records.
        - **Review before logging:** imported records should show their source,
          time, and estimate so you can confirm them and avoid duplicates.

        Imported active calories would still be estimates and would not include
        all energy your body uses at rest. Workout history above is kept
        separate from the calorie-out total unless you log a separate estimate.
        """
    )

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
