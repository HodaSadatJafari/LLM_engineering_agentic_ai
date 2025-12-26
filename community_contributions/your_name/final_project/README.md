🌍 Travel AI (Persian Land Travel Planner)
Travel AI is an intelligent, FastAPI-based service designed to generate realistic and budget-friendly land travel itineraries. It integrates real-time data scraping, weather forecasting, and Large Language Models (LLMs) to provide a seamless travel planning experience.
✨ Features

• 📊 Real-time Transport Data: Scrapes live data for trains and buses to provide accurate pricing and travel times.
• 🌦 Weather Integration: Fetches current weather conditions for the destination using the OpenWeatherMap API.
• 🏨 Accommodation Suggestions: Automatically lists available hotels in the target city.
• 🤖 AI-Powered Itineraries: Uses GPT-4o-mini (via AvalAI) to generate day-by-day plans customized to the user's budget, interests, and transport mode.
• 🇮🇷 Localization: Fully optimized for Persian language input/output and Iranian travel routes.
🛠 Tech Stack

• Framework: FastAPI (https://fastapi.tiangolo.com/)
• Language Models: GPT-4o-mini (AvalAI API)
• Data Validation: Pydantic
• APIs: OpenWeatherMap
• Libraries: Requests, Python-Dotenv, Scrapy/BeautifulSoup (for scraping)
🚀 Getting Started

1. Installation
Clone the repository and install the dependencies:
 git clone https://github.com/your-username/travel-ai.git
cd travel-ai
pip install fastapi uvicorn requests python-dotenv

2. Environment Variables
Create a .env file in the root directory and add your API keys:
WEATHER_API_KEY=your_openweathermap_key
AVALAI_API_KEY=your_avalai_api_key

3. Run the Server
Start the development server:
uvicorn main:app --reload

📖 API Usage
Once the server is running, visit http://127.0.0.1:8000/docs to access the interactive Swagger UI.
Endpoint: POST /plan
Sample Request Body:
{
  "مبدا": "Tehran",
  "مقصد": "Isfahan",
  "روزها": 3,
  "بودجه": 4000000,
  "وسیله": "قطار",
  "علایق": "Historical sites and local food"
}
Sample Response:
{
  "مسیر": {
    "time": "7 Hours",
    "price": "180,000 Tomans"
  },
  "هوا": "Clear sky",
  "اقامت": ["Abbasi Hotel", "Kowsar Hotel"],
  "برنامه": "Day 1: Arrive and visit Naqsh-e Jahan Square..."
}

🏗 Project Structure
├── main.py            # FastAPI application & AI logic
├── scraping.py        # Logic for scraping Train, Bus, and Hotel data
├── .env               # API Keys and sensitive configuration
└── requirements.txt   # Project dependencies
