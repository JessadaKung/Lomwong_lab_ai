import os

import streamlit as st
from dotenv import load_dotenv
from google import genai

from rag_engine import RAGEngine


load_dotenv()

MODEL = "gemini-2.5-flash"
KB_PATH = "knowledge/milklab_kb.txt"


@st.cache_resource
def load_rag():
    return RAGEngine(KB_PATH)


def generate_answer(prompt: str, context: str) -> str:
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "ยังไม่ได้ตั้งค่า GOOGLE_API_KEY ใน Secrets หรือไฟล์ .env ครับ"

    client = genai.Client(api_key=api_key)
    full_prompt = f"""คุณคือ Demi ผู้ช่วย AI ของร้าน Lomwong Cafe
ตอบเป็นภาษาไทยให้กระชับ สุภาพ และตอบเฉพาะจากข้อมูลร้านด้านล่างเท่านั้น
ถ้าไม่พบข้อมูล ให้ตอบว่าไม่ทราบจากข้อมูลร้านที่มี และแนะนำให้ติดต่อร้านโดยตรง

ข้อมูลร้าน:
{context}

คำถาม: {prompt}
"""
    response = client.models.generate_content(model=MODEL, contents=full_prompt)
    return response.text


st.title("Demi ผู้ช่วย AI ของ Lomwong Cafe")
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
