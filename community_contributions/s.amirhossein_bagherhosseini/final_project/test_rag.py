from rag import search_products

queries = [
    "گوشی",
    "گوشی سامسونگ",
    "موبایل",
    "لپتاپ",
    "لپتاپ گیمینگ"
]

for q in queries:
    results = search_products(q)
    print("=" * 40)
    print("QUERY:", q)
    print("RESULTS:", results)
