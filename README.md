---
title: Lomwong Cafe
emoji: ☕
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 8501
---

# Lom Wong Café & Restaurant AI — โมจิ RAG Chatbot

โมจิคือผู้ช่วย AI สำหรับ Lom Wong Café & Restaurant ใช้ตอบคำถามลูกค้าเกี่ยวกับเมนู เวลาเปิด ที่ตั้ง เบอร์โทรศัพท์ และการสั่งล่วงหน้า พร้อมระบบจัดรายการสั่งอาหารและบันทึกรายรับลง Google Sheets เมื่อกำหนด Secrets ครบ

Live demo: https://huggingface.co/spaces/jetsadapa/lomwong-cafe

## Business Domain

Lom Wong Café & Restaurant เป็นร้านอาหารและคาเฟ่บรรยากาศเป็นกันเองในอำเภอชนบท จังหวัดขอนแก่น จุดประสงค์ของระบบคือช่วยลดการตอบคำถามซ้ำใน DM และช่วยลูกค้าหาข้อมูลพื้นฐานของร้าน เช่น เวลาเปิด ที่อยู่ เบอร์โทร และเมนูที่เหมาะกับความต้องการ

ดู thinking process ของ Lab 4 ได้ที่ [PIVOT.md](PIVOT.md)

## Features

- ตอบ FAQ ของร้านจาก `knowledge/lomwong_cafe_kb.txt`
- แนะนำเมนูตามความต้องการ เช่น ไม่ดื่มกาแฟ หวานน้อย หรืออยากได้เมนูแนะนำ
- ตอบข้อมูลติดต่อจริง เช่น Facebook, ที่อยู่, เบอร์โทรศัพท์ และเวลาเปิดร้าน
- จัดรายการสั่งอาหาร คำนวณยอดรวม และสร้างข้อความออเดอร์ให้ลูกค้า
- บันทึกออเดอร์ลง Google Sheets ผ่าน worksheet `Orders` เมื่อมี service account configured
- ส่งแจ้งเตือนออเดอร์ใหม่และรายงานยอดขายวันนี้เข้า Telegram เมื่อกำหนด Telegram secrets ครบ
- ตอบเป็นภาษาไทยแบบกระชับและสุภาพ
- ถ้าไม่มีข้อมูลใน knowledge base จะบอกว่าไม่ทราบจากข้อมูลร้านที่มี

## Project Structure

- `app.py` — Streamlit chat UI และ Gemini response generation
- `rag_engine.py` — load, chunk, embed, index, search ด้วย Sentence Transformers + FAISS
- `menu_catalog.py` — รายการเมนูและราคา สำหรับระบบสั่งอาหาร
- `order_logger.py` — บันทึกออเดอร์และรายรับลง Google Sheets
- `telegram_report.py` — ส่งแจ้งเตือนออเดอร์และรายงานยอดขายเข้า Telegram
- `knowledge/lomwong_cafe_kb.txt` — knowledge base ของ Lomwong Cafe
- `Dockerfile` — configuration สำหรับ Hugging Face Space
- `PIVOT.md` — Lab 4 Pivot Worksheet

## Local Setup

```bash
pip install -r requirements.txt
```

สร้างไฟล์ `.env` แล้วใส่ Gemini API key:

```bash
GEMINI_API_KEY=your_api_key_here
```

รันแอป:

```bash
streamlit run app.py
```

## Deploy

โปรเจกต์นี้ deploy บน Hugging Face Spaces ด้วย Docker SDK ต้องตั้ง secret ใน Space Settings:

```text
GEMINI_API_KEY
```

ถ้าต้องการให้ระบบสั่งอาหารบันทึกลง Google Sheets ให้ตั้งเพิ่ม:

```text
GOOGLE_SHEET_ID
GOOGLE_SERVICE_ACCOUNT_JSON
```

และแชร์ Google Sheet ให้ `client_email` ของ service account เป็น Editor

ถ้าต้องการส่งแจ้งเตือน/รายงานเข้า Telegram ให้ตั้งเพิ่ม:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

## Demo Day Self-Check

- [x] Deploy URL ใช้งานได้ (เปิดทดสอบล่าสุด: 2026-05-21)
- [x] ไม่มี `.env` หรือ `*.json` ใน git tracking ปัจจุบัน
- [x] PIVOT.md ครบ 3 ข้อ
- [x] README อธิบายระบบของ domain ตัวเอง ไม่ใช่ MilkLab
- [x] knowledge base, prompt, UI ปรับเป็น domain ใหม่หมดแล้ว
