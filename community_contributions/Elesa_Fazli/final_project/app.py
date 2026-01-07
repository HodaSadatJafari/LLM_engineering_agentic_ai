import json
import os
from typing import Dict, List, Optional, Tuple

import gradio as gr
import gradio.blocks as gr_blocks
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from modules.intent import detect_intent as heuristic_intent

load_dotenv()

FAQ_PATH = os.path.join("data", "faqs.json")
PRODUCTS_PATH = os.path.join("data", "products.json")

# Monkeypatch: avoid Gradio API schema generation that crashes on complex states
gr_blocks.Blocks.get_api_info = lambda self, *_, **__: {"named_endpoints": {}, "unnamed_endpoints": []}

# Optional OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Warning: OPENAI_API_KEY not set; LLM fallback will be limited.")
    client = None
else:
    client = OpenAI(api_key=openai_api_key)


# ---------- Data loading ----------
def safe_load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[warn] Cannot load {path}: {exc}")
        return default


faq_data = safe_load_json(FAQ_PATH, [])
products_data = safe_load_json(PRODUCTS_PATH, [])

brand_names = {p.get("brand", "").lower() for p in products_data if p.get("brand")}
brand_keywords = brand_names | {
    "lenovo",
    "dell",
    "hp",
    "asus",
    "acer",
    "msi",
    "apple",
    "huawei",
    "xiaomi",
    "samsung",
    "lg",
    "microsoft",
    "razer",
    "sony",
}

# --------- Intent detection helpers ----------
def llm_intent(message: str) -> Optional[str]:
    """Use LLM (if available) to classify intent among a fixed set."""
    if client is None:
        return None
    prompt = (
        "Classify user intent into one of: product_info, order, payment, shipping, warranty, faq, chit_chat, other.\n"
        f"User message: {message}\n"
        "Return only the intent label."
    )
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5,
        )
        label = res.choices[0].message.content.strip().lower()
        return label
    except Exception:
        return None


def determine_intent(message: str) -> str:
    """Hybrid intent detection: LLM if available, else heuristic keywords."""
    label = llm_intent(message)
    if label:
        return label

    base, _ = heuristic_intent(message)
    if base in ("order", "product_info"):
        return base

    t = message.lower()
    shipping_terms = ["ship", "shipping", "delivery", "deliver", "ارسال", "تحویل", "پست", "دریافت", "حمل", "دریا", "کشتی"]
    time_terms = ["how long", "چه مدت", "چقدر", "زمان", "مدت", "کی", "when", "رسیدن", "میاد", "می رسد", "برسه"]
    payment_terms = ["پرداخت", "payment", "pay", "method", "card", "کارت", "درگاه", "pos", "wallet", "کیف پول"]
    warranty_terms = ["گارانتی", "ضمانت", "warranty", "return", "مرجوع", "تعویض"]

    if any(term in t for term in shipping_terms) and any(term in t for term in time_terms):
        return "shipping"
    if any(term in t for term in payment_terms):
        return "payment"
    if any(term in t for term in warranty_terms):
        return "warranty"
    return "general"



# ---------- Index builders ----------
def build_faq_index(faq_items):
    questions = [item.get("question", "") for item in faq_items if item.get("question")]
    answers = [item.get("answer", "") for item in faq_items if item.get("question")]
    if not questions:
        return {"vectorizer": None, "vectors": None, "questions": [], "answers": []}
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(questions)
    return {"vectorizer": vectorizer, "vectors": vectors, "questions": questions, "answers": answers}


def product_text(product: Dict) -> str:
    parts = [
        product.get("title", ""),
        product.get("description", ""),
        product.get("category", ""),
        product.get("brand", ""),
        " ".join(product.get("tags", [])),
    ]
    return " ".join(parts)


def build_product_index(products: List[Dict]):
    docs = [product_text(p) for p in products]
    if not docs:
        return {"vectorizer": None, "matrix": None}
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(docs)
    return {"vectorizer": vectorizer, "matrix": matrix}


faq_index = build_faq_index(faq_data)
product_index = build_product_index(products_data)


# ---------- PDF helpers ----------
def chunk_text(text: str, size: int = 800, overlap: int = 120) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + size)
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def extract_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages)


def build_pdf_state(chunks: List[Dict]) -> Dict:
    if not chunks:
        return {"chunks": [], "vectorizer": None, "matrix": None}
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([c["text"] for c in chunks])
    return {"chunks": chunks, "vectorizer": vectorizer, "matrix": matrix}


def search_pdf(query: str, pdf_state: Dict, top_k: int = 1, threshold: float = 0.12) -> Optional[Dict]:
    vectorizer = pdf_state.get("vectorizer")
    matrix = pdf_state.get("matrix")
    chunks = pdf_state.get("chunks", [])
    if not vectorizer or matrix is None or not chunks:
        return None
    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, matrix).flatten()
    if scores.size == 0:
        return None
    idx = scores.argmax()
    if scores[idx] < threshold:
        return None
    top = chunks[idx]
    return {**top, "score": float(scores[idx])}


def append_error(errors: List[str], message: str, max_len: int = 6) -> List[str]:
    new_errors = errors + [message]
    if len(new_errors) > max_len:
        new_errors = new_errors[-max_len:]
    return new_errors


# ---------- Retrieval ----------
def search_faq(query: str, threshold: float = 0.25) -> Optional[Dict]:
    vectorizer = faq_index.get("vectorizer")
    vectors = faq_index.get("vectors")
    if not vectorizer or vectors is None:
        return None
    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, vectors).flatten()
    if scores.size == 0:
        return None
    idx = scores.argmax()
    if scores[idx] < threshold:
        return None
    return {
        "question": faq_index["questions"][idx],
        "answer": faq_index["answers"][idx],
        "score": float(scores[idx]),
    }


def search_products(query: str, top_k: int = 2, threshold: float = 0.12) -> List[Dict]:
    vectorizer = product_index.get("vectorizer")
    matrix = product_index.get("matrix")
    if not vectorizer or matrix is None:
        return []
    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, matrix).flatten()
    ranked = scores.argsort()[::-1]
    results = []
    for idx in ranked[:top_k]:
        score = float(scores[idx])
        if score < threshold:
            continue
        product = products_data[idx]
        results.append({**product, "score": score})
    return results


# ---------- Response builders ----------
def format_product(product: Dict) -> str:
    currency = product.get("currency", "USD")
    lines = [
        f"📦 {product.get('title', 'محصول')}",
        f"قیمت: {product.get('price', 'نامشخص')} {currency}",
        f"موجودی: {product.get('availability', 'نامشخص')} عدد",
        f"دسته‌بندی: {product.get('category', '-')}",
    ]
    desc = product.get("description")
    if desc:
        lines.append(f"توضیح کوتاه: {desc}")
    return "\n".join(lines)


def build_context(faq_hit: Optional[Dict], product_hits: List[Dict], pdf_hit: Optional[Dict]) -> str:
    parts = []
    if product_hits:
        parts.append("محصولات مرتبط:")
        for p in product_hits:
            parts.append(f"- {p.get('title')} | قیمت {p.get('price')} {p.get('currency','USD')} | {p.get('description','')}")
    if faq_hit:
        parts.append(f"FAQ: {faq_hit['question']} => {faq_hit['answer']}")
    if pdf_hit:
        parts.append(f"متن از PDF ({pdf_hit.get('source','pdf')}): {pdf_hit.get('text','')[:500]}")
    return "\n".join(parts)


def rule_based_response(message: str, product_hits: List[Dict]) -> Optional[str]:
    """Lightweight fallback for common intents when LLM یا FAQ پاسخ نداده."""
    t = message.lower()
    payment_keys = ["پرداخت", "payment", "pay", "method", "card", "کارت", "درگاه", "pos"]
    shipping_keys = ["ارسال", "delivery", "ship", "shipping", "پست", "دریافت", "حمل", "کشتی", "دریا", "sea"]
    shipping_time_keys = ["how long", "چه مدت", "چقدر", "زمان", "مدت", "when", "reach", "رسیدن", "میاد", "برسه"]
    warranty_keys = ["گارانتی", "ضمانت", "warranty", "return", "مرجوع", "تعویض"]

    if any(k in t for k in payment_keys):
        return (
            "روش‌های پرداخت ما: پرداخت آنلاین با کارت بانکی (درگاه امن)، واریز بانکی، "
            "و در صورت توافق سازمانی، پرداخت فاکتور. پرداخت در محل فعلاً نداریم."
        )
    if any(k in t for k in shipping_keys) and any(k in t for k in shipping_time_keys):
        return "ارسال به تمام شهرها انجام می‌شود؛ زمان تقریبی ۲ تا ۷ روز کاری با کد رهگیری. هزینه بسته به مقصد متفاوت است."
    if any(k in t for k in warranty_keys):
        return "همه کالاهای اصلی با گارانتی رسمی عرضه می‌شوند. مهلت تست ۷ روز تقویمی داریم؛ مرجوع در صورت خرابی یا مغایرت."

    # Brand asked but محصولی برنگشته
    if not product_hits:
        brand_hit = next((b for b in brand_keywords if b and b in t), None)
        if brand_hit:
            if brand_hit in brand_names:
                return f"مدل دقیقی از {brand_hit} پیدا نکردم؛ لطفاً سری یا مشخصات دقیق‌تر را بگویید."
            return f"در حال حاضر کالایی از برند «{brand_hit}» در موجودی ثبت نشده است."
    return None


def ask_llm(prompt: str, context: str) -> Tuple[Optional[str], Optional[str]]:
    if client is None:
        return None, "OPENAI_API_KEY تنظیم نشده است."
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful support agent. Answer briefly and clearly in Persian."},
                {"role": "user", "content": f"پرسش کاربر: {prompt}\nاطلاعات زمینه:\n{context}\nپاسخ:"},
            ],
            temperature=0.4,
        )
        return res.choices[0].message.content.strip(), None
    except Exception as exc:
        return None, f"LLM error: {exc}"


def render_status(info_lines: List[str], errors: List[str], pdf_state: Dict) -> str:
    pdf_count = len(pdf_state.get("chunks", [])) if pdf_state else 0
    status_lines = ["### وضعیت جستجو و بارگذاری"]
    if info_lines:
        status_lines += [f"- {line}" for line in info_lines]
    else:
        status_lines.append("- هنوز نتیجه‌ای ثبت نشده است.")

    status_lines.append(f"- تعداد بخش‌های PDF: {pdf_count}")

    if errors:
        status_lines.append("### خطاها")
        status_lines += [f"- ⚠️ {e}" for e in errors[-5:]]
    return "\n".join(status_lines)


def generate_reply(message: str, pdf_state: Dict, errors: List[str]) -> Tuple[str, Dict, List[str], str]:
    info_lines: List[str] = []
    intent = determine_intent(message)
    faq_hit = search_faq(message)
    if faq_hit:
        info_lines.append(f"FAQ ({faq_hit['score']:.2f}): {faq_hit['question']}")

    product_hits = search_products(message, top_k=3)
    if product_hits:
        info_lines.append(f"محصول مرتبط: {product_hits[0]['title']} (امتیاز {product_hits[0]['score']:.2f})")

    pdf_hit = search_pdf(message, pdf_state)
    if pdf_hit:
        info_lines.append(f"یافته از PDF «{pdf_hit.get('source','pdf')}» (امتیاز {pdf_hit['score']:.2f})")

    # Intent-aware routing
    if intent == "faq" and faq_hit:
        status = render_status(info_lines, errors, pdf_state)
        return faq_hit["answer"], pdf_state, errors, status

    if intent in ("product_info", "order"):
        if product_hits:
            status = render_status(info_lines, errors, pdf_state)
            return format_product(product_hits[0]), pdf_state, errors, status
        rb = rule_based_response(message, product_hits)
        if rb:
            status = render_status(info_lines, errors, pdf_state)
            return rb, pdf_state, errors, status

    if intent == "shipping":
        if faq_hit:
            status = render_status(info_lines, errors, pdf_state)
            return faq_hit["answer"], pdf_state, errors, status
        rb = rule_based_response(message, product_hits)
        if rb:
            status = render_status(info_lines, errors, pdf_state)
            return rb, pdf_state, errors, status

    if intent == "payment":
        rb = rule_based_response(message, product_hits)
        if rb:
            status = render_status(info_lines, errors, pdf_state)
            return rb, pdf_state, errors, status

    if intent == "warranty":
        rb = rule_based_response(message, product_hits)
        if rb:
            status = render_status(info_lines, errors, pdf_state)
            return rb, pdf_state, errors, status

    # General fallbacks
    if faq_hit:
        status = render_status(info_lines, errors, pdf_state)
        return faq_hit["answer"], pdf_state, errors, status

    if product_hits:
        status = render_status(info_lines, errors, pdf_state)
        return format_product(product_hits[0]), pdf_state, errors, status

    if pdf_hit:
        snippet = pdf_hit.get("text", "")[:800]
        status = render_status(info_lines, errors, pdf_state)
        return f"بخشی از PDF «{pdf_hit.get('source','pdf')}»:\n{snippet}", pdf_state, errors, status

    rb = rule_based_response(message, product_hits)
    if rb:
        status = render_status(info_lines, errors, pdf_state)
        return rb, pdf_state, errors, status

    # LLM fallback with context
    context = build_context(faq_hit, product_hits, pdf_hit)
    llm_answer, llm_error = ask_llm(message, context)
    if llm_error:
        errors = append_error(errors, llm_error)
    status = render_status(info_lines, errors, pdf_state)
    if llm_answer:
        return llm_answer, pdf_state, errors, status
    return "فعلا نمی‌توانم پاسخ بدهم؛ لطفا بعدا دوباره امتحان کنید.", pdf_state, errors, status


# ---------- Gradio callbacks ----------
def handle_chat(message: str, history: List[Tuple[str, str]], pdf_state: Dict, errors: List[str]):
    if not message or not message.strip():
        return history, pdf_state, errors, render_status([], errors, pdf_state)
    try:
        reply, pdf_state, errors, status = generate_reply(message, pdf_state, errors)
    except Exception as exc:
        errors = append_error(errors, f"chat error: {exc}")
        reply = "مشکلی پیش آمد، لطفا دوباره امتحان کنید."
        status = render_status([], errors, pdf_state)
    history = history + [(message, reply)]
    return history, pdf_state, errors, status


def handle_pdf_upload(files, pdf_state: Dict, errors: List[str], history: List[Tuple[str, str]]):
    if files is None:
        return pdf_state, errors, render_status([], errors, pdf_state), history
    if not isinstance(files, list):
        files = [files]
    chunks = pdf_state.get("chunks", []).copy()
    added = 0
    for f in files:
        try:
            pdf_text = extract_pdf_text(f.name)
            pdf_chunks = chunk_text(pdf_text)
            if not pdf_chunks:
                errors = append_error(errors, f"PDF {os.path.basename(f.name)} خالی بود یا خوانده نشد.")
                continue
            for chunk in pdf_chunks:
                chunks.append({"text": chunk, "source": os.path.basename(f.name)})
            added += 1
        except Exception as exc:
            errors = append_error(errors, f"PDF {os.path.basename(f.name)}: {exc}")
    new_state = build_pdf_state(chunks)
    note = f"{added} فایل PDF اضافه شد." if added else "PDF جدیدی اضافه نشد."
    history = history + [("📄 بارگذاری فایل", note)]
    status = render_status([note], errors, new_state)
    return new_state, errors, status, history


def clear_chat():
    return [], {"chunks": [], "vectorizer": None, "matrix": None}, [], "### وضعیت جستجو و بارگذاری\n- هنوز نتیجه‌ای ثبت نشده است.\n- تعداد بخش‌های PDF: 0"


# ---------- UI ----------
custom_css = """
.gradio-container {background: radial-gradient(circle at 20% 20%, #f2f6ff, #eef4ff 45%, #f9fbff);}
* {font-family: 'DM Sans', 'Segoe UI', system-ui, sans-serif;}
.chatbot {min-height: 450px;}
#status-panel {border: 1px solid #e1e7ff; background: #f8faff; padding: 12px; border-radius: 12px;}
"""

with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.Markdown("## 🤝 پشتیبانی مشتری | جستجوی FAQ، محصولات و PDF", elem_id="title")
    gr.Markdown(
        "پیام خود را بفرستید. ابتدا FAQ و محصولات جستجو می‌شود، سپس (در صورت وجود) متن PDF و در نهایت مدل زبانی پاسخ می‌دهد. "
        "اگر کلید OpenAI تنظیم نشده باشد فقط جستجوهای محلی انجام می‌شود."
    )

    pdf_state = gr.State({"chunks": [], "vectorizer": None, "matrix": None})
    error_state = gr.State([])

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="گفتگو", height=480)
            with gr.Row():
                msg = gr.Textbox(
                    label="پیام",
                    placeholder="مثال: قیمت X1000 Laptop 14 چقدر است؟",
                    scale=5,
                )
                send_btn = gr.Button("ارسال", variant="primary", scale=1)
            clear_btn = gr.Button("پاک کردن گفتگو")
        with gr.Column(scale=2):
            upload = gr.File(label="بارگذاری PDF (چند فایل)", file_types=[".pdf"], file_count="multiple")
            status_md = gr.Markdown(render_status([], [], {"chunks": []}), elem_id="status-panel")

    send_btn.click(
        handle_chat,
        inputs=[msg, chatbot, pdf_state, error_state],
        outputs=[chatbot, pdf_state, error_state, status_md],
    )
    msg.submit(
        handle_chat,
        inputs=[msg, chatbot, pdf_state, error_state],
        outputs=[chatbot, pdf_state, error_state, status_md],
    )

    upload.upload(
        handle_pdf_upload,
        inputs=[upload, pdf_state, error_state, chatbot],
        outputs=[pdf_state, error_state, status_md, chatbot],
        queue=False,
    )

    clear_btn.click(
        clear_chat,
        outputs=[chatbot, pdf_state, error_state, status_md],
    )

if __name__ == "__main__":
    # show_api=False avoids gradio schema inspection that can fail on complex States.
    demo.launch(share=True, show_api=False, server_name="0.0.0.0")
