# MilkLab° AI — Demi RAG Chatbot

Template สำหรับ Session 3 ของคอร์ส STSW

## วิธีเริ่ม

1. กด **Use this template** ด้านบน → Create a new repository (public)
2. เปิด repo ใหม่ของคุณ → Code → Codespaces → Create codespace
3. รอ container build เสร็จ (~1–3 นาที)
4. เขียน `rag_engine.py` และ `app.py` ตามคู่มือ Session 3
5. รัน `streamlit run app.py` เพื่อทดสอบ

## โครงสร้างที่เตรียมไว้ให้

- `.devcontainer/devcontainer.json` — Python 3.11 + Copilot + Pylance
- `requirements.txt` — streamlit, sentence-transformers, faiss-cpu, google-genai
- `knowledge/milklab_kb.txt` — knowledge base ตัวอย่างของร้าน MilkLab°
- `.gitignore` — กัน `.env` และ credential หลุดขึ้น GitHub

## ไฟล์ที่ต้องเขียนเอง

- `rag_engine.py` — RAG pipeline 5 ขั้น (Load → Chunk → Embed → Search → Generate)
- `app.py` — Streamlit UI + เรียก Gemini API
- `.env` — เก็บ `GOOGLE_API_KEY` (อย่า commit ขึ้น GitHub)

ดูคู่มือเต็มที่  https://ecp-rmuti.gitbook.io/ai-for-solopreneurs/sessions/session-3 
