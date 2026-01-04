import streamlit as st
from typing import Any, List, Dict
from pydantic import BaseModel, Field
import uuid
import os
import json
from dotenv import load_dotenv
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# ---------- LangChain imports ----------
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langsmith import Client
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, AIMessage

# --------------------------------------------------------------
#  CONFIGURATION - Edit these paths as needed
# --------------------------------------------------------------
# Database paths (relative to project root)
BASE_DIR = Path("./chroma_db")
PRODUCT_DB_PATH = BASE_DIR / "products"
SALES_DB_PATH = BASE_DIR / "sales"

# change path to your data files
PRODUCTS_DATA_PATH = Path("path")
SALES_DATA_PATH = Path("path")

# Ensure directories exist
BASE_DIR.mkdir(parents=True, exist_ok=True)
PRODUCTS_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------
#  1. LLM & LangSmith Connection
# --------------------------------------------------------------
# Make LangSmith optional
try:
    client = Client()
except Exception:
    client = None

llm = ChatOpenAI(
    api_key=os.getenv("AVALAI_API_KEY"),  
    base_url=os.getenv("AVALAI_BASE_URL"),  
    model=os.getenv("LLM_MODEL"),
    temperature=0.2,
    streaming=True,
)

# --------------------------------------------------------------
#  2. Local Vector Store Setup with Data Loading
# --------------------------------------------------------------
embeddings = OpenAIEmbeddings(
    api_key=os.getenv("AVALAI_API_KEY"),  
    base_url=os.getenv("AVALAI_BASE_URL"),  
    model=os.getenv("EMBEDDING_MODEL"),
    show_progress_bar=False,
    skip_empty=True,
)


def load_and_format_data():
    print("Loading product and sales data...")
    
    # Load products
    if not PRODUCTS_DATA_PATH.exists():
        st.error(f"Products data file not found: {PRODUCTS_DATA_PATH}")
        st.info(f"Expected location: {PRODUCTS_DATA_PATH.absolute()}")
        st.info("Please create a 'data/products.json' file with your product data.")
        st.stop()
    
    with PRODUCTS_DATA_PATH.open("r", encoding="utf-8") as f:
        products_data = json.load(f)
    
    print(f"Raw products data type: {type(products_data)}")
    print(f"Products data keys: {products_data.keys() if isinstance(products_data, dict) else 'Not a dict'}")
    
    # Load sales
    if not SALES_DATA_PATH.exists():
        st.error(f"Sales data file not found: {SALES_DATA_PATH}")
        st.info(f"Expected location: {SALES_DATA_PATH.absolute()}")
        st.info("Please create a 'data/sales.json' file with your sales data.")
        st.stop()
    
    with SALES_DATA_PATH.open("r", encoding="utf-8") as f:
        sales_data = json.load(f)
    
    print(f" Raw sales data type: {type(sales_data)}")
    print(f" Sales data keys: {sales_data.keys() if isinstance(sales_data, dict) else 'Not a dict'}")

    # Format product chunks - handle both dict with "products" key and direct list
    product_chunks = []
    products_list = products_data.get("products", []) if isinstance(products_data, dict) else products_data
    
    if not products_list:
        st.warning(f" No products found in {PRODUCTS_DATA_PATH}")
        print(f" Products data structure: {products_data}")
    
    for i, item in enumerate(products_list):
        try:
            # Handle different review field names
            reviews = item.get('review', item.get('customer_reviews', item.get('reviews', [])))
            if not isinstance(reviews, list):
                reviews = []
            
            text = (
                f"Product Name: {item.get('name', 'Unknown')}\n"
                f"Price: {item.get('price', 'N/A')}\n"
                f"Rating: {item.get('rating', 'N/A')} stars\n"
                f"Description: {item.get('description', 'No description')}\n"
            )
            
            if reviews:
                text += "Customer Reviews:\n"
                for review in reviews[:3]:  
                    text += f"- {review}\n"
            
            product_chunks.append(text)
        except Exception as e:
            print(f"Error processing product {i}: {e}")
            print(f"   Item data: {item}")

    # Format sales chunks - handle both dict with "sales" key and direct list
    sales_chunks = []
    sales_list = sales_data.get("sales", []) if isinstance(sales_data, dict) else sales_data
    
    if not sales_list:
        st.warning(f"No sales items found in {SALES_DATA_PATH}")
        print(f"Sales data structure: {sales_data}")
    
    for i, item in enumerate(sales_list):
        try:
            # Handle different review field names
            reviews = item.get('customer_reviews', item.get('review', item.get('reviews', [])))
            if not isinstance(reviews, list):
                reviews = []
            
            text = (
                f"Product Name: {item.get('name', 'Unknown')}\n"
                f"Discount: {item.get('off_percent', item.get('discount', 0))}%\n"
                f"Price: {item.get('price', 'N/A')}\n"
                f"Rating: {item.get('rating', 'N/A')} stars\n"
                f"Description: {item.get('description', 'No description')}\n"
            )
            
            if reviews:
                text += "Customer Reviews:\n"
                for review in reviews[:3]:  # Take up to 3 reviews
                    text += f"- {review}\n"
            
            sales_chunks.append(text)
        except Exception as e:
            print(f"Error processing sale item {i}: {e}")
            print(f"   Item data: {item}")

    print(f"Formatted {len(product_chunks)} product chunks and {len(sales_chunks)} sales chunks.")
    
    if len(product_chunks) == 0:
        st.error("No product data was loaded! Check your products.json file format.")
        st.stop()
    
    if len(sales_chunks) == 0:
        st.error("No sales data was loaded! Check your sales.json file format.")
        st.stop()
    
    return product_chunks, sales_chunks


def build_vector_databases(product_chunks, sales_chunks):
    
    print("Vector store folders not found → Building new databases...")
    with st.spinner("Building vector databases... This may take a moment."):
        # Create products database
        Chroma.from_texts(
            texts=product_chunks,
            embedding=embeddings,
            collection_name="products",
            persist_directory=str(PRODUCT_DB_PATH),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )

        # Create sales database
        Chroma.from_texts(
            texts=sales_chunks,
            embedding=embeddings,
            collection_name="sales",
            persist_directory=str(SALES_DB_PATH),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )

    print("Databases built and saved successfully!")


def load_existing_databases():
    
    print("Vector store folders found → Loading existing databases...")

    db_products = Chroma(
        persist_directory=str(PRODUCT_DB_PATH),
        embedding_function=embeddings,
        collection_name="products",
        tenant=DEFAULT_TENANT,
        database=DEFAULT_DATABASE,
    )

    db_sales = Chroma(
        persist_directory=str(SALES_DB_PATH),
        embedding_function=embeddings,
        collection_name="sales",
        tenant=DEFAULT_TENANT,
        database=DEFAULT_DATABASE,
    )

    return db_products, db_sales


# Initialize or load databases
@st.cache_resource
def initialize_databases():
    """Initialize databases with caching to avoid rebuilding on every rerun."""
    # Check if databases exist and have data
    db_exists = (PRODUCT_DB_PATH.exists() and SALES_DB_PATH.exists())
    
    if not db_exists:
        st.info("First time setup: Building vector databases from your data files...")
        product_chunks, sales_chunks = load_and_format_data()
        build_vector_databases(product_chunks, sales_chunks)
        st.success("Databases created successfully!")
    
    # Load databases (whether just created or already existing)
    db_products = Chroma(
        persist_directory=str(PRODUCT_DB_PATH),
        embedding_function=embeddings,
        collection_name="products",
        tenant=DEFAULT_TENANT,
        database=DEFAULT_DATABASE,
    )

    db_sales = Chroma(
        persist_directory=str(SALES_DB_PATH),
        embedding_function=embeddings,
        collection_name="sales",
        tenant=DEFAULT_TENANT,
        database=DEFAULT_DATABASE,
    )
    
    # Create retrievers
    retriever_products = db_products.as_retriever(search_kwargs={"k": 5})
    retriever_sales = db_sales.as_retriever(search_kwargs={"k": 5})
    
    print(f"Databases loaded. Products collection size: {db_products._collection.count()}")
    print(f"Databases loaded. Sales collection size: {db_sales._collection.count()}")
    
    return retriever_products, retriever_sales


retriever_products, retriever_sales = initialize_databases()

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
#  5. Agent Setup with create_tool_calling_agent
# --------------------------------------------------------------
tools = [search_products, search_sales, order_placement_tool]

# Create the prompt template for the agent
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a customer service chatbot for an e-commerce store. Your ONLY roles is to:
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
"""),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create the agent
agent = create_tool_calling_agent(llm, tools, prompt)


agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
)

# --------------------------------------------------------------
#  6. Streamlit UI
# --------------------------------------------------------------
st.set_page_config(page_title="E-commerce Chatbot", page_icon="🛒")
st.title("🛒 Customer Service Chatbot")
st.caption("Ask me about products, sales, or place an order!")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if user_input := st.chat_input("How can I help you shop today?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        try:
            # Invoke the agent with chat history
            result = agent_executor.invoke({
                "input": user_input,
                "chat_history": st.session_state.chat_history
            })
            
            full_response = result["output"]
            response_placeholder.markdown(full_response)
            
            # Update chat history
            st.session_state.chat_history.append(HumanMessage(content=user_input))
            st.session_state.chat_history.append(AIMessage(content=full_response))
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        except Exception as e:
            error_message = f"Sorry, I encountered an error: {str(e)}"
            response_placeholder.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})