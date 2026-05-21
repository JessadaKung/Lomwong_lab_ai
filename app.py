import os
import time

import streamlit as st
from dotenv import load_dotenv
from google import genai

from menu_catalog import MENU_CATALOG
from order_logger import CustomerOrder, OrderItem, append_order, format_order_message, google_sheet_configured
from rag_engine import RAGEngine


load_dotenv()

MODEL = "gemini-3.1-flash-lite-preview"
KB_PATH = "knowledge/lomwong_cafe_kb.txt"


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
    return RAGEngine(KB_PATH)


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
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 193, 7, 0.12), transparent 28rem),
                radial-gradient(circle at top right, rgba(239, 68, 68, 0.10), transparent 26rem),
                #0f1117;
        }
        [data-testid="stMetric"] {
            background: #171a22;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 0.7rem 0.9rem;
        }
        div[data-testid="stForm"] {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 1rem;
            background: rgba(23, 26, 34, 0.76);
        }
        .order-note {
            color: #c8cdd8;
            font-size: 0.95rem;
            margin-top: -0.35rem;
        }
        </style>
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


def render_chat_tab() -> None:
    rag = load_rag()

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

    st.subheader("สั่งอาหาร")
    st.markdown(
        '<div class="order-note">เลือกเมนู ใส่จำนวน แล้วกดเพิ่มลงรายการ ระบบจะสรุปยอดและบันทึกลง Google Sheets เมื่อยืนยันออเดอร์</div>',
        unsafe_allow_html=True,
    )

    with st.form("add_item_form", clear_on_submit=True):
        col_category, col_menu, col_quantity = st.columns([1.2, 2, 0.8])
        category = col_category.selectbox("หมวด", list(MENU_CATALOG))
        category_items = MENU_CATALOG[category]
        item_labels = [f"{item['name']} - {item['price']} บาท" for item in category_items]
        selected_label = col_menu.selectbox("เมนู", item_labels)
        selected_index = item_labels.index(selected_label)
        selected_item = category_items[selected_index]
        quantity = col_quantity.number_input("จำนวน", min_value=1, max_value=50, value=1, step=1)
        item_note = st.text_input("หมายเหตุรายการนี้", placeholder="เช่น ไม่เผ็ด แยกน้ำ ไม่ใส่ผัก")
        add_item = st.form_submit_button("เพิ่มลงรายการ", use_container_width=True)

    if add_item:
        add_to_cart(
            menu_name=str(selected_item["name"]),
            quantity=int(quantity),
            unit_price=float(selected_item["price"]),
            note=item_note,
        )
        st.success(f"เพิ่ม {selected_item['name']} x {quantity} แล้ว")

    st.divider()
    st.subheader("รายการที่เลือก")
    if not st.session_state.order_cart:
        st.info("ยังไม่มีรายการอาหารในออเดอร์")
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
    st.subheader("ข้อมูลลูกค้า")
    with st.form("confirm_order_form"):
        col_name, col_phone = st.columns(2)
        customer_name = col_name.text_input("ชื่อผู้สั่ง")
        phone = col_phone.text_input("เบอร์โทร")
        fulfillment = st.selectbox("รูปแบบออเดอร์", ["รับหน้าร้าน", "จองโต๊ะ/สั่งล่วงหน้า"])
        order_note = st.text_area("หมายเหตุออเดอร์", placeholder="เช่น รับประมาณ 18:30 น. หรือขอโต๊ะ 4 คน")
        submitted = st.form_submit_button("ยืนยันออเดอร์", use_container_width=True)

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
                st.session_state.order_cart = []
            except Exception as exc:
                st.error(f"บันทึกลง Google Sheets ไม่สำเร็จ: {exc}")
                st.info("ยังสามารถใช้ข้อความด้านล่างส่งให้ร้านได้")
        else:
            st.info("คัดลอกข้อความนี้ส่งให้ร้านทาง Facebook หรือโทรแจ้งร้านได้")

        st.code(message, language="text")


inject_styles()
st.title("โมจิ ผู้ช่วย AI ของ Lom Wong Café & Restaurant")
st.caption("ถามข้อมูลร้าน ดูเมนู หรือจัดรายการสั่งอาหารได้ในที่เดียว")

chat_tab, order_tab = st.tabs(["ถามโมจิ", "สั่งอาหาร"])

with chat_tab:
    render_chat_tab()

with order_tab:
    render_order_tab()
