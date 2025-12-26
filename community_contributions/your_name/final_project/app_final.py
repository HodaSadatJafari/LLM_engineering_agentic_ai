import streamlit as st
from typing import Any, List, Dict
from pydantic import BaseModel, Field
import uuid
import os
import chromadb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------- LangChain imports ----------
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langsmith import Client
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# --------------------------------------------------------------
#  1. LLM & LangSmith Connection
# --------------------------------------------------------------
client = Client() 

llm = ChatOpenAI(
    api_key=os.getenv("AVALAI_API_KEY"),
    base_url=os.getenv("AVALAI_BASE_URL"),
    model="gpt-4o",
    temperature=0.2,
    streaming=True,
)

# --------------------------------------------------------------
#  2. Vector Store Connection (Retrieval Only)
# --------------------------------------------------------------
embeddings = OpenAIEmbeddings(
    api_key=os.getenv("AVALAI_API_KEY"),
    base_url=os.getenv("AVALAI_BASE_URL"),
    model="text-embedding-3-small",
    show_progress_bar=False,
    skip_empty=True,
)

# Initialize Chroma Cloud Client
cloud_client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_CLOUD_API_KEY"),
    tenant=os.getenv("CHROMA_TENANT"),
    database=os.getenv("CHROMA_DATABASE")
)

# Connect to existing collections in Chroma Cloud
db_products = Chroma(
    client=cloud_client,
    collection_name="products",
    embedding_function=embeddings
)

db_sales = Chroma(
    client=cloud_client,
    collection_name="sales",
    embedding_function=embeddings
)

# Create retrievers
retriever_products = db_products.as_retriever(search_kwargs={"k": 5})
retriever_sales = db_sales.as_retriever(search_kwargs={"k": 5})

# --------------------------------------------------------------
#  3. Extraction Logic (For Order Tool)
# --------------------------------------------------------------
class Order(BaseModel):
    name: str = Field(..., description="Full name of the customer")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    itemlist: str = Field(..., description="Comma-separated list of items")

parser = JsonOutputParser(pydantic_object=Order)
order_prompt = PromptTemplate(
    template="Extract order details from: {query}\n{format_instructions}",
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)
order_extraction_chain = order_prompt | llm | parser

# --------------------------------------------------------------
#  4. Tools (Search & Order)
# --------------------------------------------------------------
@tool
def order_placement_tool(customer_message: str) -> dict:
    """Call when the user wants to place an order."""
    try:
        result = order_extraction_chain.invoke({"query": customer_message})
        return {"status": "success", "message": f"Order confirmed for {result['name']}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@tool
def search_products(query: str) -> str:
    """Search the regular catalog."""
    docs = retriever_products.invoke(query)
    return "\n\n".join([f"Product: {d.page_content}" for d in docs]) if docs else "No products found."

@tool
def search_sales(query: str) -> str:
    """Search the discounted catalog."""
    docs = retriever_sales.invoke(query)
    return "\n\n".join([f"Sale Item: {d.page_content}" for d in docs]) if docs else "No sales found."

# --------------------------------------------------------------
#  5. Agent Setup
# --------------------------------------------------------------
tools = [search_products, search_sales, order_placement_tool]
memory_checkpointer = MemorySaver()
system_message = """You are a customer service chatbot for an e-commerce store. Your ONLY roles is to:
1. Help customers find products in our catalog 
2. Answer questions about products, prices, and availability.
3. Help customers place orders.

STRICT RULES:
- You MUST ONLY answer questions related to our products, services, and orders
- If asked about anything unrelated to our store (politics, general knowledge, coding, math, personal advice, etc.), politely decline and redirect to shopping assistance
- DO NOT engage in general conversation or answer questions outside of customer service
- Always stay professional and focused on helping customers shop
- If asked for discounted/on sale items, use the search_sales tool;
- if user did not specify which catalog, USE ITEMS IN BOTH CATALOGS WHEN SEARCHING example:
Customer: "give me a list of gaming mouse?"
answrer: 
1.mouse #1: (mouse #1 info) 
2. mouse #2: (mouse #2 info) ...
mouses on sale:
1. mouse_onsale #1: (mouse_onsale #1 info)

Example responses to off-topic questions:
- "I'm here to help you with shopping and product inquiries. Is there a product I can help you find?"
- "I can only assist with product searches and orders. How can I help you shop today?"
- "That's outside my scope as a customer service bot. Can I help you find any products instead?"
"""

agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory_checkpointer,
    prompt=system_message,
)

# --------------------------------------------------------------
#  6. Streamlit UI
# --------------------------------------------------------------
st.set_page_config(page_title="E-commerce Chatbot")
st.title("Customer Service Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("How can I help you shop today?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        inputs = {"messages": [("user", m["content"]) for m in st.session_state.messages]}
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        for chunk in agent.stream(inputs, config=config, stream_mode="values"):
            if "messages" in chunk:
                last_msg = chunk["messages"][-1]
                if last_msg.type == "ai":
                    full_response = last_msg.content
                    response_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})