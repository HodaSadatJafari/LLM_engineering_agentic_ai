import json
from datetime import datetime
from pathlib import Path

ORDERS_FILE = Path("data/orders.json")


class CheckoutService:
    """
    Handle order creation and persistence
    """

    def __init__(self):
        ORDERS_FILE.parent.mkdir(exist_ok=True)

    # -------------------------------------------------------------------------
    # Order creation
    # -------------------------------------------------------------------------
    def create_order(self, cart, customer_info: dict | None = None) -> dict:
        if cart.is_empty():
            raise ValueError("سبد خرید خالی است")

        order = {
            "order_id": self._generate_order_id(),
            "created_at": datetime.utcnow().isoformat(),
            "items": cart.items,
            "total_price": cart.total_price(),
            "customer": customer_info or {},
            "status": "created"
        }

        self._save_order(order)
        return order

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------
    def _generate_order_id(self) -> str:
        return f"ORD-{int(datetime.utcnow().timestamp())}"

    def _save_order(self, order: dict):
        try:
            orders = json.loads(ORDERS_FILE.read_text(encoding="utf-8"))
        except:
            orders = []

        orders.append(order)

        ORDERS_FILE.write_text(
            json.dumps(orders, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
