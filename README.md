# Inventory Management System

A Flask REST API for a small retail company's admin portal. Employees can
add, view, edit, and delete inventory items, and can pull real product
details (name, brand, category, image, etc.) straight from the
[OpenFoodFacts API](https://world.openfoodfacts.org/data) by barcode or
product name instead of typing everything in by hand.

## Task 1: Define the Problem

Retail staff need a single tool to:
1. Keep an accurate, persistent record of inventory (name, barcode, brand,
   category, quantity on hand, price, description, image).
2. Avoid re-typing product details that already exist in a public product
   database — look them up by barcode/name and import them instead.
3. Manage all of this without needing to know curl/Postman — a simple CLI
   menu is enough for day-to-day use.
4. Trust that the system works — automated tests cover every route.

## Task 2: Determine the Design

**Architecture**

```
┌────────────┐        HTTP/JSON        ┌────────────────┐        HTTP/JSON        ┌────────────────────┐
│  cli.py    │ ──────────────────────▶ │   app.py        │ ──────────────────────▶ │  OpenFoodFacts API  │
│ (CLI menu) │ ◀────────────────────── │  (Flask routes) │ ◀────────────────────── │  (external service) │
└────────────┘                         └───────┬─────────┘                         └────────────────────┘
                                                │
                                                ▼
                                        ┌───────────────┐
                                        │  models.py     │
                                        │ (CRUD logic)   │
                                        └───────┬────────┘
                                                │
                                                ▼
                                        ┌───────────────┐
                                        │ database.py    │
                                        │ (SQLite store) │
                                        └───────────────┘
```

- **`database.py`** — SQLite connection + schema (`items` table). Acts as our
  persistent inventory "array".
- **`models.py`** — All CRUD functions (`get_all_items`, `get_item`,
  `create_item`, `update_item`, `delete_item`) plus payload validation.
  Kept separate from Flask so it's independently testable.
- **`external_api.py`** — Wraps the two OpenFoodFacts endpoints we use
  (lookup by barcode, search by name) and normalizes the response into the
  fields our inventory cares about.
- **`app.py`** — Flask app wiring routes to `models.py` / `external_api.py`.
- **`cli.py`** — Menu-driven command line client that calls the Flask API
  with `requests`, so employees never touch raw HTTP.
- **`tests/`** — Pytest suite covering CRUD, external API (mocked), and the
  combined "import from external API" route.

**Data model** (`items` table)

| Field       | Type    | Notes                              |
|-------------|---------|-------------------------------------|
| id          | INTEGER | primary key, autoincrement          |
| name        | TEXT    | required                            |
| barcode     | TEXT    | optional, from OpenFoodFacts        |
| brand       | TEXT    | optional                            |
| category    | TEXT    | optional                            |
| quantity    | INTEGER | default 0                           |
| price       | REAL    | default 0.0                         |
| description | TEXT    | optional                            |
| image_url   | TEXT    | optional                            |

## Task 3: Develop the Code

### Setup

```bash
git clone <your-repo-url>
cd inventory-management-system
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run the API

```bash
python app.py
```

The API starts at `http://127.0.0.1:5000`. SQLite storage is created
automatically as `inventory.db` on first run.

### Run the CLI (in a second terminal, with the API still running)

```bash
python cli.py
```

You'll get a menu to list, view, add, edit, delete, and import items.

### API Reference

| Method | Route                              | Description                                             |
|--------|-------------------------------------|-----------------------------------------------------------|
| GET    | `/api/health`                      | Health check                                              |
| GET    | `/`                                 | Lists available endpoints                                  |
| GET    | `/api/items`                       | List all inventory items                                   |
| GET    | `/api/items/<id>`                  | Get one item                                                |
| POST   | `/api/items`                       | Create an item manually (JSON body: `name` required)       |
| PATCH  | `/api/items/<id>`                  | Partially update an item                                    |
| DELETE | `/api/items/<id>`                  | Delete an item                                              |
| GET    | `/api/external/barcode/<barcode>`  | Look up a product on OpenFoodFacts (not saved)              |
| GET    | `/api/external/search?q=<name>`    | Search OpenFoodFacts by name (not saved)                    |
| POST   | `/api/items/import/<barcode>`      | Fetch a product by barcode **and** save it to inventory      |

**Example: create an item**
```bash
curl -X POST http://127.0.0.1:5000/api/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Canned Beans", "quantity": 24, "price": 1.99}'
```

**Example: import a real product from OpenFoodFacts straight into inventory**
```bash
curl -X POST http://127.0.0.1:5000/api/items/import/5000112637922 \
  -H "Content-Type: application/json" \
  -d '{"quantity": 24, "price": 1.25}'
```

## Task 4: Test and Debug

Run the full test suite:

```bash
pip install pytest
pytest -v
```

The suite (`tests/`) covers:
- `test_app.py` — health check, and the full CRUD lifecycle (create, read,
  update, delete) plus validation error cases (missing name, bad
  quantity/price types, 404s on unknown IDs).
- `test_external_api.py` — OpenFoodFacts wrapper functions, with
  `requests.get` mocked so tests never touch the real network: successful
  lookup, "not found", search results, and network-failure handling.
- `test_import_route.py` — the combined "fetch from external API + save
  to inventory" route, and the search route, both with the external call
  mocked.

Debugging notes:
- All routes return structured JSON errors (`{"error": "..."}` or
  `{"errors": [...]}`) with appropriate HTTP status codes (400, 404, 502)
  so problems are easy to diagnose from the CLI or curl.
- `external_api.py` raises a custom `ExternalAPIError` on network/timeout
  issues, which `app.py` turns into a `502 Bad Gateway` instead of letting
  the server crash.

## Task 5: Document and Maintain

- Keep this README up to date whenever a route or field changes.
- Suggested Git workflow used for this project:
  1. `main` branch always holds a working, tested version.
  2. New work happens on feature branches, e.g. `feature/crud-routes`,
     `feature/external-api`, `feature/cli`, `feature/tests`.
  3. Open a pull request into `main` for each feature; review, then merge.
  4. Delete the feature branch after merge to keep the branch list clean.
- To extend the system: add new fields to the `items` table in
  `database.py`, update `models.py`'s validation/CRUD SQL, and expose them
  through `app.py`. The CLI and tests should be updated alongside.

## Project Structure

```
inventory-management-system/
├── app.py                  # Flask routes
├── models.py                # CRUD logic + validation
├── database.py               # SQLite connection/schema
├── external_api.py            # OpenFoodFacts integration
├── cli.py                      # Command line client
├── requirements.txt
├── .gitignore
├── README.md
└── tests/
    ├── __init__.py
    ├── test_app.py
    ├── test_external_api.py
    └── test_import_route.py
```
