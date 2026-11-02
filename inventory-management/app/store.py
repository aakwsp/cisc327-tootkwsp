"""In-memory data store.

Each "table" is just a dict mapping id -> object, kept in memory for the
lifetime of the running app. Data is lost when the app restarts. This keeps
the project approachable before students cover databases later in the
program, while still separating storage from the route/model code.
"""

products = {}
suppliers = {}
transactions = {}
purchase_orders = {}
adjustments = {}

_next_ids = {"product": 1, "supplier": 1, "transaction": 1, "purchase_order": 1, "adjustment": 1}

def next_id(kind):
    id_ = _next_ids[kind]
    _next_ids[kind] += 1
    return id_


def reset():
    """Clear all data. Handy for resetting state between tests."""
    products.clear()
    suppliers.clear()
    transactions.clear()
    purchase_orders.clear()
    adjustments.clear()
    _next_ids.update(product=1, supplier=1, transaction=1, purchase_order=1, adjustment=1)
