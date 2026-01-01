import gradio as gr
from admin import AdminService
from rag import build_and_save_indexes

admin_service = AdminService()

# ---------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------
def list_products():
    products = admin_service.list_products()
    if not products:
        return "هیچ محصولی وجود ندارد"
    return "\n".join(
        f"- {p['name']} | {p['price']} تومان | موجودی: {p.get('stock', '-')}"
        for p in products
    )

def add_product(name, description, price, stock, category):
    product = {
        "name": name,
        "description": description,
        "price": int(price),
        "stock": int(stock),
        "category": category
    }
    admin_service.add_product(product)
    build_and_save_indexes()  # rebuild FAISS
    return "✅ محصول اضافه شد و ایندکس FAISS بروزرسانی شد"

# ---------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------
def list_orders():
    orders = admin_service.list_orders()
    if not orders:
        return "سفارشی ثبت نشده"
    return "\n\n".join(
        f"🧾 {o['order_id']} | {o['status']} | {o['total_price']} تومان"
        for o in orders
    )

def update_order(order_id, status):
    admin_service.update_order_status(order_id, status)
    return "✅ وضعیت سفارش بروزرسانی شد"

# ---------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------
def launch_admin_ui():
    with gr.Blocks(css="body { direction: rtl; font-family: Vazirmatn; }") as demo:
        gr.Markdown("## 🔐 پنل مدیریت ShopBot")

        with gr.Tab("📦 محصولات"):
            product_list = gr.Textbox(label="لیست محصولات", lines=8)
            refresh_products = gr.Button("🔄 بروزرسانی لیست")

            refresh_products.click(
                list_products,
                outputs=product_list
            )

            gr.Markdown("### ➕ افزودن محصول جدید")
            name = gr.Textbox(label="نام محصول")
            description = gr.Textbox(label="توضیح")
            price = gr.Number(label="قیمت")
            stock = gr.Number(label="موجودی")
            category = gr.Textbox(label="دسته‌بندی")
            add_btn = gr.Button("افزودن محصول")

            add_btn.click(
                add_product,
                inputs=[name, description, price, stock, category],
                outputs=product_list
            )

        with gr.Tab("🧾 سفارش‌ها"):
            orders_box = gr.Textbox(label="لیست سفارش‌ها", lines=10)
            refresh_orders = gr.Button("🔄 بروزرسانی سفارش‌ها")

            refresh_orders.click(
                list_orders,
                outputs=orders_box
            )

            gr.Markdown("### ✏️ تغییر وضعیت سفارش")
            order_id = gr.Textbox(label="کد سفارش")
            status = gr.Dropdown(
                ["created", "paid", "shipped", "delivered", "cancelled"],
                label="وضعیت جدید"
            )
            update_btn = gr.Button("بروزرسانی وضعیت")

            update_btn.click(
                update_order,
                inputs=[order_id, status],
                outputs=orders_box
            )

    demo.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        inbrowser=True
    )

# 🔥 خیلی مهم: این قسمت باید باشد
if __name__ == "__main__":
    launch_admin_ui()
