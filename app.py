"""
app.py
------
Flask REST API for the Inventory Management System.

Routes
------
Health / helper:
  GET    /api/health                     -> simple uptime check

CRUD (inventory):
  GET    /api/items                      -> list all items
  GET    /api/items/<id>                 -> get one item
  POST   /api/items                      -> create an item manually
  PATCH  /api/items/<id>                 -> partially update an item
  DELETE /api/items/<id>                 -> delete an item

External API (OpenFoodFacts):
  GET    /api/external/barcode/<barcode> -> look up a product by barcode (not saved)
  GET    /api/external/search?q=<name>   -> search products by name (not saved)
  POST   /api/items/import/<barcode>     -> fetch by barcode AND add straight to inventory
"""

from flask import Flask, request, jsonify

import models
from database import init_db
from external_api import fetch_product_by_barcode, search_products_by_name, ExternalAPIError


def create_app():
    app = Flask(__name__)
    init_db()

    # ---------------------------------------------------------------
    # Helper routes
    # ---------------------------------------------------------------
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get("/")
    def index():
        return jsonify({
            "service": "Inventory Management System API",
            "endpoints": [
                "/api/health",
                "/api/items",
                "/api/items/<id>",
                "/api/external/barcode/<barcode>",
                "/api/external/search?q=<name>",
                "/api/items/import/<barcode>",
            ],
        }), 200

    # ---------------------------------------------------------------
    # CRUD routes
    # ---------------------------------------------------------------
    @app.get("/api/items")
    def list_items():
        return jsonify(models.get_all_items()), 200

    @app.get("/api/items/<int:item_id>")
    def get_item(item_id):
        item = models.get_item(item_id)
        if item is None:
            return jsonify({"error": f"Item {item_id} not found."}), 404
        return jsonify(item), 200

    @app.post("/api/items")
    def create_item():
        data = request.get_json(silent=True) or {}
        errors = models.validate_item_payload(data, partial=False)
        if errors:
            return jsonify({"errors": errors}), 400
        item = models.create_item(data)
        return jsonify(item), 201

    @app.patch("/api/items/<int:item_id>")
    def update_item(item_id):
        data = request.get_json(silent=True) or {}
        errors = models.validate_item_payload(data, partial=True)
        if errors:
            return jsonify({"errors": errors}), 400
        item = models.update_item(item_id, data)
        if item is None:
            return jsonify({"error": f"Item {item_id} not found."}), 404
        return jsonify(item), 200

    @app.delete("/api/items/<int:item_id>")
    def delete_item(item_id):
        deleted = models.delete_item(item_id)
        if not deleted:
            return jsonify({"error": f"Item {item_id} not found."}), 404
        return jsonify({"message": f"Item {item_id} deleted."}), 200

    # ---------------------------------------------------------------
    # External API routes
    # ---------------------------------------------------------------
    @app.get("/api/external/barcode/<barcode>")
    def external_barcode(barcode):
        try:
            product = fetch_product_by_barcode(barcode)
        except ExternalAPIError as exc:
            return jsonify({"error": str(exc)}), 502

        if product is None:
            return jsonify({"error": f"No product found for barcode {barcode}."}), 404
        return jsonify(product), 200

    @app.get("/api/external/search")
    def external_search():
        name = request.args.get("q", "").strip()
        if not name:
            return jsonify({"error": "Query parameter 'q' is required."}), 400
        try:
            results = search_products_by_name(name)
        except ExternalAPIError as exc:
            return jsonify({"error": str(exc)}), 502
        return jsonify(results), 200

    @app.post("/api/items/import/<barcode>")
    def import_item_from_barcode(barcode):
        """Fetch a product from OpenFoodFacts and add it straight to inventory."""
        try:
            product = fetch_product_by_barcode(barcode)
        except ExternalAPIError as exc:
            return jsonify({"error": str(exc)}), 502

        if product is None:
            return jsonify({"error": f"No product found for barcode {barcode}."}), 404

        overrides = request.get_json(silent=True) or {}
        payload = {
            "name": product.get("name"),
            "barcode": product.get("barcode") or barcode,
            "brand": product.get("brand"),
            "category": product.get("category"),
            "description": product.get("description"),
            "image_url": product.get("image_url"),
            "quantity": overrides.get("quantity", 0),
            "price": overrides.get("price", 0.0),
        }
        item = models.create_item(payload)
        return jsonify(item), 201

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
