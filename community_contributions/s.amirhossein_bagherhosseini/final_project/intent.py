from config import llm_client, MODEL_NAME

INTENTS = [
    "greet",
    "search_product",
    "add_to_cart",
    "view_cart",
    "checkout",
    "faq",
    "exit",
    "unknown"
]


def detect_intent(user_message: str) -> str:
    """
    Detect user intent using LLM
    """

    response = llm_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intent classifier for a Persian shopping chatbot.\n"
                    "Possible intents are:\n"
                    f"{', '.join(INTENTS)}\n\n"
                    "Return ONLY the intent name."
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0
    )

    intent = response.choices[0].message.content.strip()

    if intent not in INTENTS:
        return "unknown"

    return intent
