import gradio as gr
from agent import ShopBotAgent

# -----------------------------------------------------------------------------
# Initialize Agent
# -----------------------------------------------------------------------------
agent = ShopBotAgent()

# -----------------------------------------------------------------------------
# Chat handler
# -----------------------------------------------------------------------------
def chat_handler(message, history):
    reply = agent.respond(message)
    history.append((message, reply))
    return history, ""

# -----------------------------------------------------------------------------
# Launch UI
# -----------------------------------------------------------------------------
import gradio as gr
from agent import ShopBotAgent

agent = ShopBotAgent()

# -----------------------------------------------------------------------------
# Chat handler (ChatInterface style)
# -----------------------------------------------------------------------------
def chat_handler(message, history):
    # history به‌صورت list of dict می‌آید
    reply = agent.respond(message)
    return reply

# -----------------------------------------------------------------------------
# Launch UI
# -----------------------------------------------------------------------------
import gradio as gr
from agent import ShopBotAgent

agent = ShopBotAgent()

# -----------------------------------------------------------------------------
# Chat handler (ChatInterface – Gradio 6.2)
# -----------------------------------------------------------------------------
def chat_handler(message, history):
    # history به صورت list of dict می‌آید، ولی اینجا لازم نیست
    reply = agent.respond(message)
    return reply

# -----------------------------------------------------------------------------
# Launch UI
# -----------------------------------------------------------------------------
def launch_ui():
    demo = gr.ChatInterface(
        fn=chat_handler,
        title="🛒 ShopBot – دستیار خرید هوشمند",
        description="یک دستیار خرید فارسی مبتنی بر هوش مصنوعی"
    )

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=True
    )
