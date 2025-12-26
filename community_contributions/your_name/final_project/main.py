from fastapi import FastAPI
from pydantic import BaseModel
import os, requests
from dotenv import load_dotenv
from scraping import scrape_train, scrape_bus, scrape_hotels

load_dotenv()
app = FastAPI(title="Travel AI زمینی")

class TravelRequest(BaseModel):
    مبدا: str
    مقصد: str
    روزها: int
    بودجه: int
    وسیله: str  # قطار، اتوبوس، ماشین
    علایق: str

def get_weather(city):
    key = os.getenv("WEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&lang=fa&units=metric"
    r = requests.get(url)
    data = r.json()
    return data.get("weather", [{}])[0].get("description", "نامشخص")

def ai_plan(req, transport, hotels, weather):
    headers = {
        "Authorization": f"Bearer {os.getenv('AVALAI_API_KEY')}",
        "Content-Type": "application/json"
    }

    mabda = req.مبدا
    maghsad = req.مقصد
    vasile = req.وسیله
    roozha = req.روزها
    boodje = req.بودجه
    alayegh = req.علایق

    prompt = f"""
یک برنامه سفر زمینی واقعی و اقتصادی به فارسی بنویس.

مبدا: {mabda}
مقصد: {maghsad}
وسیله: {vasile}
مدت: {roozha} روز
بودجه: {boodje} تومان
علایق: {alayegh}
وضعیت هوا: {weather}
زمان مسیر: {transport.get('time')}
قیمت مسیر: {transport.get('price')}
اقامت‌ها: {hotels}

برنامه روزبه‌روز باشد.
"""

    r = requests.post(
        "https://api.avalai.ir/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        },
        headers=headers,
        timeout=20
    )

    try:
        return r.json()["choices"][0]["message"]["content"]
    except Exception:
        return "❌ خطا در دریافت پاسخ از AI"

@app.post("/plan")
def plan(req: TravelRequest):
    if req.وسیله == "قطار":
        transport = scrape_train(req.مبدا, req.مقصد)
    elif req.وسیله == "اتوبوس":
        transport = scrape_bus(req.مبدا, req.مقصد)
    else:
        transport = {"time": "حدود 8 ساعت (جاده‌ای)", "price": "بستگی به مصرف بنزین"}

    weather = get_weather(req.مقصد)
    hotels = scrape_hotels(req.مقصد)
    plan_text = ai_plan(req, transport, hotels, weather)

    return {
        "مسیر": transport,
        "هوا": weather,
        "اقامت": hotels,
        "برنامه": plan_text
    }