from state import BotState
from intent import detect_intent
from rag import search_products, search_faq
from cart import Cart
from checkout import CheckoutService
from analytics import log_event
from config import llm_client, MODEL_NAME


def is_confirm_message(msg: str) -> bool:
    confirms = [
        "بله", "آره", "میخام بخرم", "میخوام بخرم",
        "می‌خرم", "بخر", "ادامه خرید", "خرید ادامه بدیم",
        "اوکی", "ok", "yes", "مورد یک", "1"
    ]
    msg = msg.strip().lower()
    return any(c in msg for c in confirms)


class ShopBotAgent:
    """
    Full-featured ShopBot Agent (Single-product, state-based, OOP)
    """

    def __init__(self):
        self.state = BotState.START
        self.cart = Cart()
        self.checkout_service = CheckoutService()
        self.current_product = None
        self.user_info = {}

    # ------------------------------------------------------------------
    # LLM helper
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Main interface
    # ------------------------------------------------------------------
    def respond(self, user_message: str) -> str:
        log_event("user_message", user_message)
        intent = detect_intent(user_message)
        log_event("intent", intent)

        # --------------------------------------------------------------
        # Greeting (ONLY once)
        # --------------------------------------------------------------
        if self.state == BotState.START:
            self.state = BotState.IDLE
            return "سلام 👋 به ShopBot خوش اومدی. چی می‌خوای بخری؟"

        # --------------------------------------------------------------
        # Exit
        # --------------------------------------------------------------
        if intent == "exit":
            self.state = BotState.END
            return "خداحافظ 👋 امیدوارم دوباره ببینمت"

        # --------------------------------------------------------------
        # Confirm buy (single product, no ambiguity)
        # --------------------------------------------------------------
        if self.state == BotState.CONFIRM_BUY and is_confirm_message(user_message):
            if not self.current_product:
                return "مشخص نیست چه محصولی مد نظرته 🤔"

            product = self.current_product
            self.cart.add_item(
                name=product["name"],
                price=product["price"],
                quantity=1
            )

            log_event("add_to_cart", product["name"])
            self.current_product = None
            self.state = BotState.IDLE

            return f"✅ {product['name']} به سبد خرید اضافه شد. ادامه خرید یا تسویه؟"

        # --------------------------------------------------------------
        # Product search (single-product assumption)
        # --------------------------------------------------------------
        if intent == "search_product":
            products = search_products(user_message, k=1)

            if not products:
                return "محصولی پیدا نشد 😕"

            product = products[0]
            self.current_product = product
            self.state = BotState.CONFIRM_BUY

            return (
                f"🔹 {product['name']} با قیمت {product['price']} تومان موجود است.\n"
                "آیا مایل به خرید آن هستید؟"
            )

        # --------------------------------------------------------------
        # View cart
        # --------------------------------------------------------------
        if intent == "view_cart":
            return self.cart.summary()

        # --------------------------------------------------------------
        # Start checkout (collect user info)
        # --------------------------------------------------------------
        if intent == "checkout":
            if self.cart.is_empty():
                return "🛒 سبد خرید خالی است"

            self.state = BotState.GET_NAME
            return "🧑 لطفاً نام و نام خانوادگی خود را وارد کنید:"

        # --------------------------------------------------------------
        # Get name
        # --------------------------------------------------------------
        if self.state == BotState.GET_NAME:
            self.user_info["name"] = user_message.strip()
            self.state = BotState.GET_PHONE
            return "📞 لطفاً شماره تماس خود را وارد کنید:"

        # --------------------------------------------------------------
        # Get phone
        # --------------------------------------------------------------
        if self.state == BotState.GET_PHONE:
            phone = user_message.strip()
            if not phone.isdigit():
                return "❌ شماره تماس نامعتبر است. لطفاً فقط عدد وارد کنید."

            self.user_info["phone"] = phone
            self.state = BotState.GET_ADDRESS
            return "📍 لطفاً آدرس خود را وارد کنید:"

        # --------------------------------------------------------------
        # Get address & finalize order
        # --------------------------------------------------------------
        if self.state == BotState.GET_ADDRESS:
            self.user_info["address"] = user_message.strip()

            order = self.checkout_service.create_order(
                cart=self.cart,
                customer_info=self.user_info
            )

            self.cart.clear()
            self.user_info = {}
            self.state = BotState.IDLE

            log_event("checkout", order["order_id"])

            return (
                "✅ سفارش شما ثبت شد!\n\n"
                f"🧾 کد سفارش: {order['order_id']}\n"
                f"💰 مبلغ: {order['total_price']} تومان"
            )

        # --------------------------------------------------------------
        # FAQ
        # --------------------------------------------------------------
        if intent == "faq":
            answer = search_faq(user_message)
            return answer or "جواب این سوال رو ندارم 🤔"

        # --------------------------------------------------------------
        # Fallback
        # --------------------------------------------------------------
        return self._llm_response(
            system_prompt="You are a helpful Persian assistant.",
            user_prompt=user_message
        )
