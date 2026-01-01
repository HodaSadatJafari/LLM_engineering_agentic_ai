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

    FAQ = auto()
    """
    پاسخ به سوالات متداول
    """

    ADD_TO_CART = auto()
    """
    اضافه کردن محصول به سبد خرید
    """

    CHECKOUT = auto()
    """
    ثبت سفارش و پرداخت
    """

    END = auto()
    """
    پایان مکالمه
    """
