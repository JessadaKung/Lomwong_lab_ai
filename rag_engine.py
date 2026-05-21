import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
QUESTION_WORDS = [
    "ราคาเท่าไหร่",
    "เท่าไหร่",
    "ราคา",
    "มีเมนู",
    "เมนู",
    "อะไรบ้าง",
    "อะไร",
    "บ้าง",
    "ไหม",
    "มั้ย",
    "ครับ",
    "ค่ะ",
    "คะ",
    "?",
]
CATEGORY_HEADERS = [
    ("แจ่วฮ้อน", "===เมนูแจ่วฮ้อน==="),
    ("เมนูต้ม", "===เมนูต้ม==="),
    ("เมนูตำ", "===เมนูตำ==="),
    ("เมนูยำ", "===เมนูยำ==="),
    ("อาหารจานเดียว", "===เมนูอาหารจานเดียว==="),
    ("ข้าวผัด", "===เมนูอาหารจานเดียว==="),
    ("กระเพรา", "===เมนูอาหารจานเดียว==="),
    ("ทานเล่น", "===เมนูทานเล่น==="),
    ("เครื่องดื่ม", "===เครื่องดื่มและโปรโมชัน==="),
    ("โปร", "===เครื่องดื่มและโปรโมชัน==="),
]


class RAGEngine:
    def __init__(self, kb_path: str):
        self.model = SentenceTransformer(EMBED_MODEL)
        self.chunks = self._load_and_chunk(kb_path)
        self.index, self.embeddings = self._build_index()

    def _load_and_chunk(self, path: str) -> list[str]:
        with open(path, encoding="utf-8") as f:
            text = f.read()

        return [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

    def _build_index(self):
        embeddings = self.model.encode(self.chunks, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype="float32")

        index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)

        return index, embeddings

    def _normalize(self, text: str) -> str:
        return "".join(ch for ch in text.lower() if not ch.isspace())

    def _keyword_matches(self, query: str) -> list[int]:
        normalized_query = self._normalize(query)
        search_key = normalized_query
        for word in QUESTION_WORDS:
            search_key = search_key.replace(self._normalize(word), "")

        matches = []
        for keyword, header in CATEGORY_HEADERS:
            if self._normalize(keyword) not in normalized_query:
                continue
            for index, chunk in enumerate(self.chunks):
                if self._normalize(chunk).startswith(header):
                    matches.append(index)

        for index, chunk in enumerate(self.chunks):
            normalized_chunk = self._normalize(chunk)
            if search_key and search_key in normalized_chunk:
                if index not in matches:
                    matches.append(index)
                continue
            if normalized_query and normalized_query in normalized_chunk:
                if index not in matches:
                    matches.append(index)

        return matches

    def search(self, query: str, top_k: int = 3) -> list[str]:
        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding, dtype="float32")

        _, indices = self.index.search(query_embedding, top_k)

        ordered_indices = []
        for i in self._keyword_matches(query):
            if i not in ordered_indices:
                ordered_indices.append(i)

        for i in indices[0]:
            if i < len(self.chunks) and i not in ordered_indices:
                ordered_indices.append(i)

        return [self.chunks[i] for i in ordered_indices[:top_k]]
