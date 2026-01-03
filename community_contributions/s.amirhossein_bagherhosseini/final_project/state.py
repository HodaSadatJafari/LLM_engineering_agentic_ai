from enum import Enum, auto


class BotState(Enum):
    """
    State machine for ShopBot conversation flow
    """

    START = auto()
    """
    شروع مکالمه – اولین پیام کاربر
    """

    IDLE = auto()
    """
    حالت آماده به کار – منتظر درخواست کاربر
    """

    PRODUCT_SEARCH = auto()
    """
    جستجوی محصول (RAG + FAISS)
    """

    CONFIRM_BUY = auto()
    """
    تأیید خرید محصول – منتظر پاسخ‌هایی مثل «بله»، «می‌خرم»
    """

    ADD_TO_CART = auto()
    """
    اضافه کردن محصول به سبد خرید
    """

    GET_NAME = auto()
    """
    دریافت نام و نام خانوادگی مشتری
    """

    GET_PHONE = auto()
    """
    دریافت شماره تماس مشتری
    """

    GET_ADDRESS = auto()
    """
    دریافت آدرس مشتری
    """

    CHECKOUT = auto()
    """
    ثبت نهایی سفارش و پرداخت
    """

    FAQ = auto()
    """
    پاسخ به سوالات متداول
    """

    END = auto()
    """
    پایان مکالمه
    """
