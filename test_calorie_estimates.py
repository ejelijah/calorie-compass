import pytest

from calorie_estimates import estimate_activity_calories


def test_activity_estimate_uses_calories_above_rest():
    assert estimate_activity_calories(weight_kg=70, duration_minutes=30, met=4) == 110


@pytest.mark.parametrize(
    ("weight", "duration", "met"),
    [(0, 30, 4), (70, 0, 4), (70, 30, 1)],
)
def test_activity_estimate_rejects_invalid_inputs(weight, duration, met):
    with pytest.raises(ValueError):
        estimate_activity_calories(weight, duration, met)
