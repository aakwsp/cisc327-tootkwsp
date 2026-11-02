from datetime import date

from flask import Blueprint, jsonify, request

from app import store
from app.models.purchase_order import PurchaseOrder
from app.models.transaction import Transaction

purchase_orders_bp = Blueprint("purchase_orders", __name__, url_prefix="/purchase-orders")


@purchase_orders_bp.route("", methods=["GET"])
def list_purchase_orders():
    return jsonify([po.to_dict() for po in store.purchase_orders.values()])


@purchase_orders_bp.route("", methods=["POST"])
def create_purchase_order():
    data = request.get_json()
    supplier = store.suppliers.get(data["supplier_id"])
    if supplier is None:
        return jsonify({"error": "Supplier not found"}), 404
    product = store.products.get(data["product_id"])
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    po_id = store.next_id("purchase_order")
    po = PurchaseOrder(
        id=po_id,
        supplier_id=data["supplier_id"],
        product_id=data["product_id"],
        quantity_ordered=data["quantity_ordered"],
        status="pending",
    )
    store.purchase_orders[po_id] = po
    return jsonify(po.to_dict()), 201


@purchase_orders_bp.route("/<int:po_id>", methods=["GET"])
def get_purchase_order(po_id):
    po = store.purchase_orders.get(po_id)
    if po is None:
        return jsonify({"error": "Purchase order not found"}), 404
    return jsonify(po.to_dict())


@purchase_orders_bp.route("/<int:po_id>/receive", methods=["PUT"])
def receive_purchase_order(po_id):
    po = store.purchase_orders.get(po_id)
    if po is None:
        return jsonify({"error": "Purchase order not found"}), 404

    if po.status == "received":
        return jsonify({"error": "Purchase order already received"}), 400

    data = request.get_json(silent=True) or {}

    quantity_received = data.get(
        "quantity_received",
        po.quantity_ordered,
    )

    if not isinstance(quantity_received, int) or quantity_received <= 0:
        return jsonify({
            "error": "quantity_received must be a positive integer"
        }), 400

    po.status = "received"
    po.received_date = date.today()
    po.quantity_received = quantity_received

    product = store.products[po.product_id]
    product.quantity_on_hand += quantity_received

    transaction_id = store.next_id("transaction")
    transaction = Transaction(
        id=transaction_id,
        product_id=po.product_id,
        supplier_id=po.supplier_id,
        type="IN",
        quantity=quantity_received,
    )
    store.transactions[transaction_id] = transaction

    return jsonify(po.to_dict())
