# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_
# test_a4_moshi.py
#
# CISC327 A4 browser E2E tests (Playwright)
#
# needs the app running first (locally or in docker) on port 5000:
#   python run.py            or   docker run --rm -p 5000:5000 cisc327-a4
# then:
#   python -m pytest tests/e2e -v --headed
#
# each test makes its own data with a unique name, so it doesn't depend
# on other tests or whatever is already in the in-memory store
# -_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_

import os
import uuid

from playwright.sync_api import Page, expect

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")


def unique(prefix):
    """short unique name so reruns never clash with old data"""
    return f"{prefix}-{uuid.uuid4().hex[:6]}"


def add_product(page: Page, name, sku, price="12.50", qty="5"):
    """fills in the add product form and submits it"""
    page.goto(f"{BASE_URL}/ui/products")
    page.fill("input[name=name]", name)
    page.fill("input[name=sku]", sku)
    page.fill("input[name=unit_price]", price)
    page.fill("input[name=quantity_on_hand]", qty)
    page.click("button:has-text('Add Product')")


# -_-_-_-_-_-_-_-_-_-_-_-_- success: add then delete a product

def test_add_and_delete_product_through_ui(page: Page):
    name = unique("Hammer")
    sku = unique("HAM")

    add_product(page, name, sku, price="12.50", qty="5")

    # back on the products page, the new product is listed with what we typed
    expect(page).to_have_url(f"{BASE_URL}/ui/products")
    row = page.locator("tr", has_text=name)
    expect(row).to_have_count(1)
    expect(row).to_contain_text(sku)
    expect(row).to_contain_text("12.5")
    expect(row.locator("td").nth(4)).to_have_text("5")

    # delete it from the same row, and it is gone from the table
    row.locator("button:has-text('Delete')").click()
    expect(page).to_have_url(f"{BASE_URL}/ui/products")
    expect(page.locator("tr", has_text=name)).to_have_count(0)


# -_-_-_-_-_-_-_-_-_-_-_-_- boundary: quantity 0 is not a valid stock movement

def test_stock_movement_with_zero_quantity_is_blocked(page: Page):
    name = unique("Saw")
    add_product(page, name, unique("SAW"), qty="5")
    product_id = page.locator("tr", has_text=name).locator("td").first.inner_text()

    page.goto(f"{BASE_URL}/ui/transactions")
    rows_before = page.locator("table tr").count()

    page.fill("input[name=product_id]", product_id)
    page.select_option("select[name=type]", "OUT")
    page.fill("input[name=quantity]", "0")
    page.click("button:has-text('Record')")

    # the form's min=1 rule stops the submit: the browser flags the field
    quantity = page.locator("input[name=quantity]")
    assert quantity.evaluate("el => el.validity.rangeUnderflow") is True
    assert quantity.evaluate("el => el.validationMessage") != ""

    # nothing was recorded and the stock did not change
    expect(page.locator("table tr")).to_have_count(rows_before)
    page.goto(f"{BASE_URL}/ui/products")
    row = page.locator("tr", has_text=name)
    expect(row.locator("td").nth(4)).to_have_text("5")
