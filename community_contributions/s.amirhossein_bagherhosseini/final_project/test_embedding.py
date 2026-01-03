from rag import embed_texts

texts = [
    "گوشی سامسونگ A55 گوشی میان رده موبایل",
    "لپتاپ گیمینگ"
]

vecs = embed_texts(texts)
print("SHAPE:", vecs.shape)
print(vecs[0][:10])
