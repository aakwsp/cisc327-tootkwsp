from datetime import datetime


class StockAdjustment:
    """Stock Count Correction"""

    def __init__(self, id, product_id, previous_quantity, counted_quantity, staff_name, reason="", created_at=None):
        self.id = id
        self.product_id = product_id
        self.previous_quantity = previous_quantity
        self.counted_quantity = counted_quantity
        self.staff_name = staff_name
        self.reason = reason
        self.created_at = created_at or datetime.now()

    @property
    def difference(self):
        return self.counted_quantity - self.previous_quantity

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "previous_quantity": self.previous_quantity,
            "counted_quantity": self.counted_quantity,
            "difference": self.difference,
            "staff_name": self.staff_name,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(timespec="seconds"),
        }