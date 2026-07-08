"""
models.py
---------
All the CRUD logic for inventory items lives here. app.py (the Flask
routes) simply calls these functions, which keeps the HTTP layer thin
and makes the functions independently unit-testable.
"""

from database import get_connection, row_to_dict


REQUIRED_FIELDS = ["name"]


def validate_item_payload(data, partial=False):
    """
    Very small validation helper.
    Returns a list of error strings (empty list == valid).
    `partial=True` is used for PATCH, where not every field is required.
    """
    errors = []
    if not isinstance(data, dict):
        return ["Request body must be a JSON object."]

    if not partial:
        for field in REQUIRED_FIELDS:
            if field not in data or not str(data.get(field)).strip():
                errors.append(f"'{field}' is required.")

    if "quantity" in data and data["quantity"] is not None:
        try:
            int(data["quantity"])
        except (ValueError, TypeError):
            errors.append("'quantity' must be an integer.")

    if "price" in data and data["price"] is not None:
        try:
            float(data["price"])
        except (ValueError, TypeError):
            errors.append("'price' must be a number.")

    return errors


def get_all_items():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM items ORDER BY id").fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


def get_item(item_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


def create_item(data):
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO items (name, barcode, brand, category, quantity, price, description, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("name"),
            data.get("barcode"),
            data.get("brand"),
            data.get("category"),
            int(data.get("quantity", 0) or 0),
            float(data.get("price", 0.0) or 0.0),
            data.get("description"),
            data.get("image_url"),
        ),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return get_item(new_id)


def update_item(item_id, data):
    existing = get_item(item_id)
    if existing is None:
        return None

    updated = {**existing, **{k: v for k, v in data.items() if v is not None}}

    conn = get_connection()
    conn.execute(
        """
        UPDATE items
        SET name = ?, barcode = ?, brand = ?, category = ?,
            quantity = ?, price = ?, description = ?, image_url = ?
        WHERE id = ?
        """,
        (
            updated.get("name"),
            updated.get("barcode"),
            updated.get("brand"),
            updated.get("category"),
            int(updated.get("quantity") or 0),
            float(updated.get("price") or 0.0),
            updated.get("description"),
            updated.get("image_url"),
            item_id,
        ),
    )
    conn.commit()
    conn.close()
    return get_item(item_id)


def delete_item(item_id):
    existing = get_item(item_id)
    if existing is None:
        return False

    conn = get_connection()
    conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return True
