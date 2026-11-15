from unittest.mock import patch

def _create_product(client, quantity=12, reorder_level=5):
    response = client.post(
        "/products",
        json={
            "name": "Hammer",
            "sku": "HAM-001",
            "unit_price": 10.0,
            "quantity_on_hand": quantity,
            "reorder_level": reorder_level,
        },
    )
    assert response.status_code == 201
    return response.get_json()

def test_stock_adjustment_reports_successful_notification_with_stub(client, monkeypatch):
    product = _create_product(client, quantity=12, reorder_level=5)
    monkeypatch.setattr(
        "app.routes.adjustments.send_notification",
        lambda recipient, subject, message: True,
    )

    response = client.post(
        "/adjustments",
        json={"product_id": product["id"], "counted_quantity": 3,
              "staff_name": "Tim", "reason": "Physical count"},
    )

    assert response.status_code == 201
    adjustment = response.get_json()
    assert adjustment["notification_sent"] is True
    assert adjustment["previous_quantity"] == 12
    assert adjustment["counted_quantity"] == 3
    assert adjustment["difference"] == -9
    assert client.get(f"/products/{product['id']}/stock-level").get_json()["quantity_on_hand"] == 3
    assert client.get("/adjustments").get_json()[0]["id"] == adjustment["id"]

def test_stock_adjustment_calls_notification_with_expected_details(client):
    product = _create_product(client, quantity=12, reorder_level=5)

    with patch("app.routes.adjustments.send_notification", return_value=True) as mock_send:
        response = client.post(
            "/adjustments",
            json={"product_id": product["id"], "counted_quantity": 5,
                  "staff_name": "Tim"},
        )

    assert response.status_code == 201
    assert response.get_json()["notification_sent"] is True
    assert client.get(f"/products/{product['id']}").get_json()["quantity_on_hand"] == 5
    assert len(client.get("/adjustments").get_json()) == 1
    mock_send.assert_called_once_with(
        "Inventory / Operations Manager",
        "Low stock alert: Hammer",
        "Hammer (SKU HAM-001) has 5 units remaining; reorder level is 5.",
    )
