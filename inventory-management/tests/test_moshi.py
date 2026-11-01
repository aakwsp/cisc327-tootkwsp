# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
# test_moshi.py
# 
# test file for CISC327 A2
# 
# covers: list, add, view, update, delete prod, check stock level
# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_

def make_product(client, **overrides):
    """makes product thru api and ret the JSON body"""
    payload = {
        "name": "Hammer",
        "sku": "HAM-001",
        "unit_price": 12.50,
        "quantity_on_hand": 5,
        "reorder_level": 10,
    }
    payload.update(overrides)
    response = client.post("/products", json=payload)
    assert response.status_code == 201
    return response.get_json()
 
# -_-_-_-_-_-_-_-_-_-_-_-_- add product (r17, r29)
 
def test_create_product_returns_all_fields(client):
    product = make_product(client)
    assert product["id"] == 1
    assert product["name"] == "Hammer"
    assert product["sku"] == "HAM-001"
    assert product["unit_price"] == 12.50
    assert product["quantity_on_hand"] == 5
    assert product["reorder_level"] == 10
 
def test_create_product_uses_defaults_for_optional_fields(client):
    response = client.post("/products", json={"name": "Nails", "sku": "NAI-001"})
    assert response.status_code == 201
    product = response.get_json()
    assert product["unit_price"] == 0.0
    assert product["quantity_on_hand"] == 0
    assert product["reorder_level"] == 0
 
def test_created_products_get_unique_increasing_ids(client):
    first = make_product(client, sku="A-1")
    second = make_product(client, sku="A-2")
    assert second["id"] == first["id"] + 1
 
# -_-_-_-_-_-_-_-_-_-_-_-_- list all products (r29)
 
def test_list_products_returns_every_created_product(client):
    make_product(client, name="Hammer", sku="HAM-001")
    make_product(client, name="Screwdriver", sku="SCR-001")
    products = client.get("/products").get_json()
    assert len(products) == 2
    assert {p["name"] for p in products} == {"Hammer", "Screwdriver"}
 
def test_catalog_supports_500_products(client):
    """R29: the catalog must hold at least 500 products."""
    for i in range(500):
        make_product(client, name=f"Item {i}", sku=f"SKU-{i}")
    assert len(client.get("/products").get_json()) == 500
    last = client.get("/products/500")
    assert last.status_code == 200
    assert last.get_json()["sku"] == "SKU-499"
 
# -_-_-_-_-_-_-_-_-_-_-_-_- view one product (r1)

def test_get_product_returns_matching_product(client):
    created = make_product(client)
    response = client.get(f"/products/{created['id']}")
    assert response.status_code == 200
    assert response.get_json() == created
 
def test_get_nonexistent_product_returns_404(client):
    response = client.get("/products/999")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Product not found"
 
# -_-_-_-_-_-_-_-_-_-_-_-_- update one product (r4, r17)
 
def test_update_product_changes_only_given_fields(client):
    created = make_product(client)
    response = client.put(f"/products/{created['id']}", json={"unit_price": 15.00})
    assert response.status_code == 200
    updated = client.get(f"/products/{created['id']}").get_json()
    assert updated["unit_price"] == 15.00
    assert updated["name"] == "Hammer"
    assert updated["quantity_on_hand"] == 5
 
def test_update_reorder_level_persists(client):
    created = make_product(client, reorder_level=10)
    client.put(f"/products/{created['id']}", json={"reorder_level": 3})
    assert client.get(f"/products/{created['id']}").get_json()["reorder_level"] == 3
 
def test_update_nonexistent_product_returns_404(client):
    response = client.put("/products/999", json={"name": "Ghost"})
    assert response.status_code == 404
 
# -_-_-_-_-_-_-_-_-_-_-_-_- delete a product (no r)
 
def test_delete_product_removes_it(client):
    created = make_product(client)
    response = client.delete(f"/products/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/products/{created['id']}").status_code == 404
    assert client.get("/products").get_json() == []
 
def test_delete_product_twice_returns_404_second_time(client):
    created = make_product(client)
    assert client.delete(f"/products/{created['id']}").status_code == 204
    assert client.delete(f"/products/{created['id']}").status_code == 404
 
# -_-_-_-_-_-_-_-_-_-_-_-_- check stock level (r1, r14)
 
def test_stock_level_matches_created_quantity(client):
    created = make_product(client, quantity_on_hand=42)
    body = client.get(f"/products/{created['id']}/stock-level").get_json()
    assert body == {"product_id": created["id"], "quantity_on_hand": 42}
 
def test_stock_level_reflects_product_update(client):
    created = make_product(client, quantity_on_hand=10)
    client.put(f"/products/{created['id']}", json={"quantity_on_hand": 8})
    body = client.get(f"/products/{created['id']}/stock-level").get_json()
    assert body["quantity_on_hand"] == 8
 
def test_stock_level_for_nonexistent_product_returns_404(client):
    assert client.get("/products/999/stock-level").status_code == 404

# -_-_-_-_-_-_-_-_-_-_-_-_- view low stock prod (r17, r18, r19)

def test_low_stock_includes_product_at_threshold(client):
    """Boundary: quantity equal to reorder_level counts as low stock."""
    make_product(client, name="Hammer", sku="HAM-001", quantity_on_hand=10, reorder_level=10)
    flagged = client.get("/products/low-stock").get_json()
    assert [p["name"] for p in flagged] == ["Hammer"]


def test_low_stock_excludes_product_above_threshold(client):
    make_product(client, name="Hammer", sku="HAM-001", quantity_on_hand=11, reorder_level=10)
    assert client.get("/products/low-stock").get_json() == []


def test_low_stock_only_lists_flagged_products(client):
    make_product(client, name="Hammer", sku="HAM-001", quantity_on_hand=2, reorder_level=10)
    make_product(client, name="Saw", sku="SAW-001", quantity_on_hand=50, reorder_level=10)
    flagged = client.get("/products/low-stock").get_json()
    assert [p["name"] for p in flagged] == ["Hammer"]


def test_product_becomes_low_stock_after_outgoing_transaction(client):
    """Workflow: an OUT transaction drops stock to the threshold."""
    product = make_product(client, quantity_on_hand=12, reorder_level=10)
    assert client.get("/products/low-stock").get_json() == []
    client.post("/transactions", json={"product_id": product["id"], "type": "OUT", "quantity": 2})
    flagged = client.get("/products/low-stock").get_json()
    assert [p["id"] for p in flagged] == [product["id"]]

# -_-_-_-_-_-_-_-_-_-_-_-_- record incoming stock (r1, r2, r6, r8)

def test_incoming_transaction_increases_stock(client):
    product = make_product(client, quantity_on_hand=5)
    response = client.post(
        "/transactions",
        json={"product_id": product["id"], "type": "IN", "quantity": 7},
    )
    assert response.status_code == 201
    tx = response.get_json()
    assert tx["type"] == "IN"
    assert tx["quantity"] == 7
    assert tx["product_id"] == product["id"]
    stock = client.get(f"/products/{product['id']}/stock-level").get_json()
    assert stock["quantity_on_hand"] == 12


def test_incoming_transaction_records_supplier(client):
    product = make_product(client)
    client.post("/suppliers", json={"name": "Acme Tools", "contact_email": "acme@example.com"})
    tx = client.post(
        "/transactions",
        json={"product_id": product["id"], "type": "IN", "quantity": 3, "supplier_id": 1},
    ).get_json()
    assert tx["supplier_id"] == 1


def test_transaction_for_nonexistent_product_returns_404_and_is_not_logged(client):
    response = client.post("/transactions", json={"product_id": 999, "type": "IN", "quantity": 5})
    assert response.status_code == 404
    assert client.get("/transactions").get_json() == []


def test_invalid_transaction_type_is_rejected_and_stock_unchanged(client):
    product = make_product(client, quantity_on_hand=5)
    response = client.post(
        "/transactions",
        json={"product_id": product["id"], "type": "MOVE", "quantity": 5},
    )
    assert response.status_code == 400
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 5

# -_-_-_-_-_-_-_-_-_-_-_-_- record outgoing stock (r1, r3, r6, r8)

def test_outgoing_transaction_decreases_stock(client):
    product = make_product(client, quantity_on_hand=12)
    response = client.post(
        "/transactions",
        json={"product_id": product["id"], "type": "OUT", "quantity": 2},
    )
    assert response.status_code == 201
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 10


def test_in_then_out_leaves_correct_stock(client):
    """Workflow: 5 + 7 - 2 = 10 (mirrors the Table A R1 check)."""
    product = make_product(client, quantity_on_hand=5)
    client.post("/transactions", json={"product_id": product["id"], "type": "IN", "quantity": 7})
    client.post("/transactions", json={"product_id": product["id"], "type": "OUT", "quantity": 2})
    assert client.get(f"/products/{product['id']}/stock-level").get_json()["quantity_on_hand"] == 10


def test_outgoing_transaction_with_negative_quantity_is_rejected(client):
    """R3: OUT must decrease stock. KNOWN DEFECT: the API accepts -3 and
    increases stock from 5 to 8 instead of rejecting the request."""
    product = make_product(client, quantity_on_hand=5)
    response = client.post(
        "/transactions",
        json={"product_id": product["id"], "type": "OUT", "quantity": -3},
    )
    assert response.status_code == 400
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 5


def test_outgoing_transaction_cannot_exceed_stock_on_hand(client):
    """R1/R3: stock on hand cannot go below zero. KNOWN DEFECT: an OUT of 10
    against 5 in stock is accepted and leaves quantity_on_hand at -5."""
    product = make_product(client, quantity_on_hand=5)
    response = client.post(
        "/transactions",
        json={"product_id": product["id"], "type": "OUT", "quantity": 10},
    )
    assert response.status_code == 400
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 5

# -_-_-_-_-_-_-_-_-_-_-_-_- view / filter transactions (r5)

def test_transactions_list_starts_empty(client):
    assert client.get("/transactions").get_json() == []


def test_transaction_log_includes_type_quantity_and_date(client):
    """R5 (partial): each logged change has a type, quantity and date."""
    product = make_product(client)
    client.post("/transactions", json={"product_id": product["id"], "type": "IN", "quantity": 4})
    log = client.get("/transactions").get_json()
    assert len(log) == 1
    entry = log[0]
    assert entry["type"] == "IN"
    assert entry["quantity"] == 4
    assert entry["product_id"] == product["id"]
    assert entry["transaction_date"]  # ISO date string, e.g. "2026-11-01"


def test_filter_transactions_by_supplier(client):
    product = make_product(client)
    client.post("/suppliers", json={"name": "Acme Tools", "contact_email": "acme@example.com"})
    client.post("/suppliers", json={"name": "Kingston Supply", "contact_email": "ks@example.com"})
    client.post("/transactions", json={"product_id": product["id"], "type": "IN", "quantity": 1, "supplier_id": 1})
    client.post("/transactions", json={"product_id": product["id"], "type": "IN", "quantity": 2, "supplier_id": 2})
    results = client.get("/transactions?supplier_id=2").get_json()
    assert [t["quantity"] for t in results] == [2]


def test_filter_transactions_by_product_returns_only_that_product(client):
    """R5: staff must be able to review a product's stock changes.
    KNOWN DEFECT: the product_id filter compares against supplier_id, so the
    OUT transaction (no supplier) for product 1 is dropped from the results."""
    hammer = make_product(client, name="Hammer", sku="HAM-001")
    make_product(client, name="Saw", sku="SAW-001")
    client.post("/suppliers", json={"name": "Acme Tools", "contact_email": "acme@example.com"})
    client.post("/transactions", json={"product_id": hammer["id"], "type": "OUT", "quantity": 1})
    client.post("/transactions", json={"product_id": hammer["id"], "type": "IN", "quantity": 2, "supplier_id": 1})
    client.post("/transactions", json={"product_id": 2, "type": "IN", "quantity": 3})
    results = client.get(f"/transactions?product_id={hammer['id']}").get_json()
    assert sorted(t["quantity"] for t in results) == [1, 2]
    assert all(t["product_id"] == hammer["id"] for t in results)