import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai

from .menu_catalog import MENU_CATALOG
from .order_logger import (
    CustomerOrder,
    OrderItem,
    append_order,
    format_order_message,
    google_sheet_configured,
)
from .rag_engine import RAGEngine
from .telegram_report import (
    send_order_notification,
    telegram_configured,
)


load_dotenv()

MODEL = "gemini-3.1-flash-lite-preview"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
KB_PATH = PROJECT_ROOT / "data" / "knowledge" / "lomwong_cafe_kb.txt"


def answer_common_question(prompt: str) -> str | None:
    question = prompt.strip().lower()
    asks_time = any(word in question for word in ["เวลาเปิด", "เปิดกี่โมง", "ปิดกี่โมง", "กี่โมง"])
    asks_contact = any(word in question for word in ["ช่องทางติดต่อ", "ติดต่อ", "เบอร์", "โทร", "facebook", "เฟส"])

    if asks_time and asks_contact:
        return (
            "Lom Wong Café & Restaurant เปิดทุกวัน เวลา 17:00-00:00 น. ครับ\n\n"
            "ช่องทางติดต่อ:\n"
            "- โทร: 062 275 8148 หรือ 062 015 2279\n"
            "- Facebook: https://web.facebook.com/profile.php?id=61584912115591"
        )

    if asks_time:
        return "Lom Wong Café & Restaurant เปิดทุกวัน เวลา 17:00-00:00 น. ครับ"

    if asks_contact:
        return (
            "ช่องทางติดต่อของร้านครับ\n\n"
            "- โทร: 062 275 8148 หรือ 062 015 2279\n"
            "- Facebook: https://web.facebook.com/profile.php?id=61584912115591"
        )

    if any(word in question for word in ["ที่อยู่", "อยู่ไหน", "อยู่ที่ไหน", "แผนที่", "location"]):
        return "ร้านอยู่เยื้อง ๆ กับ ปตท. บ.แวงใหญ่ อ.แวงใหญ่ จ.ขอนแก่น 40330 ครับ"

    if any(word in question for word in ["wifi", "wi-fi", "ไวไฟ"]):
        return "ร้านมี Wi-Fi สำหรับลูกค้าครับ"

    if any(word in question for word in ["delivery", "เดลิเวอรี่", "ส่งไหม", "ส่งได้ไหม"]):
        return "ตอนนี้ยังไม่มีบริการ delivery ผ่านแพลตฟอร์มประจำครับ รับ walk-in, pre-order และสอบถามการสั่งจองได้ทาง Facebook หรือโทรศัพท์"

    return None


@st.cache_resource
def load_rag():
    return RAGEngine(str(KB_PATH))


def generate_answer(prompt: str, context: str) -> str:
    direct_answer = answer_common_question(prompt)
    if direct_answer:
        return direct_answer

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "ยังไม่ได้ตั้งค่า GOOGLE_API_KEY หรือ GEMINI_API_KEY ใน Secrets หรือไฟล์ .env ครับ"

    client = genai.Client(api_key=api_key)
    full_prompt = f"""คุณคือโมจิ ผู้ช่วย AI ของร้าน Lom Wong Café & Restaurant
ตอบเป็นภาษาไทยให้กระชับ สุภาพ และตอบเฉพาะจากข้อมูลร้านด้านล่างเท่านั้น
ถ้าไม่พบข้อมูล ให้ตอบว่าไม่ทราบจากข้อมูลร้านที่มี และแนะนำให้ติดต่อร้านโดยตรง

ข้อมูลร้าน:
{context}

คำถาม: {prompt}
"""
    for attempt in range(3):
        try:
            response = client.models.generate_content(model=MODEL, contents=full_prompt)
            return response.text
        except Exception as exc:
            error_text = str(exc)
            if "quota" in error_text.lower() or "RESOURCE_EXHAUSTED" in error_text:
                time.sleep(2**attempt)
                continue
            return (
                "ระบบ AI มีปัญหาชั่วคราวครับ แต่ข้อมูลที่เกี่ยวข้องจากร้านคือ:\n\n"
                f"{context}"
            )

    return "ตอนนี้ระบบถูกจำกัดจำนวนการใช้งานชั่วคราวครับ กรุณาลองใหม่อีกครั้งภายหลัง"


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #111110;
            --bg2: #1a1a18;
            --bg3: #222220;
            --border: #333330;
            --border2: #444440;
            --txt: #f0ede8;
            --txt2: #a09d98;
            --txt3: #666360;
            --accent: #D85A30;
        }

        .stApp {
            background: var(--bg);
            color: var(--txt);
        }

        .block-container {
            max-width: 960px;
            padding-top: 1.5rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3, label, p {
            letter-spacing: 0;
        }

        .brand-hero {
            border: 0.5px solid var(--border);
            border-radius: 12px;
            background: var(--bg2);
            display: grid;
            grid-template-columns: minmax(0, 1fr) 76px;
            gap: 1rem;
            align-items: center;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }

        .brand-mark {
            width: 64px;
            aspect-ratio: 1;
            border-radius: 12px;
            justify-self: end;
            display: grid;
            place-items: center;
            background: var(--bg3);
            border: 0.5px solid var(--border2);
        }

        .brand-mark-inner {
            width: 52px;
            aspect-ratio: 1;
            border-radius: 8px;
            background: var(--bg2);
            color: var(--txt);
            display: grid;
            place-items: center;
            text-align: center;
            font-weight: 700;
            line-height: 1.05;
            letter-spacing: 0;
            border: 0.5px solid var(--border);
        }

        .brand-mark-main {
            display: block;
            font-size: 0.82rem;
        }

        .brand-mark-sub {
            display: block;
            color: var(--txt3);
            font-size: 0.45rem;
            margin-top: 0.12rem;
        }

        .brand-kicker {
            color: var(--txt3);
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .brand-title {
            color: var(--txt);
            font-size: clamp(1.55rem, 3.6vw, 2.25rem);
            font-weight: 500;
            line-height: 1.2;
            letter-spacing: 0;
            margin: 0;
        }

        .brand-subtitle {
            color: var(--txt2);
            font-size: 14px;
            line-height: 1.55;
            max-width: 720px;
            margin: 0.55rem 0 0;
        }

        .brand-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.8rem;
        }

        .brand-pill {
            border: 0.5px solid var(--border2);
            border-radius: 8px;
            color: var(--txt2);
            background: var(--bg3);
            font-size: 12px;
            font-weight: 500;
            padding: 0.32rem 0.58rem;
            white-space: nowrap;
        }

        .section-label {
            color: var(--txt3);
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .section-title {
            color: var(--txt);
            font-size: 22px;
            font-weight: 500;
            line-height: 1.25;
            margin: 0;
        }

        .section-copy,
        .order-note {
            color: var(--txt2);
            font-size: 14px;
            line-height: 1.55;
            margin: 0.4rem 0 1rem;
        }

        [data-testid="stTabs"] [role="tablist"] {
            gap: 0.45rem;
            border-bottom: 0.5px solid var(--border);
        }

        [data-testid="stTabs"] [role="tab"] {
            border-radius: 8px 8px 0 0;
            color: var(--txt2);
            padding: 0.55rem 0.95rem;
        }

        [data-testid="stTabs"] [aria-selected="true"] {
            color: var(--txt);
            background: var(--bg2);
        }

        [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            background-color: var(--border2);
        }

        div[data-testid="stForm"],
        .stDataFrame,
        [data-testid="stAlert"] {
            border-radius: 12px;
        }

        [data-testid="stMetric"] {
            background: var(--bg3);
            border: 0.5px solid var(--border2);
            border-radius: 12px;
            padding: 0.85rem 0.95rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--bg2);
            border: 0.5px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
        }

        div[data-testid="stForm"] {
            border: 0.5px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            background: var(--bg2);
        }

        .stSelectbox [data-baseweb="select"],
        .stNumberInput input,
        .stTextInput input,
        .stTextArea textarea {
            background-color: var(--bg3);
            border: 0.5px solid var(--border2);
            border-radius: 8px;
            color: var(--txt);
            font-size: 14px;
            min-height: 40px;
        }

        .stNumberInput input {
            min-height: 30px;
            height: 30px;
            padding: 0 0.25rem;
            text-align: center;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: var(--txt3);
        }

        label,
        [data-testid="stWidgetLabel"] p {
            color: var(--txt2);
            font-size: 12px;
            font-weight: 500;
        }

        .stSelectbox [data-baseweb="select"] * {
            color: var(--txt);
        }

        [data-baseweb="popover"],
        [data-baseweb="menu"] {
            background: var(--bg3);
            color: var(--txt);
        }

        [data-baseweb="menu"] li {
            color: var(--txt);
        }

        [data-testid="stMarkdownContainer"],
        [data-testid="stText"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {
            color: var(--txt);
        }

        .stNumberInput button {
            background: var(--bg3);
            border-color: var(--border2);
            color: var(--txt);
        }

        [data-testid="stAlert"] {
            background: var(--bg3);
            border: 0.5px solid var(--border2);
            color: var(--txt2);
        }

        [data-testid="stAlert"] p {
            color: var(--txt2);
        }

        .stButton > button,
        .stFormSubmitButton > button,
        div[data-testid="stBaseButton-secondary"] button {
            border-radius: 8px;
            border: 0.5px solid var(--border2);
            background: var(--bg3);
            color: var(--txt);
            font-weight: 500;
            min-height: 40px;
            font-size: 14px;
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"] {
            border: 0.5px solid var(--accent);
            background: var(--accent);
            color: #ffffff;
            font-weight: 600;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            border-color: var(--txt3);
            background: var(--bg3);
            color: var(--txt);
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover {
            border-color: var(--accent);
            background: var(--accent);
            color: #ffffff;
        }

        .qty-control button,
        div[data-testid="column"]:has(.qty-control) button {
            min-height: 30px;
            height: 30px;
            padding: 0;
            border-radius: 8px;
            background: var(--bg3);
            border: 0.5px solid var(--border2);
            color: var(--txt);
        }

        .qty-label {
            color: var(--txt2);
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 0.35rem;
        }

        div[data-testid="stChatMessage"] {
            border: 0.5px solid var(--border);
            border-radius: 12px;
            background: var(--bg2);
            padding: 0.72rem 0.85rem;
        }

        [data-testid="stDataFrame"],
        [data-testid="stCodeBlock"] {
            border: 0.5px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }

        hr {
            border: 0;
            border-top: 0.5px solid var(--border);
            margin: 1.6rem 0;
        }

        .empty-cart {
            border: 0.5px solid var(--border2);
            border-radius: 8px;
            background: var(--bg3);
            padding: 2rem 1rem;
            text-align: center;
            color: var(--txt3);
        }

        .empty-cart-icon {
            width: 42px;
            height: 42px;
            margin: 0 auto 0.75rem;
            border-radius: 8px;
            display: grid;
            place-items: center;
            background: var(--bg2);
            border: 0.5px solid var(--border2);
            color: var(--txt2);
            font-size: 20px;
            font-weight: 600;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1.1rem;
            }

            .brand-hero {
                grid-template-columns: 1fr;
                padding: 1rem;
            }

            .brand-mark {
                width: 68px;
                justify-self: start;
                order: -1;
            }

            .brand-mark-inner {
                width: 56px;
            }

            .brand-mark-main {
                font-size: 0.9rem;
            }

            .brand-title {
                font-size: 1.7rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header() -> None:
    st.markdown(
        f"""
        <section class="brand-hero">
            <div>
                <div class="brand-kicker">Lom Wong Café & Restaurant</div>
                <h1 class="brand-title">โมจิ ผู้ช่วยของล้อมวง</h1>
                <p class="brand-subtitle">
                    ถามข้อมูลร้าน ดูเมนู และจัดรายการสั่งอาหารได้ในที่เดียว
                    โทนคำตอบกระชับ สุภาพ และอ้างอิงจากข้อมูลของร้าน
                </p>
                <div class="brand-meta">
                    <span class="brand-pill">เปิดทุกวัน 17:00-00:00</span>
                    <span class="brand-pill">แวงใหญ่ ขอนแก่น</span>
                    <span class="brand-pill">Walk-in และสั่งล่วงหน้า</span>
                </div>
            </div>
            <div class="brand-mark" aria-label="Lom Wong">
                <div class="brand-mark-inner">
                    <span class="brand-mark-main">ล้อมวง</span>
                    <span class="brand-mark-sub">LOM WONG</span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(label: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-label">{label}</div>
        <h2 class="section-title">{title}</h2>
        <p class="section-copy">{copy}</p>
        """,
        unsafe_allow_html=True,
    )


def cart_total() -> float:
    return sum(item["quantity"] * item["unit_price"] for item in st.session_state.order_cart)


def add_to_cart(menu_name: str, quantity: int, unit_price: float, note: str) -> None:
    st.session_state.order_cart.append(
        {
            "menu": menu_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total": quantity * unit_price,
            "note": note.strip(),
        }
    )


def adjust_order_quantity(delta: int) -> None:
    current_quantity = int(st.session_state.get("order_quantity", 1))
    st.session_state.order_quantity = min(50, max(1, current_quantity + delta))


def render_chat_tab() -> None:
    rag = load_rag()
    render_section_header(
        "Ask Moji",
        "ถามข้อมูลร้าน",
        "ถามเวลาเปิด ที่ตั้ง เมนูแนะนำ หรือข้อมูลติดต่อของร้านได้เลย",
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("ถามอะไรเกี่ยวกับร้านได้เลย..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        context_chunks = rag.search(prompt, top_k=3)
        context = "\n---\n".join(context_chunks)
        answer = generate_answer(prompt, context)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)


def render_order_tab() -> None:
    if "order_cart" not in st.session_state:
        st.session_state.order_cart = []
    if "order_quantity" not in st.session_state:
        st.session_state.order_quantity = 1

    render_section_header(
        "ORDER",
        "สั่งอาหาร",
        "เลือกเมนู ใส่จำนวน แล้วกดเพิ่มลงรายการ ระบบจะสรุปยอดและบันทึกลง Google Sheets เมื่อยืนยันออเดอร์",
    )

    with st.container(border=True):
        col_category, col_menu, col_quantity = st.columns([1, 1, 1])
        category = col_category.selectbox("หมวดหมู่", list(MENU_CATALOG), key="order_category")
        category_items = MENU_CATALOG[category]
        item_labels = [f"{item['name']} - {item['price']} บาท" for item in category_items]
        selected_label = col_menu.selectbox("เมนู", item_labels, key=f"order_menu_{category}")
        selected_index = item_labels.index(selected_label)
        selected_item = category_items[selected_index]

        with col_quantity:
            st.markdown('<div class="qty-control qty-label">จำนวน</div>', unsafe_allow_html=True)
            qty_minus, qty_value, qty_plus = st.columns(3)
            qty_minus.button(
                "−",
                key="qty_minus",
                on_click=adjust_order_quantity,
                args=(-1,),
                use_container_width=True,
            )
            quantity = qty_value.number_input(
                "จำนวน",
                min_value=1,
                max_value=50,
                step=1,
                key="order_quantity",
                label_visibility="collapsed",
            )
            qty_plus.button(
                "+",
                key="qty_plus",
                on_click=adjust_order_quantity,
                args=(1,),
                use_container_width=True,
            )

        item_note = st.text_input("หมายเหตุรายการนี้", placeholder="เช่น ไม่เผ็ด แยกน้ำ ไม่ใส่ผัก", key="item_note")
        add_item = st.button("เพิ่มลงออเดอร์", type="primary", use_container_width=True, key="add_to_order")

    if add_item:
        add_to_cart(
            menu_name=str(selected_item["name"]),
            quantity=int(quantity),
            unit_price=float(selected_item["price"]),
            note=item_note,
        )
        st.success(f"เพิ่ม {selected_item['name']} x {quantity} แล้ว")

    st.divider()
    render_section_header("CART", "รายการที่เลือก", "ตรวจรายการและยอดรวมก่อนกรอกข้อมูลลูกค้า")
    with st.container(border=True):
        if not st.session_state.order_cart:
            st.markdown(
                """
                <div class="empty-cart">
                    <div class="empty-cart-icon">＋</div>
                    <div>ยังไม่มีรายการอาหารในออเดอร์</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.dataframe(st.session_state.order_cart, use_container_width=True, hide_index=True)
            metric_cols = st.columns(3)
            metric_cols[0].metric("จำนวนรายการ", len(st.session_state.order_cart))
            metric_cols[1].metric("จำนวนชิ้น", sum(item["quantity"] for item in st.session_state.order_cart))
            metric_cols[2].metric("ยอดรวม", f"{cart_total():.0f} บาท")

            clear_col, _ = st.columns([1, 3])
            if clear_col.button("ล้างรายการ", use_container_width=True):
                st.session_state.order_cart = []
                st.rerun()

    st.divider()
    render_section_header("CUSTOMER", "ข้อมูลลูกค้า", "ใส่ข้อมูลสำหรับติดต่อกลับและรูปแบบการรับออเดอร์")
    with st.form("confirm_order_form"):
        col_name, col_phone = st.columns(2)
        customer_name = col_name.text_input("ชื่อผู้สั่ง")
        phone = col_phone.text_input("เบอร์โทร")
        fulfillment = st.selectbox("รูปแบบออเดอร์", ["รับหน้าร้าน", "จองโต๊ะ/สั่งล่วงหน้า"])
        order_note = st.text_area("หมายเหตุออเดอร์", placeholder="เช่น รับประมาณ 18:30 น. หรือขอโต๊ะ 4 คน")
        submitted = st.form_submit_button("ยืนยันออเดอร์", type="primary", use_container_width=True)

    if not google_sheet_configured():
        st.warning(
            "ยังไม่ได้ตั้งค่า GOOGLE_SHEET_ID และ GOOGLE_SERVICE_ACCOUNT_JSON ใน Hugging Face Secrets "
            "ตอนนี้ระบบจะสรุปออเดอร์ให้ แต่ยังไม่บันทึกลง Google Sheets"
        )
    if submitted:
        if not st.session_state.order_cart:
            st.error("กรุณาเพิ่มเมนูก่อนยืนยันออเดอร์")
            return
        if not customer_name.strip() or not phone.strip():
            st.error("กรุณาใส่ชื่อผู้สั่งและเบอร์โทร")
            return

        order = CustomerOrder(
            customer_name=customer_name,
            phone=phone,
            fulfillment=fulfillment,
            note=order_note.strip(),
            items=[
                OrderItem(
                    menu=item["menu"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    note=item.get("note", ""),
                )
                for item in st.session_state.order_cart
            ],
        )
        message = format_order_message(order)

        if google_sheet_configured():
            try:
                result = append_order(order)
                st.success(f"บันทึกออเดอร์ {result['order_id']} แล้ว ยอดรวม {result['total']:.0f} บาท")
                if telegram_configured():
                    try:
                        send_order_notification(order, order_id=str(result["order_id"]))
                        st.success("ส่งแจ้งเตือนออเดอร์เข้า Telegram แล้ว")
                    except Exception as exc:
                        st.warning(f"บันทึกออเดอร์แล้ว แต่ส่ง Telegram ไม่สำเร็จ: {exc}")
                st.session_state.order_cart = []
            except Exception as exc:
                st.error(f"บันทึกลง Google Sheets ไม่สำเร็จ: {exc}")
                st.info("ยังสามารถใช้ข้อความด้านล่างส่งให้ร้านได้")
        else:
            st.info("คัดลอกข้อความนี้ส่งให้ร้านทาง Facebook หรือโทรแจ้งร้านได้")

        st.code(message, language="text")


def main() -> None:
    st.set_page_config(
        page_title="โมจิ | Lom Wong Café & Restaurant",
        page_icon="LW",
        layout="centered",
    )
    inject_styles()
    render_brand_header()

    chat_tab, order_tab = st.tabs(["ถามโมจิ", "สั่งอาหาร"])

    with chat_tab:
        render_chat_tab()

    with order_tab:
        render_order_tab()


if __name__ == "__main__":
    main()
