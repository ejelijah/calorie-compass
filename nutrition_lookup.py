"""Lookup packaged-food nutrition from Open Food Facts."""

from __future__ import annotations

import json
import math
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class FoodLookupError(Exception):
    """Raised when a product cannot be looked up or lacks calorie data."""


def parse_product(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("status") != 1 or not isinstance(payload.get("product"), dict):
        raise FoodLookupError("No matching product was found.")

    product = payload["product"]
    nutriments = product.get("nutriments")
    if not isinstance(nutriments, dict):
        raise FoodLookupError("This product has no calorie information available.")

    calories = nutriments.get("energy-kcal_100g")
    if calories is None:
        energy_kj = nutriments.get("energy_100g")
        if energy_kj is None:
            raise FoodLookupError(
                "This product has no calorie information available."
            )
        try:
            calories = float(energy_kj) / 4.184
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            raise FoodLookupError(
                "This product has no usable calorie information."
            ) from exc

    try:
        calories = float(calories)
    except (TypeError, ValueError) as exc:
        raise FoodLookupError(
            "This product has no usable calorie information."
        ) from exc

    if not math.isfinite(calories) or calories < 0:
        raise FoodLookupError("This product has invalid calorie information.")

    name = product.get("product_name") or product.get("product_name_en")
    if not isinstance(name, str) or not name.strip():
        name = "Packaged food"

    brand = product.get("brands")
    return {
        "name": name.strip(),
        "brand": brand.strip() if isinstance(brand, str) else "",
        "calories_per_100g": calories,
    }


def lookup_product(barcode: str) -> dict[str, Any]:
    clean_barcode = barcode.strip()
    if not re.fullmatch(r"\d{8,14}", clean_barcode):
        raise FoodLookupError("Enter a product barcode with 8 to 14 digits.")

    request = Request(
        "https://world.openfoodfacts.org/api/v2/product/"
        f"{clean_barcode}.json?fields=product_name,product_name_en,brands,nutriments",
        headers={"User-Agent": "NeoCal/0.1 (student calorie tracking MVP)"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FoodLookupError(
            "Food lookup is unavailable right now. Check your connection and try again."
        ) from exc

    if not isinstance(payload, dict):
        raise FoodLookupError("The food database returned an unexpected response.")
    return parse_product(payload)


def calories_for_amount(calories_per_100g: float, amount_grams: float) -> int:
    if not math.isfinite(calories_per_100g) or calories_per_100g < 0:
        raise ValueError("Calories per 100 grams must be a non-negative number.")
    if not math.isfinite(amount_grams) or amount_grams <= 0:
        raise ValueError("Serving size must be greater than zero.")
    return round(calories_per_100g * amount_grams / 100)
