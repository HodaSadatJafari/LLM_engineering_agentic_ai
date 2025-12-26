#single agent

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from rag import retrieve_documents, faq_collection, products_collection
import json
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, function_tool
import asyncio

#api key
load_dotenv()
aval_api_key=os.getenv("AVALAI_API_KEY")
custom_client = AsyncOpenAI(
    api_key=aval_api_key,
    base_url="https://api.avalai.ir/v1"
)
set_default_openai_client(custom_client)
set_tracing_disabled(True)

#instructions
instructions = """
You are a customer service assistant for a clothing shop.

CRITICAL RULES:
- You MUST use tools to answer factual questions.
- Use ONLY ONE tool per user message.
- When a tool returns a response, you MUST return it directly to the user.
- If a tool returns text, output it verbatim and STOP.
- Do not summarize, rewrite, or add commentary.
- Do NOT call another tool after receiving a valid answer.
- If the user greets you, respond politely.
- If the user's message is unclear, ask a clarifying question
- For store information (address, hours, policies), you MUST use the FAQ tool.
- For product questions, you MUST use the product tool.
- If no tool provides the answer, say you don't know.
- Do NOT answer from general knowledge.
- Be polite, friendly, and concise.
"""

#llm response
# async def get_llm_response(context: str) -> str:
#     messages = [
#     {'role':'system', 'content': instructions},
#     {'role': 'user', 'content': context}
#     ]

#     response = await custom_client.responses.create(
#         model='gpt-4o-mini',
#         input=messages,
#         temperature=0.3
#     )
#     assistant_reply = response.output_text
#     return assistant_reply

#-------------------------rag context starts
def rag_context(user_message: str, docs: list[str]) -> str:
    retrieved_text = '\n\n'.join(docs)

    context = f"""
Use the following context to answer the user's question.
If the answer is not in the context, say you don't know.

Context:
{retrieved_text}

Question:
{user_message}
"""
    return context
#-------------------------rag context ends



#----------------------------------order ends


#----------------------------------agent tools start

#retrieval starts
@function_tool
async def faq_tool(user_message: str) -> str:
    """answer FAQ questions using only the FAQ knowledge base from faq_collection"""
    print("TOOL CALLED: faq_tool")
    print("QUERY:", user_message)
    retrieve_docs = retrieve_documents(user_message, faq_collection)
    print(f"DOCS FOUND: {len(retrieve_docs)}")
    if not retrieve_docs:
        return 'No matching FAQ were found'

    return retrieve_docs

@function_tool
async def product_tool(user_message: str) -> str:
    """answer product-related questions using only the product knowledge base from products_collection"""

    print("TOOL CALLED: product_tool")
    print("QUERY:", user_message)
    
    retrieve_docs = retrieve_documents(user_message, products_collection)

    print(f"DOCS FOUND: {len(retrieve_docs)}")

    print(retrieve_docs)

    if not retrieve_docs:
        return 'No matching product were found'

    return ("Here is the relevant product information:\n\n"
    + "\n\n".join(retrieve_docs))
#retrieval ends


tools = [faq_tool, product_tool]

service_agent = Agent(
    name='customer service agent',
    instructions=instructions,
    tools=tools,
    model='gpt-4o-mini'
)