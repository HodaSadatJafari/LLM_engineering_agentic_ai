🛒 ShopBot – Enterprise AI Shopping Assistant

ShopBot is a production-ready Persian AI shopping assistant built with modern LLM architecture, semantic search, and modular admin & analytics panels.

This README is written for developers, teams, and companies who want to understand, run, extend, and maintain the system.

1. What is ShopBot?

ShopBot is an AI-powered conversational shopping system that allows users to:

Search products using natural language (Persian)

Receive grounded, non-hallucinated answers

Interact with a real product catalog

Behind the scenes, it uses:

AvalAI (OpenAI-compatible API)

GPT-4o-mini for reasoning & conversation

FAISS for semantic vector search (RAG)

Gradio 6.x for user-facing and admin UIs

2. Core Capabilities

User Features

Conversational product search

Semantic understanding ("I want to buy a phone")

Natural Persian responses

Extendable cart & checkout logic

Admin Features

Product management (add / view)

Order visibility

Automatic FAISS index rebuild

Analytics Features

Intent tracking

Search statistics

Interaction logs

3. High-Level Architecture

User
 ↓
Gradio ChatInterface
 ↓
ShopBot Agent
 ↓
Intent Detection
 ↓
RAG Layer (FAISS)
 ↓
AvalAI (GPT-4o-mini)

Key Design Principle:

LLM never answers blindly — it is always grounded by retrieved data.

4. Project Structure

shopbot/
├── app.py                  # User entry point
├── ui.py                   # User chat UI
├── agent.py                # Core decision engine
├── rag.py                  # FAISS + embeddings
├── build_index.py          # Index builder
├── intent.py               # LLM-based intent classifier
├── cart.py                 # Cart logic
├── checkout.py             # Order creation
├── admin.py                # Admin business logic
├── admin_ui.py             # Admin panel UI
├── analytics.py            # Event logger
├── analytics_dashboard.py  # Analytics UI
├── config.py               # AvalAI config
├── requirements.txt
├── .env
├── .env.example
└── data/
    ├── products.json
    ├── faqs.json
    ├── orders.json
    ├── analytics.json
    └── index/

5. Installation Guide

5.1 Create Virtual Environment

python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows

5.2 Install Dependencies

pip install -r requirements.txt

6. Environment Configuration

Create .env:

AVALAI_API_KEY=AA-XXXXXXXXXXXXXXXXXXXXXXXX
AVALAI_BASE_URL=https://api.avalai.ir/v1

Never commit .env — use .env.example for sharing.

7. Product Data Format

data/products.json

[
  {
    "name": "Samsung Galaxy A55",
    "description": "Mid-range Samsung smartphone with strong battery",
    "price": 55000000,
    "stock": 10,
    "category": "mobile"
  }
]

Important:

Products are embedded using: name + description + category

Any change requires rebuilding FAISS index

8. Build FAISS Index (Required)

python build_index.py

Expected output:

✅ FAISS indexes created successfully.

This step must be repeated whenever products or FAQs change.

9. Running the User Panel

python app.py

URL: http://127.0.0.1:7860

Example queries:

سلام

گوشی میخوام بخرم

لپتاپ گیمینگ

10. Running the Admin Panel

python admin_ui.py

URL: http://127.0.0.1:7861

Capabilities:

View products

Add products

Automatic FAISS rebuild

11. Running Analytics Dashboard

python analytics_dashboard.py

URL: http://127.0.0.1:7862

Displays:

User intents

Event counts

Interaction history

12. How RAG Works in ShopBot

User query is embedded

FAISS finds nearest product vectors

Retrieved data is injected into GPT prompt

GPT generates a grounded response

This prevents hallucination and ensures accuracy.

13. Debugging Guide

Products not found?

Check data/index/

Re-run python build_index.py

Ensure products.json is not empty

FAISS mismatch?

print(PRODUCT_INDEX.ntotal)
print(len(PRODUCT_META))

Both must match.

14. Security & Production Notes

API keys are stored only in .env

Admin UI should be protected in production

Analytics data can be moved to a database

15. Roadmap (Non-Deploy)

Authentication (Admin / Users)

Database integration

Payment gateway

Role-based access

Automated tests

Monitoring & logging

16. License

MIT License

17. Final Notes

ShopBot is designed as a real AI system, not a toy demo.
Its architecture allows seamless scaling into enterprise e-commerce solutions.

