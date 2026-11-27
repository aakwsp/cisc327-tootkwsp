from uuid import uuid4

from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"


def test_create_product_success(page: Page):
    name = f"Test Product {uuid4().hex[:8]}"
    sku = f"SKU-{uuid4().hex[:8]}"

    page.goto(BASE_URL)
    page.get_by_role("link", name="Products", exact=True).click()

    page.get_by_label("Name", exact=True).fill(name)
    page.get_by_label("SKU").fill(sku)
    page.get_by_label("Unit Price").fill("19.99")
    page.get_by_label("Quantity on Hand").fill("10")

    page.get_by_role("button", name="Add Product").click()

    row = page.get_by_role("row").filter(has_text=sku)

    expect(row).to_have_count(1)
    expect(row.get_by_role("cell", name=name, exact=True)).to_be_visible()
    expect(row.get_by_role("cell", name="19.99", exact=True)).to_be_visible()
    expect(row.get_by_role("cell", name="10", exact=True)).to_be_visible()


def test_create_supplier_invalid_email(page: Page):
    name = f"Invalid Supplier {uuid4().hex[:8]}"

    page.goto(BASE_URL)
    page.get_by_role("link", name="Suppliers", exact=True).click()

    page.get_by_label("Name", exact=True).fill(name)

    email = page.get_by_label("Contact Email")
    email.fill("invalid-email")

    page.get_by_role("button", name="Add Supplier").click()

    assert email.evaluate("(el) => el.validity.typeMismatch")
    assert email.evaluate("(el) => el.validationMessage") != ""

    expect(
        page.get_by_role("row").filter(has_text=name)
    ).to_have_count(0)

    page.reload()

    expect(
        page.get_by_role("row").filter(has_text=name)
    ).to_have_count(0)
