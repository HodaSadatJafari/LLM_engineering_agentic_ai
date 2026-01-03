from config import llm_client, MODEL_NAME

response = llm_client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {"role": "user", "content": "سلام فقط بگو اوکی"}
    ],
    timeout=30
)

print(response.choices[0].message.content)
