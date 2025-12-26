import os
import gradio as gr
import asyncio
from single_agent import service_agent
from rag import retrieve_documents, products_collection
from agents import Agent, Runner
import json
import time

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

#order starts

ORDER_KEYWORDS = [
    "order",
    "buy",
    "purchase",
    "place an order",
    "i want to order",
]

def is_order_intent(message: str) -> bool:
    msg = message.lower()
    return any(k in msg for k in ORDER_KEYWORDS)


def order_state_machine(user_message: str) -> str:
    """handle multi-step order placement"""

    print("ORDER CALLED")
    print("QUERY:", user_message)
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
            return "That doesn't look like a valid phone number. Please enter an 11-digit number."
            
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
            print(order_state['active'], order_state['stage'])
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
    file_path = 'data/orders.json'

    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    with open(file_path, 'r', encoding='utf-8') as f:
        orders = json.loads(f)

    orders.append(order_data)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

#---------------------------------------ORDER ENDS

async def chat(user_message, chat_history):

    print("USER MESSAGE:", user_message)
    print(order_state['active'])

    chat_history.append({
        'role': 'user',
        'content': user_message
    })
    chat_history.append({
        'role': 'assistant',
        'content': ''
    })

    if order_state['active']:
        reply = order_state_machine(user_message)
    elif is_order_intent(user_message):
        reply = order_state_machine(user_message)
    else:
        result = await Runner.run(service_agent, user_message)
        reply = result.final_output

    print("AGENT OUTPUT:", reply)

    streamed = ""
    for char in reply:
        streamed += char
        chat_history[-1]["content"] = streamed
        yield chat_history
        await asyncio.sleep(0.03)  

# ------------------------------- GRADIO

with gr.Blocks() as demo:
    gr.Markdown('## 🛍️ Clothing Shop Assistant')
    gr.Markdown('Ask about products, FAQs, or place an order.')

    chatbot = gr.Chatbot(
        label='Assistant',
        height=450
    )

    with gr.Row():
        user_input = gr.Textbox(
            placeholder='Ask me anything...',
            scale=4,
            show_label=False
        )
        send_btn = gr.Button('Send', scale=1)

    send_btn.click(
        chat,
        inputs=[user_input, chatbot],
        outputs=chatbot
    )

    user_input.submit(
        chat,
        inputs=[user_input, chatbot],
        outputs=chatbot
    )

    send_btn.click(
        lambda: "",
        None,
        user_input
    )
    user_input.submit(
        lambda: "",
        None,
        user_input
    )

    gr.Markdown(
        "💡 Try: *Hi*, *What are your return policies?*, *I want to order a jacket*"
    )


demo.launch()