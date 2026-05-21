---
title: Lomwong Cafe
emoji: ☕
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 8501
---

# Lomwong Cafe AI — Demi RAG Chatbot

Demi คือผู้ช่วย AI สำหรับ Lomwong Cafe ใช้ตอบคำถามลูกค้าเกี่ยวกับเมนู เวลาเปิด ระดับความหวาน ที่ตั้ง และการสั่งล่วงหน้า โดยดึงคำตอบจาก knowledge base ของร้านผ่าน RAG pipeline

Live demo: https://huggingface.co/spaces/jetsadapa/lomwong-cafe

## Business Domain

Lomwong Cafe เป็นคาเฟ่บรรยากาศเป็นกันเองสำหรับนักศึกษาและคนทำงานใกล้มหาวิทยาลัยเทคโนโลยีราชมงคลอีสาน วิทยาเขตขอนแก่น จุดประสงค์ของระบบคือช่วยลดการตอบคำถามซ้ำใน DM และช่วยลูกค้าเลือกเมนูที่เหมาะกับความต้องการ

ดู thinking process ของ Lab 4 ได้ที่ [PIVOT.md](PIVOT.md)

## Features

- ตอบ FAQ ของร้านจาก `knowledge/lomwong_cafe_kb.txt`
- แนะนำเมนูตามความต้องการ เช่น ไม่ดื่มกาแฟ หวานน้อย หรืออยากได้เมนูแนะนำ
- ตอบเป็นภาษาไทยแบบกระชับและสุภาพ
- ถ้าไม่มีข้อมูลใน knowledge base จะบอกว่าไม่ทราบจากข้อมูลร้านที่มี

## Project Structure

- `app.py` — Streamlit chat UI และ Gemini response generation
- `rag_engine.py` — load, chunk, embed, index, search ด้วย Sentence Transformers + FAISS
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

## Demo Day Self-Check

- [x] Deploy URL ใช้งานได้ (เปิดทดสอบล่าสุด: 2026-05-21)
- [x] ไม่มี `.env` หรือ `*.json` ใน git tracking ปัจจุบัน
- [x] PIVOT.md ครบ 3 ข้อ
- [x] README อธิบายระบบของ domain ตัวเอง ไม่ใช่ MilkLab
- [x] knowledge base, prompt, UI ปรับเป็น domain ใหม่หมดแล้ว
