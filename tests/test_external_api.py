"""
tests/test_external_api.py
---------------------------
Tests for the OpenFoodFacts wrapper functions. We NEVER hit the real
network in unit tests -- `requests.get` is mocked via `unittest.mock`
so tests are fast, deterministic, and don't depend on internet access.
"""

import sys
import os
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from external_api import (
    fetch_product_by_barcode,
    search_products_by_name,
    ExternalAPIError,
)


def _mock_response(json_data, status_code=200, raise_for_status=None):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    return mock_resp


@patch("external_api.requests.get")
def test_fetch_product_by_barcode_found(mock_get):
    mock_get.return_value = _mock_response({
        "status": 1,
        "product": {
            "code": "1234567890",
            "product_name": "Test Cereal",
            "brands": "TestBrand",
            "categories": "Breakfast, Cereals",
            "generic_name": "Crunchy cereal",
            "image_url": "http://example.com/img.jpg",
            "quantity": "500g",
        },
    })

    product = fetch_product_by_barcode("1234567890")
    assert product["name"] == "Test Cereal"
    assert product["brand"] == "TestBrand"
    assert product["category"] == "Breakfast"
    assert product["barcode"] == "1234567890"


@patch("external_api.requests.get")
def test_fetch_product_by_barcode_not_found(mock_get):
    mock_get.return_value = _mock_response({"status": 0})
    product = fetch_product_by_barcode("0000000000")
    assert product is None


@patch("external_api.requests.get")
def test_fetch_product_by_barcode_network_error(mock_get):
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("no network")

    with pytest.raises(ExternalAPIError):
        fetch_product_by_barcode("1234567890")


@patch("external_api.requests.get")
def test_search_products_by_name_returns_list(mock_get):
    mock_get.return_value = _mock_response({
        "products": [
            {"code": "111", "product_name": "Apple Juice", "brands": "BrandA"},
            {"code": "222", "product_name": "Orange Juice", "brands": "BrandB"},
        ]
    })

    results = search_products_by_name("juice")
    assert len(results) == 2
    assert results[0]["name"] == "Apple Juice"
    assert results[1]["barcode"] == "222"


@patch("external_api.requests.get")
def test_search_products_by_name_empty_results(mock_get):
    mock_get.return_value = _mock_response({"products": []})
    results = search_products_by_name("nonexistentproductxyz")
    assert results == []


@patch("external_api.requests.get")
def test_search_products_by_name_network_error(mock_get):
    import requests
    mock_get.side_effect = requests.exceptions.Timeout("timed out")

    with pytest.raises(ExternalAPIError):
        search_products_by_name("juice")
