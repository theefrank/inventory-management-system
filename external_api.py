"""
external_api.py
----------------
Thin wrapper around the OpenFoodFacts public API.

Docs: https://world.openfoodfacts.org/data
Endpoints used:
  * GET https://world.openfoodfacts.org/api/v2/product/<barcode>.json
  * GET https://world.openfoodfacts.org/cgi/search.pl?search_terms=<name>&json=1

Isolating these calls behind two small functions means:
  1. app.py / cli.py don't need to know anything about the OFF response shape.
  2. Unit tests can mock `requests.get` in one place instead of patching Flask routes.
"""

import requests

BASE_URL = "https://world.openfoodfacts.org"
TIMEOUT = 10  # seconds


class ExternalAPIError(Exception):
    """Raised when the OpenFoodFacts API is unreachable or returns bad data."""


def _simplify_product(raw_product):
    """Pull out only the fields our inventory system cares about."""
    if not raw_product:
        return None
    return {
        "barcode": raw_product.get("code"),
        "name": raw_product.get("product_name") or raw_product.get("generic_name") or "Unknown product",
        "brand": raw_product.get("brands"),
        "category": (raw_product.get("categories") or "").split(",")[0].strip() or None,
        "description": raw_product.get("generic_name"),
        "image_url": raw_product.get("image_url"),
        "quantity_label": raw_product.get("quantity"),  # e.g. "500g" - informational only
    }


def fetch_product_by_barcode(barcode):
    """
    Fetch a single product from OpenFoodFacts by its barcode.
    Returns a simplified dict, or None if not found.
    Raises ExternalAPIError on network/timeout problems.
    """
    url = f"{BASE_URL}/api/v2/product/{barcode}.json"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExternalAPIError(f"Could not reach OpenFoodFacts: {exc}") from exc

    data = response.json()
    if data.get("status") != 1:
        return None

    return _simplify_product(data.get("product"))


def search_products_by_name(name, limit=10):
    """
    Search OpenFoodFacts by product name.
    Returns a list of simplified product dicts (possibly empty).
    Raises ExternalAPIError on network/timeout problems.
    """
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": limit,
    }
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ExternalAPIError(f"Could not reach OpenFoodFacts: {exc}") from exc

    data = response.json()
    products = data.get("products", [])
    return [_simplify_product(p) for p in products if p]
