import json
from collections import Counter
from pathlib import Path
import gradio as gr

ANALYTICS_FILE = Path("data/analytics.json")


def load_logs():
    if not ANALYTICS_FILE.exists():
        return []
    with open(ANALYTICS_FILE, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------
# Analytics views
# ---------------------------------------------------------------------
def show_recent_events(limit=20):
    logs = load_logs()
    logs = logs[-limit:][::-1]

    if not logs:
        return "هیچ رویدادی ثبت نشده"

    return "\n\n".join(
        f"🕒 {l['timestamp']}\n🔹 {l['event_type']}\n📄 {l['data']}"
        for l in logs
    )


def intent_stats():
    logs = load_logs()
    intents = [l["data"] for l in logs if l["event_type"] == "intent"]

    if not intents:
        return "دیتایی برای intent وجود ندارد"

    counter = Counter(intents)
    return "\n".join(
        f"{intent}: {count}"
        for intent, count in counter.most_common()
    )


def event_stats():
    logs = load_logs()
    events = [l["event_type"] for l in logs]

    if not events:
        return "دیتایی وجود ندارد"

    counter = Counter(events)
    return "\n".join(
        f"{event}: {count}"
        for event, count in counter.most_common()
    )


# ---------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------
def launch_analytics_dashboard():
    with gr.Blocks(css="body { direction: rtl; font-family: Vazirmatn; }") as demo:
        gr.Markdown("## 📊 داشبورد آنالیتیکس ShopBot")

        with gr.Tab("🕒 رویدادهای اخیر"):
            recent_box = gr.Textbox(lines=15, label="آخرین رویدادها")
            refresh_recent = gr.Button("🔄 بروزرسانی")
            refresh_recent.click(show_recent_events, outputs=recent_box)

        with gr.Tab("🧠 آمار Intent"):
            intent_box = gr.Textbox(lines=10, label="Intent ها")
            refresh_intent = gr.Button("🔄 بروزرسانی")
            refresh_intent.click(intent_stats, outputs=intent_box)

        with gr.Tab("📈 آمار رویدادها"):
            event_box = gr.Textbox(lines=10, label="Event ها")
            refresh_event = gr.Button("🔄 بروزرسانی")
            refresh_event.click(event_stats, outputs=event_box)

    demo.launch()


if __name__ == "__main__":
    launch_analytics_dashboard()