## using llm only


import os
from dotenv import load_dotenv
from openai import OpenAI
from rag import retrieve_documents, faq_collection, products_collection
import json
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled, function_tool
import asyncio

#api key
load_dotenv()
aval_api_key=os.getenv("AVALAI_API_KEY")
client = OpenAI(
    api_key=aval_api_key,
    base_url="https://api.avalai.ir/v1"
)

#instructions
instructions = """
You are a customer service assistant for a clothing shop.
Your rules:
- Be polite, friendly, and concise.
- Answer clearly in simple language.
- If you are unsure, ask a clarifying question.
- Do not invent product details or store policies.
"""

intent_prompt = """
You are an intent classification engine for a clothing shop assistant.

Your task:
Classify the user's message into ONE of the following intents:

- greeting        (hello, hi, good morning, small talk)
- faq             (store hours, returns, policies, support questions)
- product         (asking about products, prices, availability, features)
- order           (buying, ordering, checkout, purchase intent)
- unknown         (unclear or unrelated messages)


Rules:
- Output ONLY the intent name
- Do NOT explain
- Do NOT add punctuation
- Do NOT add extra words
- Output must be lowercase
"""

#--------------------------intent detecting starts
def detect_intent(user_query:str) -> str:
    response = client.responses.create(
        model='gpt-4o-mini',
        input=[
            {'role': 'system','content': intent_prompt},
            {'role': 'user','content': user_query}
        ]
    )

    intent = response.output_text.strip().lower()
    return intent
#--------------------------intent detecting ends

#-------------------------relevant docs retireve starts
#faq docs
# def retrieve_faq_docs(user_message: str, k:int = 3) -> list[str]:
#     return retrieve_documents(user_message, faq_collection, k=k)

# #products docs
# def retrieve_product_docs(user_message: str, k:int = 3) -> list[str]:
#     return retrieve_documents(user_message, products_collection, k=k)

def retrieve_relevant_docs(user_message: str, intent: str) :
    if intent == 'faq':
        return retrieve_documents(user_message, faq_collection)
    
    if intent == 'product':
        return retrieve_documents(user_message, products_collection)
    
    return None

#rag context
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
#-------------------------relevant docs retireve ends

#-----------------------------order starts

#handling order
order_state = {
    'active' : False,
    'stage'  : None,
    'data'   : {
        'product'      : None,     #ask_product
        'name'         : None,     #ask_name
        'phone'        : None,     #ask_phone
        'email'        : None,     #ask_email
        'ask_conf'     : None,     #ask_conf
        'confirmation' : None      #confirm
    }
}

def order_handler(user_message : str):
    """information needed for order:
        global order_state
        Product name -> validate if that product exist and available
        Name
        Phone no. -> validate number of digits - should be 11
        Email
    """
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
            return 'Please enter a valid 11-digit phone number.'
            
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

#----------------------------------special intent starts
def special_intent(intent: str) -> str:
    if intent == 'greeting':
        return "Hello! 👋 How can I help you today?"
    
    if intent == 'unknown':
        return f"I'm not sure what you're looking for. \nAre you asking about store information or a product?"
    
    return None
#----------------------------------special intent ends

#llm response
def get_llm_response(context: str) -> str:
    messages = [
    {'role':'system', 'content': instructions},
    {'role': 'user', 'content': context}
    ]

    response = client.responses.create(
        model='gpt-4o-mini',
        input=messages,
        temperature=0.3
    )
    assistant_reply = response.output_text
    return assistant_reply

#routing user message
def route_user_message(user_message: str):
    #order flow
    if order_state['active']:
        return order_handler(user_message)
    
    intent = detect_intent(user_message)

    #special intents
    special_resp = special_intent(intent)
    if special_resp:
        return special_resp
    
    #order
    if intent == 'order':
        return order_handler(user_message, intent)
    
    #faq or products 
    retrieved_data = retrieve_relevant_docs(user_message,intent)
    if not retrieved_data:
        return "Hmm, I didn't quite catch that. Could you rephrase your question?"
    
    context = rag_context(user_message, retrieved_data)
    return get_llm_response(context)