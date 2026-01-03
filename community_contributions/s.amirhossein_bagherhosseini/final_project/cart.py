class Cart:
    """
    Simple in-memory shopping cart
    """

    def __init__(self):
        self.items = []
        # هر آیتم:
        # {
        #   "name": str,
        #   "price": int,
        #   "quantity": int
        # }

    # -------------------------------------------------------------------------
    # Cart operations
    # -------------------------------------------------------------------------
    def add_item(self, name: str, price: int, quantity: int = 1):
        for item in self.items:
            if item["name"] == name:
                item["quantity"] += quantity
                return

        self.items.append({
            "name": name,
            "price": price,
            "quantity": quantity
        })

    def remove_item(self, name: str):
        self.items = [i for i in self.items if i["name"] != name]

    def clear(self):
        self.items = []

    # -------------------------------------------------------------------------
    # Calculations
    # -------------------------------------------------------------------------
    def total_price(self) -> int:
        return sum(item["price"] * item["quantity"] for item in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    # -------------------------------------------------------------------------
    # Display
    # -------------------------------------------------------------------------
    def summary(self) -> str:
        if self.is_empty():
            return "🛒 سبد خرید خالی است."

        lines = ["🛒 سبد خرید شما:"]
        for item in self.items:
            lines.append(
                f"- {item['name']} × {item['quantity']} "
                f"= {item['price'] * item['quantity']} تومان"
            )

        lines.append(f"\n💰 جمع کل: {self.total_price()} تومان")
        return "\n".join(lines)
