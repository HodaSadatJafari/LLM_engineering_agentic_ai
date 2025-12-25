# intent.py
from typing import Tuple

ORDER_KEYWORDS = ["buy", "order", "purchase", "i want to buy", "place an order", "سفارش", "خرید"]
INFO_KEYWORDS = ["price", "cheapest", "available", "availability", "how many", "suitable", "describe", "cost"]

def detect_intent(text: str) -> Tuple[str, float]:
    t = text.lower()
    if any(k in t for k in ORDER_KEYWORDS):
        return ("order", 0.95)
    if any(k in t for k in INFO_KEYWORDS):
        return ("product_info", 0.8)
    return ("general", 0.5)
