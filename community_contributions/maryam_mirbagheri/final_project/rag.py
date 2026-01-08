import os
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
aval_api_key=os.getenv("AVALAI_API_KEY")


#read json file
def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

faq_file = "data/faq.json"
products_file = "data/products.json"

faqs = read_json(faq_file)
products = read_json(products_file)

#json to text
#faq to text
def faq_to_text(faq) -> str :
    questions = '\n'.join(f'- {q.strip()}' for q in faq.get('question_variants', []))


    text = f"""
FAQ ID: {faq.get("id")}
Category: {faq.get("category")}
Questions: {questions}

Answer:
{faq.get("answer")}
""".strip()

    return text

#list of faqs
faq_texts = [faq_to_text(f) for f in faqs] 


#product to text
def product_to_text(product) -> str :
    sizes  = ", ".join(product.get('sizes', []))
    colors = ", ".join(product.get('colors', []))
    season = ", ".join(product.get('season', []))
    style  = ", ".join(product.get('style', []))

    availability_dict = product.get('availability', {})
    availability_lines = "\n".join( f"- {size}: {qty}" for size, qty in availability_dict.items()) if availability_dict else "N/A"

    text = f"""
Product ID: {product.get("id")}
Name: {product.get("name")}
Category: {product.get("category")}
Gender: {product.get("gender")}
Price: {product.get("price")} {product.get("currency")}
Sizes: {sizes}
Colors: {colors}
Material: {product.get("material")}
Season: {season}
Style: {style}
Fit: {product.get("fit")}
Availability: \n{availability_lines}
Care Instructions: {product.get("care_instructions")}

Description:
{product.get("description")}
""".strip()

    return text

#list of products
products_texts = [product_to_text(p) for p in products]

#chromadb setup & embeddings

client = chromadb.Client()

embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
    api_key=aval_api_key,
    api_base="https://api.avalai.ir/v1",
    model_name="text-embedding-3-small"
)

#faq collection
faq_collection = client.get_or_create_collection(
    name= 'faq_collection',
    embedding_function=embedding_fn
)

faq_ids = [f['id'] for f in faqs]
faq_metadatas = [{'source': 'faq'} for _ in range(len(faq_texts))]

faq_collection.add(
    ids=faq_ids,
    documents=faq_texts,
    metadatas=faq_metadatas
)

#products collection
products_collection = client.get_or_create_collection(
    name= 'products_collection',
    embedding_function=embedding_fn
)

products_ids = [p['id'] for p in products]
products_metadatas = [{'source': 'product', 'gender': p['gender'], 'category': p['category']} for p in products]

products_collection.add(
    ids=products_ids,
    documents=products_texts,
    metadatas=products_metadatas
)

def retrieve_documents(query, collection, k: int = 2):
    results = collection.query(
        query_texts=[query],
        n_results=k
    )
    
    retrieved_chunk = results['documents'][0] if results['documents'] else []  
    return retrieved_chunk

