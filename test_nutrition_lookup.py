import pytest

from nutrition_lookup import (
    FoodLookupError,
    calories_for_amount,
    lookup_product,
    parse_product,
)


def test_parse_product_returns_food_details_and_per_100g_calories():
    product = parse_product(
        {
            "status": 1,
            "product": {
                "product_name": "Oats",
                "brands": "Example",
                "nutriments": {"energy-kcal_100g": "389"},
            },
        }
    )

    assert product == {
        "name": "Oats",
        "brand": "Example",
        "calories_per_100g": 389.0,
    }


def test_parse_product_can_convert_kilojoules():
    product = parse_product(
        {
            "status": 1,
            "product": {"nutriments": {"energy_100g": 418.4}},
        }
    )

    assert product["calories_per_100g"] == pytest.approx(100)


def test_missing_product_or_calorie_data_is_reported():
    with pytest.raises(FoodLookupError, match="No matching product"):
        parse_product({"status": 0})

    with pytest.raises(FoodLookupError, match="no calorie information"):
        parse_product({"status": 1, "product": {"nutriments": {}}})


def test_calories_are_scaled_to_portion_size():
    assert calories_for_amount(250, 40) == 100
    assert calories_for_amount(0, 100) == 0


def test_barcode_validation_happens_before_network_lookup():
    with pytest.raises(FoodLookupError, match="8 to 14 digits"):
        lookup_product("not-a-barcode")


@pytest.mark.parametrize(
    ("calories_per_100g", "amount"),
    [(-1, 100), (float("nan"), 100), (100, 0), (100, float("inf"))],
)
def test_invalid_portion_calculations_are_rejected(calories_per_100g, amount):
    with pytest.raises(ValueError):
        calories_for_amount(calories_per_100g, amount)
