import os
import time
from typing import Annotated, TypedDict, List
from dotenv import load_dotenv
import streamlit as st

# LangChain and LangGraph core components
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Load environment variables for API authentication
load_dotenv()
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY")
AVALAI_BASE_URL = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Initialize the Large Language Model via AvalAI
# Using gpt-4o-mini for efficient processing and better rate limit resilience
llm = ChatOpenAI(
    api_key=AVALAI_API_KEY,
    base_url=AVALAI_BASE_URL,
    model="gpt-4o-mini",
    temperature=0.5,
    max_retries=3
)

# Search tool configuration to fetch real-time travel data from the web
search_tool = TavilySearchResults(k=3)

# Define the state schema for the travel planning agent
class TravelState(TypedDict):
    # History of the conversation managed by add_messages reducer
    messages: Annotated[List[BaseMessage], add_messages]
    # Storage for raw data retrieved during the research phase
    search_context: str

# Node 1: Research Node
# This function queries the web to find current weather, prices, and attractions
def research_node(state: TravelState):
    user_request = state["messages"][-1].content
    
    # Constructing a targeted search query for better results
    query = f"latest travel guide weather and hotels for {user_request} in 2025"
    
    try:
        # Executing the search tool
        raw_results = search_tool.invoke({"query": query})
        return {"search_context": str(raw_results)}
    except Exception:
        # Fallback if the search tool fails
        return {"search_context": "Web search was unavailable at the moment."}

# Node 2: Planning Node
# This function synthesizes search data into a structured Persian itinerary
def planner_node(state: TravelState):
    context = state.get("search_context", "General knowledge")
    
    # Expert prompt to guide the LLM in creating high-quality Persian content
    system_prompt = SystemMessage(content=f"""
    شما یک کارشناس خبره برنامه‌ریزی سفر هستید. وظیفه شما تنظیم یک برنامه سفر دقیق بر اساس داده‌های زنده است.
    
    اطلاعات زنده استخراج شده از وب:
    {context}
    
    قوانین خروجی:
    1. برنامه باید شامل جزئیات اماکن دیدنی، وضعیت آب و هوا و برآورد هزینه باشد.
    2. یک برنامه پیشنهادی سه روزه تنظیم کنید.
    3. توصیه‌های کاربردی برای رزرو هتل و حمل و نقل ارائه دهید.
    4. لحن پاسخگویی باید الهام‌بخش، رسمی و کاملا فارسی باشد.
    """)
    
    # Manual retry mechanism for AvalAI Rate Limit (429) handling
    for attempt in range(3):
        try:
            response = llm.invoke([system_prompt] + state["messages"])
            return {"messages": [response]}
        except Exception as e:
            if "429" in str(e):
                time.sleep(5)
                continue
            return {"messages": [AIMessage(content="در حال حاضر امکان پردازش درخواست سفر مقدور نیست.")]}
    
    return {"messages": [AIMessage(content="خطا در برقراری ارتباط با سرویس هوشمند سفر.")]}

# Orchestrating the Agentic Workflow
workflow = StateGraph(TravelState)
workflow.add_node("researcher", research_node)
workflow.add_node("planner", planner_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "planner")
workflow.add_edge("planner", END)

# Final agent application
travel_agent = workflow.compile()

# Streamlit UI Construction
st.set_page_config(page_title="AI Travel Planner", layout="wide")

st.title("سامانه هوشمند برنامه‌ریزی سفر")
st.write("مقصد مورد نظر و اولویت‌های خود را بنویسید تا برنامه اختصاصی شما تدوین شود.")

# Persisting conversation history in Streamlit session state
if "travel_history" not in st.session_state:
    st.session_state.travel_history = []

# Displaying chat messages
for msg in st.session_state.travel_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input processing
if prompt := st.chat_input("به کجا می‌خواهید سفر کنید؟"):
    st.session_state.travel_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("در حال تحقیق و تنظیم برنامه سفر..."):
            # Prepare messages for the graph execution
            lc_history = []
            for m in st.session_state.travel_history:
                if m["role"] == "user":
                    lc_history.append(HumanMessage(content=m["content"]))
                else:
                    lc_history.append(AIMessage(content=m["content"]))
            
            try:
                # Invoke the agent graph
                result = travel_agent.invoke({"messages": lc_history})
                final_reply = result["messages"][-1].content
                
                st.markdown(final_reply)
                st.session_state.travel_history.append({"role": "assistant", "content": final_reply})
            except Exception as e:
                st.error(f"System Error: {str(e)}")

# Mehrab Mahmoudifar