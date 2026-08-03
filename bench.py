from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from src.NguyenHoangMinh import chunking as personal_chunking
from src.NguyenHoangMinh import models as personal_models
from src.NguyenHoangMinh import store as personal_store
from src.NguyenHoangMinh.agent import KnowledgeBaseAgent
from src.NguyenHoangMinh.chunking import (
    ChunkingStrategyComparator,
    RecursiveChunker,
)
from src.NguyenHoangMinh.embeddings import LocalEmbedder, _mock_embed

# Repo nhóm lưu lời giải cá nhân trong src/NguyenHoangMinh. Các alias này giúp
# ingest.py được cung cấp sẵn tiếp tục import đúng ba module theo contract gốc.
sys.modules.setdefault("src.chunking", personal_chunking)
sys.modules.setdefault("src.models", personal_models)
sys.modules.setdefault("src.store", personal_store)

from ingest import build_knowledge_base, load_documents  # noqa: E402


DATA_DIR = Path("data/k4_ecommerce")
QUERY_FILE = DATA_DIR / "benchmark_queries.json"


class HeadingAwareChunker:
    """Tách theo Markdown heading, rồi recursive-split section quá dài.

    Heading được gắn lại vào từng mảnh con để các chunk sau vẫn giữ ngữ cảnh
    điều/khoản của chính sách.
    """

    def __init__(self, chunk_size: int = 260) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        sections = [
            section.strip()
            for section in re.split(r"(?=^#{1,6}\s+)", text, flags=re.MULTILINE)
            if section.strip()
        ]
        chunks: list[str] = []
        for section in sections:
            if len(section) <= self.chunk_size:
                chunks.append(section)
                continue

            lines = section.splitlines()
            heading = lines[0].strip() if re.match(r"^#{1,6}\s+", lines[0]) else ""
            body = "\n".join(lines[1:] if heading else lines).strip()
            available_size = max(1, self.chunk_size - len(heading) - 1)
            pieces = RecursiveChunker(chunk_size=available_size).chunk(body)
            chunks.extend(
                f"{heading}\n{piece}".strip() if heading else piece
                for piece in pieces
                if piece.strip()
            )
        return chunks


class RetrievedResultsStore:
    """Adapter để Agent dùng đúng kết quả đã metadata-filter trong benchmark."""

    def __init__(self, results: list[dict]) -> None:
        self.results = results

    def search(self, _question: str, top_k: int = 3) -> list[dict]:
        return self.results[:top_k]


def select_embedder():
    provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip().lower()
    if provider == "local":
        return LocalEmbedder()
    return _mock_embed


def extractive_demo_llm(prompt: str) -> str:
    """LLM giả lập: trả lại chunk đầu tiên cùng nhãn nguồn để demo grounding."""

    context = prompt.split("Context:\n", 1)[-1].split("\n\nQuestion:", 1)[0]
    first_block = re.split(r"\n\n(?=\[2\])", context, maxsplit=1)[0]
    return first_block.strip()


def print_baseline() -> None:
    print("=== BASELINE: 3 tài liệu, đã bỏ YAML front matter ===")
    comparator = ChunkingStrategyComparator()
    for document in load_documents(DATA_DIR)[:3]:
        comparison = comparator.compare(document.content, chunk_size=260)
        print(f"document={document.id}")
        for strategy, stats in comparison.items():
            print(
                f"  {strategy:12} count={stats['count']:2d} "
                f"avg_length={stats['avg_length']:.2f}"
            )


def main() -> int:
    queries = json.loads(QUERY_FILE.read_text(encoding="utf-8"))
    if len(queries) != 5:
        raise ValueError(f"Benchmark phải có đúng 5 query, hiện có {len(queries)}")

    print_baseline()

    # DÒNG STRATEGY RIÊNG CỦA NGUYỄN HOÀNG MINH:
    chunker = HeadingAwareChunker(chunk_size=260)
    embedding_fn = select_embedder()
    backend = getattr(embedding_fn, "_backend_name", embedding_fn.__class__.__name__)
    store = build_knowledge_base(DATA_DIR, embedding_fn, chunker=chunker)

    print("\n=== PERSONAL BENCHMARK ===")
    print("owner=NguyenHoangMinh-2A202601764")
    print("strategy=HeadingAwareChunker(chunk_size=260, fallback=RecursiveChunker)")
    print(f"embedding={backend}")
    print(f"chunks={store.get_collection_size()}")
    if backend == "mock embeddings fallback":
        print("WARNING=Mock chỉ xác minh pipeline; không dùng để kết luận chất lượng retrieval.")

    for item in queries:
        metadata_filter = item.get("metadata_filter")
        if metadata_filter:
            results = store.search_with_filter(
                item["query"], top_k=3, metadata_filter=metadata_filter
            )
        else:
            results = store.search(item["query"], top_k=3)

        agent = KnowledgeBaseAgent(
            store=RetrievedResultsStore(results),
            llm_fn=extractive_demo_llm,
        )
        answer = agent.answer(item["query"], top_k=3)

        print(f"\n[{item['id']}] {item['query']}")
        print(f"filter={metadata_filter}")
        print(f"gold_doc_id={item['gold_doc_id']}")
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            preview = " ".join(result["content"].split())[:160]
            print(
                f"top-{rank} score={result['score']:.4f} "
                f"doc_id={metadata.get('doc_id')} "
                f"chunk_index={metadata.get('chunk_index')} preview={preview}"
            )
        print(f"agent_answer={answer.replace(chr(10), ' ')[:300]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
