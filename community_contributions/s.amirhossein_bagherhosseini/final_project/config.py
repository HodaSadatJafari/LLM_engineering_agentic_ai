from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

AVALAI_API_KEY = os.getenv("AVALAI_API_KEY")
AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")
MODEL_NAME = "gpt-4o-mini"

llm_client = OpenAI(
    api_key=AVALAI_API_KEY,
    base_url=AVALAI_BASE_URL,
    timeout=30,        # 🔥 خیلی مهم
    max_retries=2      # 🔥 خیلی مهم
)
