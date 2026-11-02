from datetime import date


class PurchaseOrder:
    def __init__(
        self,
        id,
        supplier_id,
        product_id,
        quantity_ordered,
        status="pending",
        created_date=None,
        received_date=None,
        quantity_received=None,
    ):
        self.id = id
        self.supplier_id = supplier_id
        self.product_id = product_id
        self.quantity_ordered = quantity_ordered
        self.status = status  # "pending" or "received"
        self.created_date = created_date or date.today()
        self.received_date = received_date
        self.quantity_received = quantity_received

    def to_dict(self):
        return {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "product_id": self.product_id,
            "quantity_ordered": self.quantity_ordered,
            "quantity_received": self.quantity_received,
            "status": self.status,
            "created_date": self.created_date.isoformat(),
            "received_date": self.received_date.isoformat() if self.received_date else None,
        }
