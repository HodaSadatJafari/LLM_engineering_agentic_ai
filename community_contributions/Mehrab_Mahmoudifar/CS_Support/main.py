import os
import json
import time
import datetime
import streamlit as st
from dotenv import load_dotenv
from typing import Annotated, TypedDict, List

# Core libraries for building the agentic workflow and handling message history
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Load environment variables from the .env file
load_dotenv()
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY")
AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")

# Initialize the Large Language Model using AvalAI infrastructure
# We use gpt-4o-mini for a balance of high intelligence and better rate limit handling
llm = ChatOpenAI(
    api_key=AVALAI_API_KEY,
    base_url=AVALAI_BASE_URL,
    model="gpt-4o-mini",
    temperature=0.3,
    max_retries=3
)

# Utility function to load store data which serves as our RAG knowledge base
def get_store_knowledge():
    try:
        with open("products.json", "r", encoding="utf-8") as p_file:
            products = json.load(p_file)
        with open("faq.json", "r", encoding="utf-8") as f_file:
            faq = json.load(f_file)
        return products, faq
    except FileNotFoundError:
        # Returning empty lists if database files are missing to prevent system crash
        return [], []

# Defining the state structure for the LangGraph agent
class AgentState(TypedDict):
    # The add_messages reducer allows the graph to append new messages to the existing history
    messages: Annotated[List[BaseMessage], add_messages]

# The main logic node where the LLM processes user queries and makes decisions
def assistant_core(state: AgentState):
    products, faq = get_store_knowledge()
    
    # The system prompt defines the agent's persona and strict operational boundaries
    # Note: Language is set to formal and professional Persian for high-quality customer experience
    instruction = f"""
    شما دستیار ارشد و رسمی این فروشگاه هستید. وظیفه شما راهنمایی مشتریان با نهایت احترام و وقار است.
    
    داده‌های مرجع شما برای پاسخگویی:
    فهرست محصولات: {json.dumps(products, ensure_ascii=False)}
    سوالات متداول: {json.dumps(faq, ensure_ascii=False)}
    
    دستورالعمل‌های اجرایی:
    1. پاسخ‌های خود را صرفا بر اساس اطلاعات ارائه شده در بالا تنظیم کنید.
    2. در صورتی که کاربر تمایل به خرید داشت، الزامی است اطلاعات ذیل را دریافت کنید: نام کامل، شماره همراه، نشانی ایمیل و نام دقیق محصول مورد نظر.
    3. تا زمانی که تمامی این چهار مورد به طور کامل دریافت نشده است، از تایید نهایی سفارش خودداری نمایید.
    4. به محض تکمیل مشخصات، در انتهای آخرین پاسخ خود عبارت [ORDER_FINALIZED] را مرقوم فرمایید تا در سیستم ثبت گردد.
    5. لحن شما باید رسمی، صمیمی و مطابق با استانداردهای ادب فارسی باشد.
    """
    
    system_message = SystemMessage(content=instruction)
    
    # Implementing a manual retry loop to handle potential API Rate Limits gracefully
    for attempt in range(3):
        try:
            # Invoking the model with the system instruction and the current dialogue state
            response = llm.invoke([system_message] + state["messages"])
            return {"messages": [response]}
        except Exception as error:
            # If we hit a rate limit, we pause for a few seconds before retrying
            if "429" in str(error):
                time.sleep(5)
                continue
            # General error handling for other network or API issues
            return {"messages": [AIMessage(content="در حال حاضر اختلالی در شبکه مشاهده می شود. لطفا لحظاتی دیگر تلاش فرمایید.")]}
    
    return {"messages": [AIMessage(content="متاسفانه به دلیل ترافیک بالا، پاسخگویی مقدور نیست.")]}

# Action node responsible for persisting confirmed orders to a local JSON file
def persistence_manager(state: AgentState):
    last_content = state["messages"][-1].content
    
    # We check for the internal confirmation tag to trigger the saving process
    if "[ORDER_FINALIZED]" in last_content:
        order_log = {
            "timestamp": str(datetime.datetime.now()),
            "content": last_content.replace("[ORDER_FINALIZED]", "").strip(),
            "status": "Registered"
        }
        # Appending the order summary to our local storage file
        with open("orders.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(order_log, ensure_ascii=False) + "\n")
            
    return state

# Constructing the LangGraph agentic workflow
# assistant (logic) -> persistence (action) -> END
builder = StateGraph(AgentState)
builder.add_node("assistant", assistant_core)
builder.add_node("logger", persistence_manager)

builder.set_entry_point("assistant")
builder.add_edge("assistant", "logger")
builder.add_edge("logger", END)

# Compiling the state machine into a single executable object
agent_app = builder.compile()

# Setting up the Streamlit interface for a professional web-based interaction
st.set_page_config(page_title="سیستم پشتیبانی هوشمند", layout="centered")

st.title("پنل پشتیبانی هوشمند")
st.write("این سامانه با بهره‌گیری از هوش مصنوعی عامل‌محور، آماده پاسخگویی به پرسش‌ها و ثبت سفارش‌های شماست.")

# Administrative sidebar to view recent orders from the persistence file
with st.sidebar:
    st.header("بخش مدیریت")
    if st.button("بارگذاری لیست سفارشات"):
        if os.path.exists("orders.json"):
            with open("orders.json", "r", encoding="utf-8") as f:
                st.text_area("سوابق سفارشات", f.read(), height=350)
        else:
            st.info("تاکنون سفارشی در سامانه ثبت نشده است.")

# Initializing session state to keep track of the chat history within the browser session
if "dialogue_history" not in st.session_state:
    st.session_state.dialogue_history = []

# Rendering previous chat messages to the UI
for entry in st.session_state.dialogue_history:
    with st.chat_message(entry["role"]):
        st.write(entry["content"])

# Handling new user input
if user_text := st.chat_input("پرسش خود را اینجا بنویسید..."):
    # Storing user message in session state
    st.session_state.dialogue_history.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    # Invoking the intelligent agent to process the query
    with st.chat_message("assistant"):
        with st.spinner("در حال بررسی و بازیابی اطلاعات..."):
            # Translating Streamlit session history into LangChain message objects
            formatted_history = []
            for m in st.session_state.dialogue_history:
                if m["role"] == "user":
                    formatted_history.append(HumanMessage(content=m["content"]))
                else:
                    formatted_history.append(AIMessage(content=m["content"]))
            
            try:
                # Triggering the graph execution
                result = agent_app.invoke({"messages": formatted_history})
                raw_response = result["messages"][-1].content
                
                # Removing internal system tags before displaying the final answer to the user
                final_answer = raw_response.replace("[ORDER_FINALIZED]", "سفارش شما با موفقیت در سامانه ثبت گردید.").strip()
                
                st.write(final_answer)
                st.session_state.dialogue_history.append({"role": "assistant", "content": final_answer})
            except Exception as e:
                st.error(f"خطای سیستمی: {str(e)}")

# Project Developed by
# Mehrab Mahmoudifar