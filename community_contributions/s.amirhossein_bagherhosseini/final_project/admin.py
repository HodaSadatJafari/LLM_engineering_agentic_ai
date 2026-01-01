import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data")
PRODUCTS_FILE = DATA_DIR / "products.json"
ORDERS_FILE = DATA_DIR / "orders.json"


class AdminService:
    """
    Business logic for Admin Panel
    """

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------
    def list_products(self) -> list:
        return self._read_json(PRODUCTS_FILE)

    def add_product(self, product: dict):
        products = self._read_json(PRODUCTS_FILE)
        product["created_at"] = datetime.utcnow().isoformat()
        products.append(product)
        self._write_json(PRODUCTS_FILE, products)

    def update_product(self, name: str, updated_fields: dict):
        products = self._read_json(PRODUCTS_FILE)
        for p in products:
            if p["name"] == name:
                p.update(updated_fields)
                p["updated_at"] = datetime.utcnow().isoformat()
                break
        self._write_json(PRODUCTS_FILE, products)

    def delete_product(self, name: str):
        products = self._read_json(PRODUCTS_FILE)
        products = [p for p in products if p["name"] != name]
        self._write_json(PRODUCTS_FILE, products)

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------
    def list_orders(self) -> list:
        return self._read_json(ORDERS_FILE)

    def update_order_status(self, order_id: str, status: str):
        orders = self._read_json(ORDERS_FILE)
        for o in orders:
            if o["order_id"] == order_id:
                o["status"] = status
                o["updated_at"] = datetime.utcnow().isoformat()
                break
        self._write_json(ORDERS_FILE, orders)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _read_json(self, path: Path) -> list:
        if not path.exists():
            return []
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: list):
        path.parent.mkdir(exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
