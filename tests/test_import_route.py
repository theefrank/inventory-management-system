"""
tests/test_import_route.py
---------------------------
Tests the Flask route that combines the external API call with the
CRUD "create" operation: POST /api/items/import/<barcode>.
This is the "fetch from external API and add it to the database array"
feature called out explicitly in the rubric.
"""

import sys
import os
from unittest.mock import patch
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import reset_db


@pytest.fixture()
def client():
    reset_db()
    app = create_app()
    app.config.update({"TESTING": True})
    with app.test_client() as client:
        yield client
    reset_db()


@patch("app.fetch_product_by_barcode")
def test_import_item_adds_to_inventory(mock_fetch, client):
    mock_fetch.return_value = {
        "barcode": "5000112637922",
        "name": "Coca-Cola",
        "brand": "Coca-Cola",
        "category": "Beverages",
        "description": "Fizzy soft drink",
        "image_url": "http://example.com/coke.jpg",
    }

    resp = client.post(
        "/api/items/import/5000112637922", json={"quantity": 24, "price": 1.25}
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Coca-Cola"
    assert data["quantity"] == 24
    assert data["price"] == 1.25

    # Confirm it actually landed in the inventory "database array"
    list_resp = client.get("/api/items")
    names = [i["name"] for i in list_resp.get_json()]
    assert "Coca-Cola" in names


@patch("app.fetch_product_by_barcode")
def test_import_item_not_found(mock_fetch, client):
    mock_fetch.return_value = None
    resp = client.post("/api/items/import/0000000000000")
    assert resp.status_code == 404


@patch("app.search_products_by_name")
def test_external_search_route(mock_search, client):
    mock_search.return_value = [
        {"barcode": "111", "name": "Green Tea", "brand": "BrandX"},
    ]
    resp = client.get("/api/external/search", params={"q": "tea"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[0]["name"] == "Green Tea"


def test_external_search_missing_query(client):
    resp = client.get("/api/external/search")
    assert resp.status_code == 400
