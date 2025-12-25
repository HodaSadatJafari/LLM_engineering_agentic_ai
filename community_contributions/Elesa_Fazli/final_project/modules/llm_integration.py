# modules/llm_integration.py
import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def generate_response(query, retrieval_result, history=None):
    """
    Generate natural language response using OpenAI LLM.
    Includes retrieved products, FAQs, and conversation history.
    """
    context = ""
    if retrieval_result.get("products"):
        context += "Products info:\n"
        for p in retrieval_result["products"]:
            context += f"- {p['title']}, ${p['price']}, {p['description']}\n"

    if retrieval_result.get("faqs"):
        context += "FAQs:\n"
        for f in retrieval_result["faqs"]:
            question = f.get("question") or f.get("q", "")
            answer = f.get("answer") or f.get("a", "")
            context += f"- Q: {question} A: {answer}\n"

    if history:
        context += "Conversation history:\n"
        for h in history[-5:]:
            context += f"Q: {h['query']} A: {h['response']}\n"

    prompt = f"User asked: {query}\nUse the following context to answer naturally:\n{context}\nAnswer:"

    try:
        if client is None:
            return "LLM response unavailable: please set OPENAI_API_KEY."
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return res.choices[0].message.content
    except Exception:
        return "I'm here to help, but I couldn't generate a response at this moment."
