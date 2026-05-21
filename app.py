import os
import time

import streamlit as st
from dotenv import load_dotenv
from google import genai

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
        return "ร้านอยู่ที่ 140 ตำบล ห้วยแก อำเภอ ชนบท ขอนแก่น 40180 ครับ"

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


st.title("โมจิ ผู้ช่วย AI ของ Lom Wong Café & Restaurant")
st.caption("ถามเรื่องเมนู เวลาเปิด ความหวาน หรือข้อมูลร้านได้เลย")

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
