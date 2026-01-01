from state import BotState
from intent import detect_intent
from rag import search_products, search_faq
from cart import Cart
from checkout import CheckoutService
from analytics import log_event
from config import llm_client, MODEL_NAME


class ShopBotAgent:
    """
    Full-featured ShopBot Agent
    """

    def __init__(self):
        self.state = BotState.START
        self.cart = Cart()
        self.checkout_service = CheckoutService()

    # ---------------------------------------------------------------------
    # LLM helper
    # ---------------------------------------------------------------------
    def _llm_response(self, system_prompt: str, user_prompt: str) -> str:
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    # ---------------------------------------------------------------------
    # Main interface
    # ---------------------------------------------------------------------
    
    def respond(self, user_message: str) -> str:
        print("USER:", user_message)
        products = search_products(user_message)
        print("FOUND PRODUCTS:", products)

        log_event("user_message", user_message)

        intent = detect_intent(user_message)
        log_event("intent", intent)

        # -----------------------------------------------------------------
        # Greeting
        # -----------------------------------------------------------------
        if intent == "greet" or self.state == BotState.START:
            self.state = BotState.IDLE
            return "سلام 👋 به ShopBot خوش اومدی. چی می‌خوای بخری؟"

        # -----------------------------------------------------------------
        # Exit
        # -----------------------------------------------------------------
        if intent == "exit":
            self.state = BotState.END
            return "خداحافظ 👋 امیدوارم دوباره ببینمت"

        # -----------------------------------------------------------------
        # Product search (FAISS)
        # -----------------------------------------------------------------
        if intent == "search_product":
            self.state = BotState.PRODUCT_SEARCH
            products = search_products(user_message)

            if not products:
                return "محصولی پیدا نشد 😕"

            context = "\n".join(
                f"{i+1}. {p['name']} | {p['price']} تومان"
                for i, p in enumerate(products)
            )

            return self._llm_response(
                system_prompt=(
                    "You are a Persian shopping assistant. "
                    "Only use the provided products. "
                    "Do not invent products."
                ),
                user_prompt=f"""
محصولات زیر پیدا شده‌اند:
{context}

پیام کاربر:
{user_message}

به کاربر کمک کن یکی رو انتخاب کنه.
"""
            )

        # -----------------------------------------------------------------
        # Add to cart
        # -----------------------------------------------------------------
        if intent == "add_to_cart":
            products = search_products(user_message, k=1)

            if not products:
                return "مشخص نیست کدوم محصول رو می‌خوای اضافه کنی 🤔"

            product = products[0]
            self.cart.add_item(
                name=product["name"],
                price=product["price"],
                quantity=1
            )

            self.state = BotState.ADD_TO_CART
            log_event("add_to_cart", product["name"])

            return f"✅ {product['name']} به سبد خرید اضافه شد"

        # -----------------------------------------------------------------
        # View cart
        # -----------------------------------------------------------------
        if intent == "view_cart":
            return self.cart.summary()

        # -----------------------------------------------------------------
        # Checkout
        # -----------------------------------------------------------------
        if intent == "checkout":
            if self.cart.is_empty():
                return "🛒 سبد خرید خالی است"

            order = self.checkout_service.create_order(self.cart)
            self.cart.clear()
            self.state = BotState.CHECKOUT

            log_event("checkout", order["order_id"])

            return (
                "✅ سفارش شما ثبت شد!\n\n"
                f"🧾 کد سفارش: {order['order_id']}\n"
                f"💰 مبلغ: {order['total_price']} تومان"
            )

        # -----------------------------------------------------------------
        # FAQ
        # -----------------------------------------------------------------
        if intent == "faq":
            answer = search_faq(user_message)
            return answer or "جواب این سوال رو ندارم 🤔"

        # -----------------------------------------------------------------
        # Fallback
        # -----------------------------------------------------------------
        return self._llm_response(
            system_prompt="You are a helpful Persian assistant.",
            user_prompt=user_message
        )
