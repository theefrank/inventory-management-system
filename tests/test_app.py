"""
tests/test_app.py
------------------
Tests for every Flask route: health check, and full CRUD lifecycle.
Uses Flask's built-in test client, so no live server is required.
Each test resets the database first so tests are independent/repeatable.
"""

import sys
import os
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


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_index_route_lists_endpoints(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "endpoints" in resp.get_json()


def test_list_items_empty(client):
    resp = client.get("/api/items")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_item_success(client):
    payload = {"name": "Canned Beans", "quantity": 10, "price": 1.99}
    resp = client.post("/api/items", json=payload)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Canned Beans"
    assert data["quantity"] == 10
    assert data["id"] is not None


def test_create_item_missing_name_fails(client):
    resp = client.post("/api/items", json={"quantity": 5})
    assert resp.status_code == 400
    assert "errors" in resp.get_json()


def test_create_item_bad_quantity_type_fails(client):
    resp = client.post("/api/items", json={"name": "Bad Item", "quantity": "abc"})
    assert resp.status_code == 400


def test_get_item_found(client):
    created = client.post("/api/items", json={"name": "Rice", "quantity": 20, "price": 3.5}).get_json()
    resp = client.get(f"/api/items/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Rice"


def test_get_item_not_found(client):
    resp = client.get("/api/items/9999")
    assert resp.status_code == 404


def test_list_items_returns_created_items(client):
    client.post("/api/items", json={"name": "Item A", "quantity": 1, "price": 1.0})
    client.post("/api/items", json={"name": "Item B", "quantity": 2, "price": 2.0})
    resp = client.get("/api/items")
    data = resp.get_json()
    assert len(data) == 2
    names = {item["name"] for item in data}
    assert names == {"Item A", "Item B"}


def test_update_item_success(client):
    created = client.post("/api/items", json={"name": "Old Name", "quantity": 5, "price": 1.0}).get_json()
    resp = client.patch(f"/api/items/{created['id']}", json={"name": "New Name", "quantity": 50})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "New Name"
    assert data["quantity"] == 50
    # price should be unchanged
    assert data["price"] == 1.0


def test_update_item_not_found(client):
    resp = client.patch("/api/items/9999", json={"name": "Ghost"})
    assert resp.status_code == 404


def test_update_item_bad_price_fails(client):
    created = client.post("/api/items", json={"name": "Item", "quantity": 1, "price": 1.0}).get_json()
    resp = client.patch(f"/api/items/{created['id']}", json={"price": "not-a-number"})
    assert resp.status_code == 400


def test_delete_item_success(client):
    created = client.post("/api/items", json={"name": "To Delete", "quantity": 1, "price": 1.0}).get_json()
    resp = client.delete(f"/api/items/{created['id']}")
    assert resp.status_code == 200

    follow_up = client.get(f"/api/items/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_item_not_found(client):
    resp = client.delete("/api/items/9999")
    assert resp.status_code == 404


def test_full_crud_lifecycle(client):
    """End-to-end: create -> read -> update -> delete."""
    created = client.post(
        "/api/items", json={"name": "Lifecycle Item", "quantity": 3, "price": 9.99}
    ).get_json()
    item_id = created["id"]

    read_resp = client.get(f"/api/items/{item_id}")
    assert read_resp.get_json()["name"] == "Lifecycle Item"

    update_resp = client.patch(f"/api/items/{item_id}", json={"quantity": 30})
    assert update_resp.get_json()["quantity"] == 30

    delete_resp = client.delete(f"/api/items/{item_id}")
    assert delete_resp.status_code == 200

    final_resp = client.get(f"/api/items/{item_id}")
    assert final_resp.status_code == 404
