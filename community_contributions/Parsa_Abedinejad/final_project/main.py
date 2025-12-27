import gradio as gr
from agent import generate_travel_plan

def main():
    css = """
    body {
        direction: rtl;
        font-family: Vazirmatn, sans-serif;
        background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
    }

    .container {
        max-width: 900px;
        margin: auto;
    }

    .card {
        background: white;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    .output-box textarea {
        direction: ltr !important;
        text-align: left !important;
        font-family: monospace;
    }

    h1 {
        color: #2e7d32;
    }

    button {
        border-radius: 12px !important;
        font-size: 16px !important;
    }
    """

    with gr.Blocks(css=css) as demo:
        with gr.Column(elem_classes="container"):

            gr.Markdown("""
            <div style="text-align:center;">
                <h1>✈️ دستیار هوشمند برنامه‌ریزی سفر</h1>
                <p>
                    مقصد، بودجه و مدت سفر را وارد کنید تا یک برنامه سفر حرفه‌ای دریافت کنید
                </p>
            </div>
            """)

            # کارت ورودی
            with gr.Column(elem_classes="card"):
                gr.Markdown("### 🧭 اطلاعات سفر")

                destination = gr.Textbox(
                    label="مقصد سفر",
                    placeholder="مثال: شیراز"
                )

                budget = gr.Textbox(
                    label="بودجه تقریبی (تومان)",
                    placeholder="مثال: 10000000"
                )

                days = gr.Textbox(
                    label="تعداد روزهای سفر",
                    placeholder="مثال: 3"
                )

                submit_btn = gr.Button("✨ ساخت برنامه سفر", variant="primary")

            # کارت خروجی
            with gr.Column(elem_classes="card output-box"):
                gr.Markdown("### 📘 برنامه سفر پیشنهادی")
                output = gr.Textbox(
                    lines=18,
                    interactive=False,
                    show_copy_button=True
                )

            submit_btn.click(
                fn=generate_travel_plan,
                inputs=[destination, budget, days],
                outputs=output
            )

    demo.launch(share=True)

if __name__ == "__main__":
    main()
