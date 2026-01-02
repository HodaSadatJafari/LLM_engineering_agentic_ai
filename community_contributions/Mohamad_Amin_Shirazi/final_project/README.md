# AI-Powered Travel Assistant with Real-Time Data
This project is an AI-powered travel assistant that helps users plan trips using real-time data and LLM. The system combines multiple real-world APIs with an LLM to produce human-friendly travel recommendations.

# Agent's Capabilities
1) Suggest destinations based on user preferences and budget
2) Generate realistic multi-day travel itineraries
3) Provide real-time travel alerts such as weather conditions and flight status

# Language, UI and API-clients
1) Python
2) Jupyter Notebook
3) Gradio (UI)
4) OpenAI-compatible client (AvalAI)
5) API-clients:
    (You can get APIs in the following URL. If you couldn't or got a problem, tell me and I will send you my API keys.)
    1. OpenWeather (weather data)          https://home.openweathermap.org/api_keys
    2. Geoapify (places & attractions)     https://myprojects.geoapify.com/api
    3. Aviationstack (flight status)       https://aviationstack.com/dashboard
    4. AVAL-AI (client for LLM)            https://chat.avalai.ir/platform/api-keys

# How the agent works
1) User enters travel preferences and budget
2) The agent suggests suitable destinations using an LLM
3) User selects a destination
4) The agent fetches real-time weather data, retrieves real attractions and checks recent flight status
5) The LLM generates a personalized itinerary and explanations

# How to RUN the project
1) Create and activate a virtual environment
2) Install dependencies from "requirements.txt"
3) Create a ".env" file and add your API keys
4) Run the notebook (First to Last block by block)
4) Launch the Gradio interface and interact with the agent

⚠️⚠️ Notes that API keys are required for the project to work ⚠️⚠️