def create_supplier(client, name="Acme Tools", email="sales@acme.ca"):
    response = client.post(
        "/suppliers",
        json={
            "name": name,
            "contact_email": email,
        },
    )

    assert response.status_code == 201
    return response.get_json()


def test_add_supplier_returns_expected_data_and_persists(client):
    supplier = create_supplier(client)

    assert supplier["name"] == "Acme Tools"
    assert supplier["contact_email"] == "sales@acme.ca"

    supplier_id = supplier["id"]

    response = client.get(f"/suppliers/{supplier_id}")
    assert response.status_code == 200
    assert response.get_json() == supplier


def test_list_suppliers_returns_all_created_suppliers(client):
    create_supplier(client, "Acme Tools", "sales@acme.ca")
    create_supplier(client, "Kingston Hardware", "sales@kingston.ca")

    response = client.get("/suppliers")

    assert response.status_code == 200

    suppliers = response.get_json()

    assert len(suppliers) == 2
    assert suppliers[0]["name"] == "Acme Tools"
    assert suppliers[1]["name"] == "Kingston Hardware"


def test_get_single_supplier_returns_correct_supplier(client):
    first = create_supplier(client, "Acme Tools", "sales@acme.ca")
    second = create_supplier(
        client,
        "Kingston Hardware",
        "sales@kingston.ca",
    )

    response = client.get(f"/suppliers/{second['id']}")

    assert response.status_code == 200

    supplier = response.get_json()

    assert supplier["id"] == second["id"]
    assert supplier["name"] == "Kingston Hardware"
    assert supplier["contact_email"] == "sales@kingston.ca"
    assert supplier["id"] != first["id"]


def test_update_supplier_changes_and_persists_data(client):
    supplier = create_supplier(client)
    supplier_id = supplier["id"]

    response = client.put(
        f"/suppliers/{supplier_id}",
        json={
            "name": "Updated Tools",
            "contact_email": "new@acme.ca",
        },
    )

    assert response.status_code == 200

    updated = response.get_json()

    assert updated["name"] == "Updated Tools"
    assert updated["contact_email"] == "new@acme.ca"

    get_response = client.get(f"/suppliers/{supplier_id}")
    persisted = get_response.get_json()

    assert persisted["name"] == "Updated Tools"
    assert persisted["contact_email"] == "new@acme.ca"


def test_delete_supplier_removes_supplier(client):
    supplier = create_supplier(client)
    supplier_id = supplier["id"]

    delete_response = client.delete(f"/suppliers/{supplier_id}")

    assert delete_response.status_code == 204

    get_response = client.get(f"/suppliers/{supplier_id}")
    assert get_response.status_code == 404
    assert get_response.get_json()["error"] == "Supplier not found"

    list_response = client.get("/suppliers")
    assert list_response.status_code == 200
    assert list_response.get_json() == []


def create_product(client, name="Hammer", sku="HAM-001"):
    response = client.post(
        "/products",
        json={
            "name": name,
            "sku": sku,
            "unit_price": 19.99,
            "quantity_on_hand": 5,
            "reorder_level": 2,
        },
    )

    assert response.status_code == 201
    return response.get_json()


def test_supplier_products_returns_products_received_from_supplier(client):
    supplier = create_supplier(client)
    hammer = create_product(client, "Hammer", "HAM-001")
    drill = create_product(client, "Drill", "DRL-001")

    in_response = client.post(
        "/transactions",
        json={
            "product_id": hammer["id"],
            "supplier_id": supplier["id"],
            "type": "IN",
            "quantity": 10,
        },
    )
    assert in_response.status_code == 201

    client.post(
        "/transactions",
        json={
            "product_id": drill["id"],
            "type": "OUT",
            "quantity": 1,
        },
    )

    response = client.get(f"/suppliers/{supplier['id']}/products")

    assert response.status_code == 200

    products = response.get_json()

    assert len(products) == 1
    assert products[0]["id"] == hammer["id"]
    assert products[0]["name"] == "Hammer"


def test_supplier_products_returns_404_for_missing_supplier(client):
    response = client.get("/suppliers/999/products")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Supplier not found"


def create_purchase_order(client, supplier_id, product_id, quantity=10):
    response = client.post(
        "/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "product_id": product_id,
            "quantity_ordered": quantity,
        },
    )

    assert response.status_code == 201
    return response.get_json()


def test_create_purchase_order_returns_expected_data_and_persists(client):
    supplier = create_supplier(client)
    product = create_product(client)

    purchase_order = create_purchase_order(
        client,
        supplier["id"],
        product["id"],
        quantity=12,
    )

    assert purchase_order["supplier_id"] == supplier["id"]
    assert purchase_order["product_id"] == product["id"]
    assert purchase_order["quantity_ordered"] == 12
    assert purchase_order["status"] == "pending"
    assert purchase_order["received_date"] is None

    response = client.get(f"/purchase-orders/{purchase_order['id']}")

    assert response.status_code == 200
    assert response.get_json() == purchase_order


def test_list_purchase_orders_returns_all_orders(client):
    supplier = create_supplier(client)
    hammer = create_product(client, "Hammer", "HAM-001")
    drill = create_product(client, "Drill", "DRL-001")

    first = create_purchase_order(
        client,
        supplier["id"],
        hammer["id"],
        quantity=5,
    )

    second = create_purchase_order(
        client,
        supplier["id"],
        drill["id"],
        quantity=8,
    )

    response = client.get("/purchase-orders")

    assert response.status_code == 200

    orders = response.get_json()

    assert len(orders) == 2
    assert orders[0]["id"] == first["id"]
    assert orders[1]["id"] == second["id"]
    assert orders[0]["quantity_ordered"] == 5
    assert orders[1]["quantity_ordered"] == 8


def test_get_single_purchase_order_returns_correct_order(client):
    supplier = create_supplier(client)
    hammer = create_product(client, "Hammer", "HAM-001")
    drill = create_product(client, "Drill", "DRL-001")

    first = create_purchase_order(
        client,
        supplier["id"],
        hammer["id"],
        quantity=5,
    )

    second = create_purchase_order(
        client,
        supplier["id"],
        drill["id"],
        quantity=8,
    )

    response = client.get(f"/purchase-orders/{second['id']}")

    assert response.status_code == 200

    order = response.get_json()

    assert order["id"] == second["id"]
    assert order["product_id"] == drill["id"]
    assert order["quantity_ordered"] == 8
    assert order["id"] != first["id"]


def test_receive_purchase_order_marks_received_and_records_transaction(client):
    supplier = create_supplier(client)
    product = create_product(client)

    purchase_order = create_purchase_order(
        client,
        supplier["id"],
        product["id"],
        quantity=10,
    )

    response = client.put(
        f"/purchase-orders/{purchase_order['id']}/receive"
    )

    assert response.status_code == 200

    received = response.get_json()

    assert received["status"] == "received"
    assert received["received_date"] is not None

    transaction_response = client.get("/transactions")
    assert transaction_response.status_code == 200

    transactions = transaction_response.get_json()

    assert len(transactions) == 1
    assert transactions[0]["product_id"] == product["id"]
    assert transactions[0]["supplier_id"] == supplier["id"]
    assert transactions[0]["type"] == "IN"
    assert transactions[0]["quantity"] == 10


def test_receive_purchase_order_increases_product_stock(client):
    supplier = create_supplier(client)

    product_response = client.post(
        "/products",
        json={
            "name": "Hammer",
            "sku": "HAM-001",
            "unit_price": 19.99,
            "quantity_on_hand": 5,
            "reorder_level": 2,
        },
    )
    assert product_response.status_code == 201
    product = product_response.get_json()

    purchase_order = create_purchase_order(
        client,
        supplier["id"],
        product["id"],
        quantity=10,
    )

    receive_response = client.put(
        f"/purchase-orders/{purchase_order['id']}/receive"
    )
    assert receive_response.status_code == 200

    stock_response = client.get(
        f"/products/{product['id']}/stock-level"
    )
    assert stock_response.status_code == 200

    assert stock_response.get_json()["quantity_on_hand"] == 15


def test_receiving_purchase_order_twice_is_rejected(client):
    supplier = create_supplier(client)
    product = create_product(client)

    purchase_order = create_purchase_order(
        client,
        supplier["id"],
        product["id"],
        quantity=10,
    )

    first_response = client.put(
        f"/purchase-orders/{purchase_order['id']}/receive"
    )
    assert first_response.status_code == 200

    second_response = client.put(
        f"/purchase-orders/{purchase_order['id']}/receive"
    )

    assert second_response.status_code == 400
    assert second_response.get_json()["error"] == (
        "Purchase order already received"
    )

    transactions = client.get("/transactions").get_json()
    assert len(transactions) == 1


def test_get_missing_purchase_order_returns_404(client):
    response = client.get("/purchase-orders/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Purchase order not found"


def test_receive_purchase_order_with_partial_quantity(client):
    supplier = create_supplier(client)
    product = create_product(client)

    purchase_order = create_purchase_order(
        client,
        supplier["id"],
        product["id"],
        quantity=10,
    )

    response = client.put(
        f"/purchase-orders/{purchase_order['id']}/receive",
        json={"quantity_received": 7},
    )

    assert response.status_code == 200

    received = response.get_json()

    assert received["status"] == "received"
    assert received["quantity_received"] == 7

    stock_response = client.get(
        f"/products/{product['id']}/stock-level"
    )
    assert stock_response.status_code == 200
    assert stock_response.get_json()["quantity_on_hand"] == 12

    transactions = client.get("/transactions").get_json()
    assert len(transactions) == 1
    assert transactions[0]["quantity"] == 7


def test_receive_purchase_order_rejects_invalid_received_quantity(client):
    supplier = create_supplier(client)
    product = create_product(client)

    purchase_order = create_purchase_order(
        client,
        supplier["id"],
        product["id"],
        quantity=10,
    )

    response = client.put(
        f"/purchase-orders/{purchase_order['id']}/receive",
        json={"quantity_received": 0},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "quantity_received must be a positive integer"
    )

    order = client.get(
        f"/purchase-orders/{purchase_order['id']}"
    ).get_json()

    assert order["status"] == "pending"
    assert order["quantity_received"] is None

    stock = client.get(
        f"/products/{product['id']}/stock-level"
    ).get_json()

    assert stock["quantity_on_hand"] == 5
    assert client.get("/transactions").get_json() == []