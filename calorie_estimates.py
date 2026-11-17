"""Small, transparent activity-energy estimates."""

from __future__ import annotations

ACTIVITY_MET: dict[str, float] = {
    "Walking · easy pace": 2.8,
    "Walking · brisk pace": 4.3,
    "Running · easy pace": 7.0,
    "Cycling · moderate pace": 6.8,
    "Strength training": 3.5,
    "Yoga": 2.5,
    "Swimming · moderate pace": 6.0,
}


def estimate_activity_calories(
    weight_kg: float, duration_minutes: int, met: float
) -> int:
    """Estimate active calories above resting energy using a MET approximation."""
    if weight_kg <= 0:
        raise ValueError("Weight must be greater than zero.")
    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero.")
    if met <= 1:
        raise ValueError("MET must be greater than one.")

    active_calories = (met - 1) * 3.5 * weight_kg / 200 * duration_minutes
    return max(1, round(active_calories))
