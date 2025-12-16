import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # بارگذاری .env

class TravelAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("❌ OPENAI_API_KEY در فایل .env تنظیم نشده است")

        self.client = OpenAI(api_key=api_key)

    def create_plan(self, destination, budget, days):
        prompt = f"""
یک برنامه سفر حرفه‌ای به مقصد {destination} برای {days} روز
با بودجه حدود {budget} تومان بنویس.
شامل:
- اقامت
- برنامه روزانه
- غذا
- نکات مهم
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional travel planner."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content


def generate_travel_plan(destination, budget, days):
    agent = TravelAgent()
    return agent.create_plan(destination, budget, days)
