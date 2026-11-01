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

