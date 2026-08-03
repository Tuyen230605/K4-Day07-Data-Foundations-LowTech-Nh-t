import json
from pathlib import Path
import sys

# Thêm thư mục gốc vào đường dẫn để import được ingest và src
sys.path.append(str(Path(__file__).parent.parent))

from ingest import build_knowledge_base
from src.DOANVANTUYEN_2A202601374.chunking import FixedSizeChunker, SentenceChunker, RecursiveChunker
from src.DOANVANTUYEN_2A202601374.embeddings import LocalEmbedder, _mock_embed

def run_benchmark():
    data_dir = "data/k4_ecommerce"
    queries_file = Path(data_dir) / "benchmark_queries.json"
    
    if not queries_file.exists():
        print(f"Không tìm thấy file {queries_file}")
        return

    with open(queries_file, "r", encoding="utf-8") as f:
        queries = json.load(f)

    # Dùng Local Embedder nếu có cài đặt, nếu không dùng Mock
    try:
        embedder = LocalEmbedder()
        print("Sử dụng LocalEmbedder (Mô hình thật)")
    except Exception:
        embedder = _mock_embed
        print("Sử dụng Mock Embedder (Giả lập)")

    # Khởi tạo 3 chiến lược
    strategies = {
        "Fixed Size (500, overlap 50)": FixedSizeChunker(chunk_size=500, overlap=50),
        "Sentence Chunker (max 3 câu)": SentenceChunker(max_sentences_per_chunk=3),
        "Recursive Chunker (size 500)": RecursiveChunker(chunk_size=500)
    }

    print("\n" + "="*50)
    for name, chunker in strategies.items():
        print(f"\n🚀 Đang chạy chiến lược: {name}")
        
        # Tạo vector store với chiến lược tương ứng
        store = build_knowledge_base(
            data_dir=data_dir,
            embedding_fn=embedder,
            chunker=chunker,
            collection_name=f"test_{name.replace(' ', '_')}"
        )
        
        correct_count = 0
        for q in queries:
            query_text = q["query"]
            gold_id = q["gold_doc_id"]
            filter_meta = q.get("metadata_filter")
            
            # Tìm kiếm top 3 có dùng filter
            results = store.search_with_filter(
                query=query_text, 
                top_k=3, 
                metadata_filter=filter_meta
            )
            
            # Kiểm tra xem gold_doc_id có nằm trong top kết quả không
            retrieved_doc_ids = [r["metadata"].get("doc_id") for r in results]
            is_correct = gold_id in retrieved_doc_ids
            
            if is_correct:
                correct_count += 1
                status = "✅ PASS"
            else:
                status = f"❌ FAIL (Tìm thấy: {', '.join(set(retrieved_doc_ids))})"
                
            print(f"  - {q['id']}: {status}")
            
        print(f"👉 ĐỘ CHÍNH XÁC: {correct_count}/{len(queries)}")
        print("-" * 50)

if __name__ == "__main__":
    run_benchmark()
