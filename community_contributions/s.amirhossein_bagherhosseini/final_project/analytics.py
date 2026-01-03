import json
from datetime import datetime
from pathlib import Path

ANALYTICS_FILE = Path("data/analytics.json")


def log_event(event_type: str, data):
    """
    Log analytics events to analytics.json

    event_type: str  (e.g. user_message, intent, add_to_cart, checkout)
    data: any        (string / dict)
    """

    ANALYTICS_FILE.parent.mkdir(exist_ok=True)

    try:
        with open(ANALYTICS_FILE, encoding="utf-8") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    logs.append({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data
    })

    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
