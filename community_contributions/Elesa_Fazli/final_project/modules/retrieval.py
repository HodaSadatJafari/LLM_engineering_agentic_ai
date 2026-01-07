# modules/retrieval.py
import json
import os
import pickle

import numpy as np
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize OpenAI client (optional if key is set)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

class HybridRetriever:
    """Hybrid RAG retriever: combines TF-IDF and OpenAI embeddings."""
    def __init__(self, products_path="data/products.json", faqs_path="data/faqs.json", embedding_cache="data/embedding_cache.pkl"):
        self.products = self._load(products_path)
        self.faqs = self._load(faqs_path)
        self.embedding_cache = embedding_cache

        # Build corpus for TF-IDF and embeddings
        self.product_texts = [self._build_product_text(p) for p in self.products]
        self.faq_texts = [self._build_faq_text(f) for f in self.faqs]
        self.corpus = self.product_texts + self.faq_texts

        # TF-IDF
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus) if self.corpus else None

        # Embeddings
        self.embeddings = self._build_embeddings()

        # Multi-turn conversation memory
        self.memory = {}

    def _load(self, path):
        """Load JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_product_text(self, p):
        """Concatenate product metadata for search."""
        return f"{p.get('title','')} {p.get('description','')} {p.get('brand','')} {p.get('category','')} {' '.join(p.get('tags', []))}"

    def _build_faq_text(self, f):
        """Prepare FAQ text."""
        q = f.get("question") or f.get("q", "")
        a = f.get("answer") or f.get("a", "")
        return f"Question: {q} Answer: {a}"

    def _embed(self, text):
        """Get OpenAI embedding with caching."""
        cache = {}
        if os.path.exists(self.embedding_cache):
            with open(self.embedding_cache, "rb") as f:
                cache = pickle.load(f)
        if text in cache:
            return cache[text]
        if client is None:
            return np.zeros(1536, dtype="float32")
        try:
            res = client.embeddings.create(model="text-embedding-3-small", input=text)
            emb = np.array(res.data[0].embedding, dtype="float32")
            cache[text] = emb
            with open(self.embedding_cache, "wb") as f:
                pickle.dump(cache, f)
            return emb
        except:
            return np.zeros(1536, dtype="float32")

    def _build_embeddings(self):
        """Build embeddings for the entire corpus."""
        return np.array([self._embed(t) for t in self.corpus])

    def _metadata_boost(self, product, query):
        """Boost ranking based on tags, brand, category match."""
        q = query.lower()
        score = 1.0
        if any(tag.lower() in q for tag in product.get("tags", [])):
            score += 0.2
        if product.get("brand","").lower() in q:
            score += 0.2
        if product.get("category","").lower() in q:
            score += 0.3
        return score

    def _update_memory(self, conversation_id, query, response):
        """Store conversation history."""
        if conversation_id not in self.memory:
            self.memory[conversation_id] = []
        self.memory[conversation_id].append({"query": query, "response": response})

    def retrieve(self, query, top_k=5, conversation_id=None):
        """Retrieve relevant products and FAQs using TF-IDF + Embeddings."""
        q_vec = self.vectorizer.transform([query])
        tfidf_scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten() if self.tfidf_matrix is not None else np.zeros(len(self.corpus))
        q_emb = self._embed(query)
        embed_scores = cosine_similarity([q_emb], self.embeddings).flatten() if self.embeddings.size > 0 else np.zeros(len(self.corpus))

        # Combine scores
        combined_scores = 0.5 * tfidf_scores + 0.5 * embed_scores
        ranked_idx = np.argsort(-combined_scores)

        # Separate products and FAQs
        num_products = len(self.products)
        products, faqs = [], []
        for idx in ranked_idx[:top_k*2]:
            score = combined_scores[idx]
            if idx < num_products:
                p = self.products[idx]
                score *= self._metadata_boost(p, query)
                products.append({**p, "score": float(score)})
            else:
                f = self.faqs[idx - num_products]
                faqs.append({**f, "score": float(score)})

        result = {
            "products": sorted(products, key=lambda x:x["score"], reverse=True)[:top_k],
            "faqs": sorted(faqs, key=lambda x:x["score"], reverse=True)[:top_k]
        }

        if conversation_id:
            self._update_memory(conversation_id, query, result)

        return result



