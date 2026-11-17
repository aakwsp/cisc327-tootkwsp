# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
# test_a3_moshi.py
#
# test file for A3
#
# part 1: coverage-directed tests from the baseline report
#   - home page 
#   - transaction UI page
#   - supplier API not-found paths
#   - purchase order API not-found paths 
# part 2: low-stock notification tests 
# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_

from unittest.mock import patch

from app import store


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


def make_supplier(client, **overrides):
    """makes supplier thru api and ret the JSON body"""
    payload = {"name": "Acme Tools", "contact_email": "acme@example.com"}
    payload.update(overrides)
    response = client.post("/suppliers", json=payload)
    assert response.status_code == 201
    return response.get_json()


# -_-_-_-_-_-_-_-_-_-_-_-_- home page (views.py line 13)

def test_home_page_links_to_every_ui_section(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Inventory Management System" in html
    assert 'href="/ui/products"' in html
    assert 'href="/ui/suppliers"' in html
    assert 'href="/ui/transactions"' in html


# -_-_-_-_-_-_-_-_-_-_-_-_- transaction UI page (views.py lines 60-85)

def test_transactions_page_with_no_transactions_shows_empty_table(client):
    response = client.get("/ui/transactions")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Record a Stock Movement" in html
    assert "<td>" not in html  # header row only, no transaction rows
    assert store.transactions == {}


def test_ui_incoming_transaction_adds_stock_and_records_supplier(client):
    product = make_product(client, quantity_on_hand=5)
    supplier = make_supplier(client)
    response = client.post(
        "/ui/transactions",
        data={
            "product_id": str(product["id"]),
            "type": "IN",
            "quantity": "7",
            "supplier_id": str(supplier["id"]),
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ui/transactions")
    assert store.products[product["id"]].quantity_on_hand == 12
    assert len(store.transactions) == 1
    recorded = store.transactions[1]
    assert recorded.product_id == product["id"]
    assert recorded.type == "IN"
    assert recorded.quantity == 7
    assert recorded.supplier_id == supplier["id"]


def test_ui_outgoing_transaction_removes_stock_without_supplier(client):
    product = make_product(client, quantity_on_hand=5)
    response = client.post(
        "/ui/transactions",
        data={
            "product_id": str(product["id"]),
            "type": "OUT",
            "quantity": "2",
            "supplier_id": "",  # the form sends an empty string when left blank
        },
    )
    assert response.status_code == 302
    assert store.products[product["id"]].quantity_on_hand == 3
    recorded = store.transactions[1]
    assert recorded.type == "OUT"
    assert recorded.quantity == 2
    assert recorded.supplier_id is None


def test_ui_outgoing_transaction_for_all_stock_leaves_zero(client):
    """boundary: taking out exactly what is on hand leaves 0, not negative"""
    product = make_product(client, quantity_on_hand=5)
    response = client.post(
        "/ui/transactions",
        data={"product_id": str(product["id"]), "type": "OUT", "quantity": "5"},
    )
    assert response.status_code == 302
    assert store.products[product["id"]].quantity_on_hand == 0
    assert len(store.transactions) == 1


def test_ui_transaction_for_unknown_product_records_nothing(client):
    product = make_product(client, quantity_on_hand=5)
    response = client.post(
        "/ui/transactions",
        data={"product_id": "999", "type": "IN", "quantity": "4"},
    )
    assert response.status_code == 302
    assert store.transactions == {}
    assert store.products[product["id"]].quantity_on_hand == 5


def test_recorded_transaction_is_listed_on_transactions_page(client):
    product = make_product(client, quantity_on_hand=5)
    response = client.post(
        "/ui/transactions",
        data={"product_id": str(product["id"]), "type": "IN", "quantity": "42"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "<td>IN</td>" in html
    assert "<td>42</td>" in html
    assert "<td>-</td>" in html  # no supplier given, page shows a dash


# -_-_-_-_-_-_-_-_-_-_-_-_- supplier API not-found paths (suppliers.py lines 35, 46)

def test_update_missing_supplier_returns_404_and_changes_nothing(client):
    supplier = make_supplier(client)
    response = client.put("/suppliers/999", json={"name": "Ghost Supply"})
    assert response.status_code == 404
    assert response.get_json() == {"error": "Supplier not found"}
    unchanged = client.get(f"/suppliers/{supplier['id']}").get_json()
    assert unchanged["name"] == "Acme Tools"


def test_delete_missing_supplier_returns_404_and_keeps_existing(client):
    make_supplier(client)
    response = client.delete("/suppliers/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Supplier not found"}
    assert len(client.get("/suppliers").get_json()) == 1


# -_-_-_-_-_-_-_-_-_-_-_-_- purchase order API not-found paths (purchase_orders.py lines 22, 25, 51)

def test_create_purchase_order_for_missing_supplier_is_rejected(client):
    product = make_product(client)
    response = client.post(
        "/purchase-orders",
        json={"supplier_id": 999, "product_id": product["id"], "quantity_ordered": 10},
    )
    assert response.status_code == 404
    assert response.get_json() == {"error": "Supplier not found"}
    assert client.get("/purchase-orders").get_json() == []


def test_create_purchase_order_for_missing_product_is_rejected(client):
    supplier = make_supplier(client)
    response = client.post(
        "/purchase-orders",
        json={"supplier_id": supplier["id"], "product_id": 999, "quantity_ordered": 10},
    )
    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}
    assert client.get("/purchase-orders").get_json() == []


def test_receive_missing_purchase_order_returns_404_and_leaves_stock(client):
    product = make_product(client, quantity_on_hand=5)
    response = client.put("/purchase-orders/999/receive")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Purchase order not found"}
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 5
    assert client.get("/transactions").get_json() == []


# -_-_-_-_-_-_-_-_-_-_-_-_- part 2: low-stock notification (failure + non-trigger paths)
#
# send_notification is patched where the app uses it (app.routes.adjustments),
# so no real notification is ever recorded by these tests.

SEND = "app.routes.adjustments.send_notification"


def test_failed_low_stock_alert_still_saves_adjustment(client, monkeypatch):
    """stub returns False: the stock correction must still go through and the
    response must report that the alert was not sent"""
    monkeypatch.setattr(SEND, lambda recipient, subject, message: False)  # stub
    product = make_product(client, quantity_on_hand=20, reorder_level=10)
    response = client.post(
        "/adjustments",
        json={"product_id": product["id"], "counted_quantity": 4, "staff_name": "Moshi"},
    )
    assert response.status_code == 201
    body = response.get_json()
    assert body["notification_sent"] is False
    assert body["previous_quantity"] == 20
    assert body["counted_quantity"] == 4
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 4
    assert len(client.get("/adjustments").get_json()) == 1


def test_no_alert_when_count_stays_just_above_reorder_level(client):
    """boundary: reorder level is 10 and the count lands on 11, so no alert"""
    product = make_product(client, quantity_on_hand=20, reorder_level=10)
    with patch(SEND) as mock_send:
        response = client.post(
            "/adjustments",
            json={"product_id": product["id"], "counted_quantity": 11, "staff_name": "Moshi"},
        )
    assert response.status_code == 201
    assert response.get_json()["notification_sent"] is None
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 11
    mock_send.assert_not_called()


def test_no_repeat_alert_when_product_was_already_low(client):
    """stock was already at the reorder level before the count, so it did not
    cross the threshold and no second alert goes out"""
    product = make_product(client, quantity_on_hand=10, reorder_level=10)
    with patch(SEND) as mock_send:
        response = client.post(
            "/adjustments",
            json={"product_id": product["id"], "counted_quantity": 3, "staff_name": "Moshi"},
        )
    assert response.status_code == 201
    assert response.get_json()["notification_sent"] is None
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 3
    mock_send.assert_not_called()


def test_no_alert_when_adjustment_is_rejected(client):
    """a low count with no staff name is rejected, so stock is unchanged and
    nobody is alerted about a correction that never happened"""
    product = make_product(client, quantity_on_hand=20, reorder_level=10)
    with patch(SEND) as mock_send:
        response = client.post(
            "/adjustments",
            json={"product_id": product["id"], "counted_quantity": 2, "staff_name": "  "},
        )
    assert response.status_code == 400
    assert response.get_json() == {"error": "staff_name is required"}
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 20
    assert client.get("/adjustments").get_json() == []
    mock_send.assert_not_called()
