"""
Run this script ONCE to build FAISS indexes
------------------------------------------
python build_index.py
"""

from rag import build_and_save_indexes

if __name__ == "__main__":
    print("🔧 Building FAISS indexes...")
    build_and_save_indexes()
    print("✅ FAISS indexes created successfully.")
