import gradio as gr
import json
from datetime import datetime
from products import products
import os
from dotenv import load_dotenv
from openai import OpenAI

# --- تنظیمات OpenAI ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ORDERS_FILE = "orders.json"

# --- ذخیره سفارش ---
def save_order(name, phone, product_name):
    if not name or not phone or not product_name:
        return "❌ اطلاعات سفارش ناقص است."

    order = {
        "customer_name": name,
        "phone": phone,
        "product": product_name,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        with open(ORDERS_FILE, "r", encoding="utf-8") as f:
            orders = json.load(f)
    except:
        orders = []

    orders.append(order)

    with open(ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

    return "✅ سفارش شما ثبت شد."

# --- نمایش محصولات ---
def format_products(product_list):
    text = ""
    for p in product_list:
        text += f"{p['name']} | قیمت: {p['price']:,} تومان\n{p['description']}\n{'-'*30}\n"
    return text

product_names = [p["name"] for p in products]

# --- حافظه موقت AI ---
user_state = {"name": None, "phone": None, "product": None}

# --- منطق AI ---
def ai_chat(user_message, chat_history):
    global user_state

    chat_history = chat_history or []

    buy_keywords = ["خرید", "سفارش", "میخوام", "ثبت کن", "می‌خوام", "میخواهم"]
    wants_to_buy = any(k in user_message for k in buy_keywords)

    # پیام کاربر را اضافه کن
    chat_history.append({"role": "user", "content": user_message})

    # --- مسیر خرید ---
    if wants_to_buy and not user_state["product"]:
        reply = "خیلی هم عالی 😊 لطفاً نام دقیق محصول موردنظر را بفرست."
    elif user_message in product_names:
        user_state["product"] = user_message
        reply = "نام شما را بفرست."
    elif user_state["product"] and not user_state["name"]:
        user_state["name"] = user_message
        reply = "شماره تماس را بفرست."
    elif user_state["name"] and not user_state["phone"]:
        user_state["phone"] = user_message
        reply = save_order(user_state["name"], user_state["phone"], user_state["product"])
        user_state = {"name": None, "phone": None, "product": None}
    else:
        # پاسخ عادی AI با gpt-4o-mini
        system_prompt = f"تو یک فروشنده موبایل هستی. محصولات موجود:\n{format_products(products)}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        reply = response.choices[0].message.content

    chat_history.append({"role": "assistant", "content": reply})
    return chat_history

# --- رابط Gradio ---
with gr.Blocks(title="فروشگاه موبایل هوشمند") as app:
    gr.Markdown("## 📱 فروشگاه موبایل با هوش مصنوعی")

    # --- بخش جستجوی محصول ---
    search_box = gr.Textbox(label="جستجوی محصول")
    product_output = gr.Textbox(label="لیست محصولات", lines=15)

    def search_product(query):
        if not query:
            return format_products(products)
        result = [p for p in products if query.lower() in p["name"].lower()]
        return format_products(result) if result else "❌ محصولی یافت نشد"

    search_box.change(search_product, inputs=search_box, outputs=product_output)
    app.load(lambda: format_products(products), outputs=product_output)

    gr.Markdown("---")
    gr.Markdown("## 📝 ثبت سفارش مستقیم")

    order_name = gr.Textbox(label="نام مشتری")
    order_phone = gr.Textbox(label="شماره تماس")

# --- اینجا Dropdown به جای Textbox ---
    order_product = gr.Dropdown(
        label="انتخاب محصول",
        choices=[p["name"] for p in products]
    )

    order_button = gr.Button("ثبت سفارش")
    order_result = gr.Textbox(label="نتیجه سفارش", lines=2)

    order_button.click(
        save_order,
        inputs=[order_name, order_phone, order_product],
        outputs=order_result
    )


    gr.Markdown("---")
    gr.Markdown("## 🤖 چت با فروشنده")

    chatbot = gr.Chatbot(label="چت با فروشنده")
    user_input = gr.Textbox(label="پیام شما")
    send_btn = gr.Button("ارسال")

    send_btn.click(ai_chat, inputs=[user_input, chatbot], outputs=chatbot)

app.launch()
