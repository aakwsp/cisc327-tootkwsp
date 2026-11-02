from flask import Blueprint, jsonify, request

from app import store
from app.models.stock_adjustment import StockAdjustment

adjustments_bp = Blueprint("adjustments", __name__, url_prefix="/adjustments")


@adjustments_bp.route("", methods=["GET"])
def list_adjustments():
    results = list(store.adjustments.values())
    product_id = request.args.get("product_id", type=int)
    if product_id is not None:
        results = [a for a in results if a.product_id == product_id]
    return jsonify([a.to_dict() for a in results])


@adjustments_bp.route("", methods=["POST"])
def create_adjustment():
    """record stock count correction for product + update product quantity_on_hand"""
    data = request.get_json(silent=True) or {}

    product = store.products.get(data.get("product_id"))
    if product is None:
        return jsonify({"error": "Product not found"}), 404

    counted = data.get("counted_quantity")
    if not isinstance(counted, int) or isinstance(counted, bool) or counted < 0:
        return jsonify({"error": "counted_quantity must be a whole number of 0 or more"}), 400

    staff_name = (data.get("staff_name") or "").strip()
    if not staff_name:
        return jsonify({"error": "staff_name is required"}), 400

    adjustment_id = store.next_id("adjustment")
    adjustment = StockAdjustment(
        id=adjustment_id,
        product_id=product.id,
        previous_quantity=product.quantity_on_hand,
        counted_quantity=counted,
        staff_name=staff_name,
        reason=data.get("reason", ""),
    )
    product.quantity_on_hand = counted
    store.adjustments[adjustment_id] = adjustment
    return jsonify(adjustment.to_dict()), 201