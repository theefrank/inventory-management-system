"""
cli.py
------
A simple menu-driven command line interface that talks to the Flask
REST API over HTTP using the `requests` library. This is the
"user interface" that lets an employee browse/manage inventory and
pull product data in from OpenFoodFacts without touching curl or Postman.

Run the API first:  python app.py
Then, in another terminal:  python cli.py
"""

import requests

API_BASE = "http://127.0.0.1:5000/api"


def list_items():
    resp = requests.get(f"{API_BASE}/items")
    items = resp.json()
    if not items:
        print("\nNo items in inventory yet.\n")
        return
    print("\nID  | Name                 | Barcode        | Qty  | Price")
    print("-" * 60)
    for item in items:
        print(
            f"{item['id']:<4}| {str(item['name'])[:20]:<20} | "
            f"{str(item.get('barcode') or '-'): <14} | "
            f"{item.get('quantity', 0):<4} | {item.get('price', 0):.2f}"
        )
    print()


def view_item():
    item_id = input("Item ID: ").strip()
    resp = requests.get(f"{API_BASE}/items/{item_id}")
    if resp.status_code == 200:
        print(resp.json())
    else:
        print(f"Error: {resp.json().get('error', resp.text)}")


def add_item():
    name = input("Name: ").strip()
    barcode = input("Barcode (optional): ").strip() or None
    brand = input("Brand (optional): ").strip() or None
    category = input("Category (optional): ").strip() or None
    quantity = input("Quantity [0]: ").strip() or 0
    price = input("Price [0.00]: ").strip() or 0.0

    payload = {
        "name": name,
        "barcode": barcode,
        "brand": brand,
        "category": category,
        "quantity": int(quantity),
        "price": float(price),
    }
    resp = requests.post(f"{API_BASE}/items", json=payload)
    if resp.status_code == 201:
        print("Item created:", resp.json())
    else:
        print("Error:", resp.json())


def edit_item():
    item_id = input("Item ID to edit: ").strip()
    print("Leave a field blank to keep it unchanged.")
    fields = {}
    for field in ["name", "barcode", "brand", "category", "quantity", "price", "description"]:
        val = input(f"{field}: ").strip()
        if val:
            fields[field] = val

    resp = requests.patch(f"{API_BASE}/items/{item_id}", json=fields)
    if resp.status_code == 200:
        print("Item updated:", resp.json())
    else:
        print("Error:", resp.json())


def delete_item():
    item_id = input("Item ID to delete: ").strip()
    resp = requests.delete(f"{API_BASE}/items/{item_id}")
    if resp.status_code == 200:
        print(resp.json().get("message"))
    else:
        print("Error:", resp.json())


def search_external():
    name = input("Product name to search on OpenFoodFacts: ").strip()
    resp = requests.get(f"{API_BASE}/external/search", params={"q": name})
    if resp.status_code != 200:
        print("Error:", resp.json())
        return

    results = resp.json()
    if not results:
        print("No results found.")
        return

    for idx, product in enumerate(results):
        print(f"[{idx}] {product.get('name')} ({product.get('barcode')}) - {product.get('brand')}")

    choice = input("Import which item into inventory? (index, or blank to cancel): ").strip()
    if not choice:
        return
    try:
        chosen = results[int(choice)]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    import_by_barcode(chosen.get("barcode"))


def import_by_barcode(barcode=None):
    if barcode is None:
        barcode = input("Barcode to import: ").strip()
    quantity = input("Quantity to stock [0]: ").strip() or 0
    price = input("Price [0.00]: ").strip() or 0.0

    resp = requests.post(
        f"{API_BASE}/items/import/{barcode}",
        json={"quantity": int(quantity), "price": float(price)},
    )
    if resp.status_code == 201:
        print("Imported and added to inventory:", resp.json())
    else:
        print("Error:", resp.json())


MENU = """
=== Inventory Management CLI ===
1) List all items
2) View one item
3) Add item manually
4) Edit item
5) Delete item
6) Search OpenFoodFacts by name (and optionally import)
7) Import item by barcode directly
0) Quit
"""


def main():
    actions = {
        "1": list_items,
        "2": view_item,
        "3": add_item,
        "4": edit_item,
        "5": delete_item,
        "6": search_external,
        "7": import_by_barcode,
    }
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action is None:
            print("Invalid option.")
            continue
        try:
            action()
        except requests.exceptions.ConnectionError:
            print("Could not reach the API. Is `python app.py` running?")


if __name__ == "__main__":
    main()
