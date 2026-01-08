## calling llm indside tools (don't thik that was a good idea)

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
- For store information (address, hours, policies), you MUST use the FAQ tool.
- For product questions, you MUST use the product tool.
- If no tool provides the answer, say you don't know.
- Do NOT answer from general knowledge.
- Be polite, friendly, and concise.
"""

#llm response
async def get_llm_response(context: str) -> str:
    messages = [
    {'role':'system', 'content': instructions},
    {'role': 'user', 'content': context}
    ]

    response = await custom_client.responses.create(
        model='gpt-4o-mini',
        input=messages,
        temperature=0.3
    )
    assistant_reply = response.output_text
    return assistant_reply

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

#-----------------------------order starts

#handling order state
order_state = {
    'active' : False,
    'stage'  : None,
    'data'   : {
        'product'      : None,     #ask_product
        'name'         : None,     #ask_name
        'phone'        : None,     #ask_phone
        'email'        : None,     #ask_email
        'confirmation' : None      #confirm
    }
}

#product validation
def validate_product(product_name: str) -> bool:
    results = retrieve_documents(product_name, products_collection, k =1)
    return len(results) > 0

#reset order state
def reset_order():
    global order_state
    order_state = {
    'active' : False,
    'stage'  : None,
    'data'   : {
        'product'      : None,     
        'name'         : None,    
        'phone'        : None,     
        'email'        : None,    
        'confirmation' : None      
    }
}
    
#save order into orders.json
def save_order(order_data):
    with open('data/orders.json', 'a', encoding='utf-8') as f:
        f.write(json.dumps(order_data) + '\n')

#----------------------------------order ends


#----------------------------------agent tools start

#special intents starts
@function_tool
async def greet_tool(user_message: str) -> str:
    """Handle greeting like hello, hi or small talk.
     dynamically using the LLM.
     The model should respond politely and naturally"""
    greeting_instructions = (
        'You are a friendly shop assistant.'
        'The user just greeted you.'
        'Respond politely, concisely, and naturally.'
        'Do not provide product information unless asked.'
    )

    message = [
        {'role':'system', 'content': greeting_instructions},
        {'role':'user', 'content': user_message}
    ]

    response = await custom_client.responses.create(
        model='gpt-4o-mini',
        input=message,
        temperature=0.7
    )
    return response.output_text.strip()

@function_tool
async def unknown_tool(user_message: str) -> str:
    """handle unknown or unclear or unrelated messages dynamically using the LLM.
    Ask clarifying questions politely."""
    unknown_instructions = (
        'You are a helpful clothing shop assistant.'
        'The user message is unclear or unrelated.'
        'Politely ask clarifying questions to understand their intent.'
        'Do not make up answers or product info.'
    )
    message = [
        {'role':'system', 'content': unknown_instructions},
        {'role':'user', 'content': user_message}
    ]

    response = await custom_client.responses.create(
        model='gpt-4o-mini',
        input=message,
        temperature=0.7
    )
    return response.output_text.strip()
#special intent ends

#retrieval starts
@function_tool
async def faq_tool(user_message: str) -> str:
    """answer FAQ questions using only the FAQ knowledge base from faq_collection"""
    retrieve_docs = retrieve_documents(user_message, faq_collection)
    return {
        'source' : 'faq',
        'documents': retrieve_docs
    }

@function_tool
async def product_tool(user_message: str) -> str:
    """answer product-related questions using only the product knowledge base from products_collection"""
    retrieve_docs = retrieve_documents(user_message, products_collection)
    context = rag_context(user_message, retrieve_docs)
    return context
#retrieval ends

#order starts
@function_tool
def order_tool(user_message: str) -> str:
    """handle multi-step order placement"""
    global order_state
    
    #order starts
    if not order_state['active']:
        order_state['active'] = True
        order_state['stage'] = 'ask_product'
        return "Sure! 😊 Let's proceed with placing your order.\nWhat product would you like to order?"
        
    #ask product
    if order_state['stage'] == 'ask_product':
        if not validate_product(user_message):
            return "I couldn't find that product. Please enter a valid product name."
        order_state['data']['product'] = user_message
        order_state['stage'] = 'ask_name'
        return 'Great choice! May I have your full name, please?'

    #ask name 
    if order_state['stage'] == 'ask_name':
        order_state['data']['name'] = user_message        
        order_state['stage'] = 'ask_phone'
        return "Thanks. What's the best phone number to contact you about your order?"

    #ask phone        
    if order_state['stage'] == 'ask_phone':
        if not user_message.isdigit() or len(user_message) != 11:
            return 'That doesn’t look like a valid phone number. Please enter an 11-digit number.'
            
        order_state['data']['phone'] = user_message
        order_state['stage'] = 'ask_email'
        return 'Which email address should we use for your order confirmation?'
    
    #ask email
    if order_state['stage'] == 'ask_email' :
        order_state['data']['email'] = user_message
        order_state['stage'] = 'ask_conf'
        return 'Perfect! To review and confirm your order, please type "review order".'
    
    #ask confirmation
    if order_state['stage'] == 'ask_conf' :
        if user_message.lower().strip() in ['review order' , 'review'] :
            order_state['stage'] = 'confirm'
            return review_order()

        elif user_message.lower() in ['no','cancel']:
             reset_order()
             return 'Order cancelled. Let me know if you need anything else.'
        
        else:
             return 'Please reply with **Review order** to review and confirm your order or **No** to cancel.'
     
    #confirm order
    if order_state['stage'] == 'confirm' :
        if user_message.lower() in ['yes', 'confirm']:
            save_order(order_state['data'])
            reset_order()
            return "Your order has been placed successfully! We'll contact you soon."
        
        elif user_message.lower() in ['no','cancel']:
             reset_order()
             return 'Order cancelled. Let me know if you need anything else.'
        
        else:
             return 'Please reply with **Yes** to confirm or **No** to cancel.'

#order review function
def review_order():
    data = order_state['data']
    return(
         f"""

         Almost done! Here's a quick review of your order:
         🛍 Product: {data['product']}
         👤 Name: {data['name']}
         📞 Phone: {data['phone']}
         📧 Email: {data['email']}

         Please reply **Yes** to confirm your order or **No** if you'd like to cancel.
         """
    )
tools = [greet_tool, unknown_tool, faq_tool, product_tool, order_tool]

service_agent = Agent(
    name='customer service agent',
    instructions=instructions,
    tools=tools,
    model='gpt-4o-mini'
)