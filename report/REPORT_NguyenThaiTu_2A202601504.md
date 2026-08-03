# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thái Tú
**MSSV:** 2A202601504
**Nhóm:** LowTech Nhất
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai đoạn văn bản có độ tương tự cosine cao (gần 1.0), điều đó có nghĩa là hai vector embedding của chúng gần như cùng hướng trong không gian nhiều chiều — tức là chúng mang ý nghĩa ngữ nghĩa tương đồng. Nói cách khác, nội dung và chủ đề của hai đoạn văn bản đó rất giống nhau dù có thể dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Con mèo đang nằm ngủ trên sofa."
- Câu B: "Chú mèo đang nghỉ ngơi trên ghế dài."
- Tại sao tương đồng: Cả hai câu đều mô tả cùng một tình huống (một con mèo đang nghỉ ngơi trên đồ nội thất), chỉ khác nhau về cách dùng từ ("nằm ngủ" vs "nghỉ ngơi", "sofa" vs "ghế dài") nhưng ý nghĩa ngữ nghĩa gần như giống nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thuật toán sắp xếp nhanh (quicksort) có độ phức tạp trung bình O(n log n)."
- Câu B: "Hôm nay thời tiết Hà Nội nắng đẹp, nhiệt độ 32 độ C."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau (khoa học máy tính vs thời tiết), không có sự liên quan về ngữ nghĩa, nên các vector embedding sẽ hướng về các phía khác nhau trong không gian chiều cao.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity đo góc (angle) giữa hai vector thay vì khoảng cách tuyệt đối, nên nó không bị ảnh hưởng bởi độ dài (magnitude) của vector. Điều này quan trọng vì text embeddings có thể có độ lớn khác nhau tùy thuộc vào độ dài văn bản hoặc mô hình embedding, nhưng hướng của vector mới thực sự phản ánh ý nghĩa ngữ nghĩa. Khoảng cách Euclid sẽ bị ảnh hưởng bởi sự khác biệt về magnitude, dẫn đến kết quả không chính xác khi so sánh ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Phép tính:*
> Áp dụng công thức: `số lượng chunk = ceil((độ_dài_tài_liệu - overlap) / (chunk_size - overlap))`
> = ceil((10000 - 50) / (500 - 50))
> = ceil(9950 / 450)
> = ceil(22.11)
> = **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap = 100: ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = **25 chunks** — tăng thêm 2 chunks so với trước. Overlap nhiều hơn giúp giảm nguy cơ "cắt đứt" thông tin quan trọng ở ranh giới giữa các chunks, đảm bảo rằng ngữ cảnh xung quanh ranh giới được giữ lại ở cả chunk trước và sau, từ đó cải thiện chất lượng truy xuất (retrieval quality) khi một ý nằm trải dài giữa hai đoạn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex lookbehind `(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)` để tách văn bản tại các ranh giới câu (sau dấu ". ", "! ", "? ", hoặc ".\n") mà vẫn giữ nguyên dấu câu trong câu gốc. Sau khi tách, lọc bỏ các phần tử rỗng và strip khoảng trắng thừa. Các câu được nhóm lại theo `max_sentences_per_chunk`, nối bằng khoảng trắng. Edge case xử lý: text rỗng trả về `[]`, và `max_sentences_per_chunk` luôn ≥ 1 (dùng `max(1, ...)` để bảo vệ).

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo cơ chế đệ quy: với mỗi separator trong danh sách theo thứ tự ưu tiên (`\n\n` → `\n` → `. ` → ` ` → `""`), tách văn bản bằng separator hiện tại, sau đó gộp các phần lại sao cho mỗi chunk không vượt quá `chunk_size`. Nếu chunk nào vẫn quá lớn, đệ quy xuống separator tiếp theo. Base case: nếu `len(text) <= chunk_size` thì trả về `[text]`; nếu hết separator thì cắt cứng theo `chunk_size`. Với separator rỗng `""`, cũng fallback sang cắt cứng theo ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi document được embed bằng `embedding_fn` và lưu dưới dạng dict gồm `id`, `content`, `metadata`, `embedding` vào list `_store` (in-memory). Khi search, query được embed rồi tính cosine similarity với tất cả record — sử dụng dot product chia cho tích magnitude hai vector (`dot(q, d) / (||q|| * ||d||)`). Kết quả được sắp xếp giảm dần theo score và trả về top_k. Nếu ChromaDB khả dụng, sẽ ưu tiên dùng ChromaDB thay vì in-memory.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc **trước** khi tìm kiếm (pre-filtering): duyệt `_store` và chỉ giữ các record có metadata khớp tất cả key-value trong `metadata_filter`, sau đó mới chạy similarity search trên tập đã lọc. Nếu `metadata_filter` là None, gọi thẳng `search()` để tránh lọc thừa. `delete_document` xóa tất cả record trong `_store` có `id == doc_id` hoặc `metadata["doc_id"] == doc_id` bằng list comprehension, trả về `True` nếu có ít nhất 1 record bị xóa, `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Theo mô hình RAG (Retrieval-Augmented Generation): (1) Gọi `store.search(question, top_k)` để truy xuất top_k chunks liên quan nhất, (2) Trích `content` từ mỗi kết quả và nối thành một chuỗi context bằng `"\n".join(...)`, (3) Xây dựng prompt theo format `"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"`, rồi gọi `llm_fn(prompt)` để sinh câu trả lời. Cách inject context này giúp LLM dựa vào thông tin thực tế từ knowledge base thay vì hallucinate.

### Kết quả Baseline — ChunkingStrategyComparator (Bài tập 3.1)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=200)` trên 2 tài liệu mẫu:

**File: `data/customer_support_playbook.txt` (1841 ký tự)**

| Chiến lược | Số chunks | Avg length (ký tự) |
|-----------|-----------|---------------------|
| fixed_size | 11 | 185.5 |
| by_sentences | 4 | 458.2 |
| recursive | 15 | 121.0 |

**File: `data/python_intro.txt` (2222 ký tự)**

| Chiến lược | Số chunks | Avg length (ký tự) |
|-----------|-----------|---------------------|
| fixed_size | 13 | 189.4 |
| by_sentences | 5 | 442.6 |
| recursive | 17 | 128.9 |

**Nhận xét:**
- `by_sentences` tạo ít chunk nhất nhưng mỗi chunk dài nhất (~450 ký tự), giữ nguyên ngữ cảnh câu nhưng có thể quá dài cho embedding.
- `recursive` tạo nhiều chunk nhất với kích thước nhỏ nhất (~125 ký tự), linh hoạt nhưng có thể cắt nhỏ quá.
- `fixed_size` cân bằng giữa hai chiến lược trên (~190 ký tự/chunk), đảm bảo kích thước đồng đều.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Danh sách hoàn thành

- [x] `Document` dataclass — ĐÃ TRIỂN KHAI SẴN
- [x] `FixedSizeChunker` — ĐÃ TRIỂN KHAI SẴN
- [x] `SentenceChunker` — tách dựa trên ranh giới câu, nhóm lại thành các chunks
- [x] `RecursiveChunker` — thử nghiệm các dấu phân cách theo thứ tự, đệ quy
- [x] `compute_similarity` — công thức cosine similarity kèm bảo vệ chia cho 0
- [x] `ChunkingStrategyComparator` — gọi cả ba chiến lược, tính thống kê
- [x] `EmbeddingStore.__init__` — khởi tạo store (in-memory, fallback từ ChromaDB)
- [x] `EmbeddingStore.add_documents` — embed và lưu trữ từng document
- [x] `EmbeddingStore.search` — embed query, xếp hạng theo cosine similarity
- [x] `EmbeddingStore.get_collection_size` — trả về số lượng
- [x] `EmbeddingStore.search_with_filter` — lọc metadata trước, sau đó tìm kiếm
- [x] `EmbeddingStore.delete_document` — xóa tất cả chunks của một doc_id
- [x] `KnowledgeBaseAgent.answer` — retrieve + tạo prompt + gọi LLM

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\labAI_vinuni\buoi7\K4-C1-Day07-Data-Foundations
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **Lưu ý:** Tất cả điểm thực tế dưới đây được tính bằng **mock embedder** (dùng hash MD5 để sinh vector xác định nhưng gần như ngẫu nhiên). Mock embedder **không phản ánh chất lượng ngữ nghĩa** — để có kết quả có ý nghĩa, cần dùng `EMBEDDING_PROVIDER=local` với mô hình `paraphrase-multilingual-MiniLM-L12-v2`.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Con mèo đang nằm ngủ trên sofa." | "Chú mèo đang nghỉ ngơi trên ghế dài." | cao | -0.0423 | Không |
| 2 | "Python là ngôn ngữ lập trình bậc cao." | "Python is a high-level programming language." | cao | -0.1068 | Không |
| 3 | "Chính sách đổi trả hàng trong 30 ngày." | "Khách hàng được hoàn tiền trong vòng một tháng." | cao | 0.1959 | Tương đối |
| 4 | "Trời hôm nay nắng đẹp, nhiệt độ 32 độ." | "Thuật toán quicksort có độ phức tạp O(n log n)." | thấp | -0.0503 | Đúng |
| 5 | "Giao hàng miễn phí cho đơn hàng từ 500 nghìn." | "Miễn phí vận chuyển với đơn từ 500k trở lên." | cao | 0.0366 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là **cặp 2** ("Python là ngôn ngữ lập trình bậc cao" vs "Python is a high-level programming language") — đây là hai câu có **cùng nghĩa hoàn toàn**, chỉ khác ngôn ngữ (Việt vs Anh), nhưng mock embedder cho điểm **âm** (-0.1068). Điều này chứng minh rõ ràng rằng mock embedder chỉ dựa trên hash ký tự, không hề hiểu ngữ nghĩa. Với mô hình thật (như `paraphrase-multilingual-MiniLM-L12-v2`), cặp này sẽ cho điểm rất cao vì mô hình được huấn luyện đa ngữ (multilingual) — hiểu rằng các câu song ngữ mang cùng ý nghĩa. Bài học: **chất lượng embedding phụ thuộc hoàn toàn vào mô hình** — mock chỉ nên dùng cho unit test, không bao giờ dùng để kết luận chiến lược nào tốt hơn.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân trong gói `src`. Dữ liệu: 7 tài liệu chính sách TMĐT Shopee trong `data/k4_ecommerce/`. Câu hỏi lấy từ `benchmark_queries.json` do nhóm thống nhất.

### Chiến lược cá nhân: `SentenceChunker(max_sentences_per_chunk=3)`

Lý do chọn: Tài liệu chính sách TMĐT thường có cấu trúc câu rõ ràng, mỗi câu chứa một quy định cụ thể. SentenceChunker giữ nguyên ranh giới câu, đảm bảo mỗi chunk chứa thông tin mạch lạc. Nhóm 3 câu/chunk giúp cân bằng giữa đủ ngữ cảnh và kích thước embedding hiệu quả.

**Store size:** 8 chunks

### Kết quả Retrieval (mock embedder)

| # | Câu hỏi (Query) | Top-1 Chunk (doc_id) | Score | Relevant? | Gold doc_id |
|---|-------|----------------|-------|-----------|-------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng sau khi giao? | seller-return-response | 0.2643 | Không | return-request-deadline |
| 2 | Những trường hợp nào làm căn cứ yêu cầu trả hàng? | returned-product-evidence | 0.1811 | Không | return-eligibility |
| 3 | Người bán phải phản hồi yêu cầu trả hàng trong bao lâu? | return-request-deadline | 0.1293 | Không | seller-return-response |
| 4 | Người mua cần chuẩn bị sản phẩm và bằng chứng hoàn trả thế nào? | return-shipping-refund | 0.1996 | Không | returned-product-evidence |
| 5 | Tranh chấp được xử lý trong bao lâu sau khi Shopee nhận đủ tài liệu? | return-request-deadline | 0.2100 | Không | dispute-resolution-process |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0 / 5 (với mock embedder)

### So sánh 3 chiến lược chunking trên cùng 5 câu hỏi

| Chiến lược | Store size | Q1 Top-1 doc | Q2 Top-1 doc | Q3 Top-1 doc | Q4 Top-1 doc | Q5 Top-1 doc |
|-----------|-----------|-------------|-------------|-------------|-------------|-------------|
| SentenceChunker(3) | 8 chunks | seller-return-response | returned-product-evidence | return-request-deadline | return-shipping-refund | return-request-deadline |
| RecursiveChunker(200) | 10 chunks | return-shipping-refund | returned-product-evidence | dispute-resolution-process | return-shipping-refund | return-shipping-refund |
| FixedSizeChunker(200,20) | 15 chunks | return-shipping-refund | return-shipping-refund | return-request-deadline | return-shipping-refund | return-shipping-refund |

**Nhận xét so sánh:**
- Với mock embedder, cả 3 chiến lược đều không trả về đúng gold document ở top-1, vì mock sinh vector dựa trên hash — không phản ánh ngữ nghĩa.
- RecursiveChunker tạo chunks đều hơn (10 chunks) và có Q3 trả về đúng `dispute-resolution-process` trong top-3.
- FixedSizeChunker tạo nhiều chunk nhất (15) nhưng cắt giữa câu, làm giảm tính mạch lạc.
- SentenceChunker tạo ít chunk nhất (8), giữ nguyên câu nhưng một số chunk quá dài.

### Kiểm tra Metadata Filtering

| Filter | Query | Kết quả | Nhận xét |
|--------|-------|---------|----------|
| `customer_role=buyer` | "trả hàng" | 4 kết quả (return-request-deadline, return-eligibility, return-com-rules, returned-product-evidence) | ✅ Lọc đúng — chỉ trả về tài liệu dành cho Người Mua |
| `customer_role=seller` | "phản hồi" | 1 kết quả (seller-return-response) | ✅ Lọc đúng — chỉ trả về tài liệu dành cho Người Bán |
| `category=dispute-resolution` | "tranh chấp" | 2 kết quả (dispute-resolution-process) | ✅ Lọc đúng — chỉ trả về tài liệu tranh chấp |

### Kiểm tra Delete Document

| Thao tác | Kết quả |
|----------|---------|
| Store size trước khi xóa | 8 chunks |
| `delete_document("return-com-rules")` | True ✅ |
| Store size sau khi xóa | 7 chunks (giảm 1) |

### Agent Demo

Agent hoạt động đúng theo mô hình RAG: retrieve context → build prompt → gọi LLM. Với mock LLM, câu trả lời chỉ trích dẫn lại context. Với LLM thật + embedder thật, agent sẽ tổng hợp câu trả lời chính xác dựa trên thông tin từ knowledge base.

> **Kết luận quan trọng:** Mock embedder chỉ phù hợp để kiểm tra **tính đúng đắn** của code (42/42 tests pass). Để đánh giá **chất lượng truy xuất ngữ nghĩa**, cần chuyển sang `EMBEDDING_PROVIDER=local` với mô hình `paraphrase-multilingual-MiniLM-L12-v2` — mô hình đa ngữ phù hợp cho corpus tiếng Việt.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> [Cần cập nhật sau buổi thuyết trình và thảo luận nhóm]

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |

> Phần "Kết quả truy xuất" tự đánh giá 8/10: code hoạt động đúng, metadata filtering chính xác, đã chạy benchmark trên dữ liệu thực. Trừ 2 điểm vì chưa chạy với embedder thật để có kết quả ngữ nghĩa.
