import json
from pathlib import Path
import faiss
import numpy as np

from config import llm_client

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
DATA_DIR = Path("data")
INDEX_DIR = Path("data/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

PRODUCT_INDEX_FILE = INDEX_DIR / "products.faiss"
FAQ_INDEX_FILE = INDEX_DIR / "faqs.faiss"

PRODUCT_META_FILE = INDEX_DIR / "products_meta.json"
FAQ_META_FILE = INDEX_DIR / "faqs_meta.json"

EMBEDDING_MODEL = "text-embedding-3-small"

# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------
def load_json(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def embed_texts(texts: list[str]) -> np.ndarray:
    response = llm_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts
    )
    vectors = [item.embedding for item in response.data]
    return np.array(vectors, dtype="float32")

# -----------------------------------------------------------------------------
# Build Indexes
# -----------------------------------------------------------------------------
def build_product_index(products: list[dict]):
    """
    Build FAISS index for products using name + description + category
    """
    texts = [
        f"{p.get('name', '')} {p.get('description', '')} {p.get('category', '')}"
        for p in products
    ]

    embeddings = embed_texts(texts)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    return index, products

def build_faq_index(faqs: list[dict]):
    texts = [f.get("question", "") for f in faqs]

    embeddings = embed_texts(texts)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    return index, faqs

def build_and_save_indexes():
    products = load_json("products.json")
    faqs = load_json("faqs.json")

    if products:
        product_index, product_meta = build_product_index(products)
        faiss.write_index(product_index, str(PRODUCT_INDEX_FILE))
        save_json(PRODUCT_META_FILE, product_meta)

    if faqs:
        faq_index, faq_meta = build_faq_index(faqs)
        faiss.write_index(faq_index, str(FAQ_INDEX_FILE))
        save_json(FAQ_META_FILE, faq_meta)

# -----------------------------------------------------------------------------
# Load Indexes
# -----------------------------------------------------------------------------
def load_index(index_file, meta_file):
    if not index_file.exists() or not meta_file.exists():
        return None, []

    index = faiss.read_index(str(index_file))

    with open(meta_file, encoding="utf-8") as f:
        meta = json.load(f)

    return index, meta

PRODUCT_INDEX, PRODUCT_META = load_index(
    PRODUCT_INDEX_FILE, PRODUCT_META_FILE
)

print("🔍 FAISS DEBUG")
print("PRODUCT_META length:", len(PRODUCT_META))
if PRODUCT_INDEX is None:
    print("PRODUCT_INDEX is None")
else:
    print("FAISS ntotal:", PRODUCT_INDEX.ntotal)

FAQ_INDEX, FAQ_META = load_index(
    FAQ_INDEX_FILE, FAQ_META_FILE
)

# -----------------------------------------------------------------------------
# Search
# -----------------------------------------------------------------------------
def search_products(query: str, k: int = 3):
    if PRODUCT_INDEX is None or not PRODUCT_META:
        return []

    query_vec = embed_texts([query])
    _, indices = PRODUCT_INDEX.search(query_vec, k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(PRODUCT_META):
            results.append(PRODUCT_META[idx])

    return results

def search_faq(query: str, k: int = 1):
    if FAQ_INDEX is None or not FAQ_META:
        return None

    query_vec = embed_texts([query])
    _, indices = FAQ_INDEX.search(query_vec, k)

    idx = indices[0][0]
    if 0 <= idx < len(FAQ_META):
        return FAQ_META[idx].get("answer")

    return None
