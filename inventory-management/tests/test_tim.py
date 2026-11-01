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
