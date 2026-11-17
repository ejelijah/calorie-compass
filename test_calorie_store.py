from datetime import date, timedelta

import pytest

from calorie_store import (
    add_entry,
    delete_entry,
    get_daily_history,
    get_daily_totals,
    get_entries,
    initialize_database,
)


def test_daily_totals_include_zero_and_calculate_net(tmp_path):
    database = tmp_path / "test.db"
    initialize_database(database)
    today = date(2026, 11, 16)

    assert get_daily_totals(today, database) == {
        "calories_in": 0,
        "calories_out": 0,
        "net": 0,
    }

    add_entry(today, "in", "Lunch", 650, database)
    add_entry(today, "out", "Walk", 180, database)

    assert get_daily_totals(today, database) == {
        "calories_in": 650,
        "calories_out": 180,
        "net": 470,
    }


def test_entries_are_separated_by_date_and_can_be_deleted(tmp_path):
    database = tmp_path / "test.db"
    initialize_database(database)
    today = date(2026, 11, 16)
    entry_id = add_entry(today, "in", "Breakfast", 400, database)
    add_entry(today + timedelta(days=1), "in", "Snack", 100, database)

    entries = get_entries(today, database)
    assert len(entries) == 1
    assert entries[0]["description"] == "Breakfast"
    assert delete_entry(entry_id, database)
    assert get_entries(today, database) == []
    assert not delete_entry(entry_id, database)


def test_history_includes_days_without_entries(tmp_path):
    database = tmp_path / "test.db"
    initialize_database(database)
    end_date = date(2026, 11, 16)
    add_entry(end_date, "in", "Dinner", 700, database)

    history = get_daily_history(end_date, days=3, db_path=database)

    assert [row["net"] for row in history] == [0, 0, 700]


@pytest.mark.parametrize(
    ("entry_type", "description", "calories"),
    [
        ("other", "Food", 100),
        ("in", " ", 100),
        ("out", "Run", 0),
        ("in", "Snack", -1),
        ("in", "Snack", True),
    ],
)
def test_invalid_entries_are_rejected(
    tmp_path, entry_type, description, calories
):
    database = tmp_path / "test.db"
    initialize_database(database)

    with pytest.raises(ValueError):
        add_entry(date(2026, 11, 16), entry_type, description, calories, database)
