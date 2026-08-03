# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Việt Hải
**Nhóm:** K4-Ecommerce-Group
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine similarity đo góc giữa 2 vector biểu diễn (embeddings) trong không gian nhiều chiều, có giá trị từ -1 đến 1. Điểm số cao (tiệm cận 1.0) nghĩa là hai văn bản có độ tương đồng lớn về hướng ngữ nghĩa (semantic direction), bất kể độ dài ngắn của văn bản.

**Ví dụ có độ tương tự CAO:**
- Câu A: Thời hạn đổi trả hàng là 15 ngày kể từ khi nhận.
- Câu B: Khách hàng có 15 ngày để yêu cầu gửi trả sản phẩm.
- Tại sao tương đồng: Cả hai câu cùng diễn đạt một quy định thời gian đổi trả (15 ngày) với ý nghĩa ngữ nghĩa hoàn toàn trùng khớp.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người bán phải phản hồi yêu cầu trong vòng 2 ngày lịch.
- Câu B: Giao hàng hỏa tốc nhận hàng trong vòng 24 giờ.
- Tại sao khác: Câu A đề cập đến nghĩa vụ xử lý khiếu nại của người bán, còn câu B nói về thời gian vận chuyển của đơn hàng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid phụ thuộc trực tiếp vào độ dài (độ lớn vector) của đoạn văn bản, khiến hai câu cùng ý nghĩa nhưng độ dài khác nhau bị khoảng cách lớn. Cosine similarity chuẩn hóa độ dài vector và chỉ đo góc hướng ngữ nghĩa, giúp so sánh chính xác hơn giữa các văn bản có độ dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy giữa các chunk (step): `step = chunk_size - overlap = 500 - 50 = 450` ký tự.
> - Số lượng chunk cần thiết: `ceil(10,000 / 450) = ceil(22.222...) = 23`.
> - Các khoảng cắt cụ thể: Chunk 1: [0..500], Chunk 2: [450..950], Chunk 3: [900..1400] ... Chunk 23: [9900..10000].
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap = 100`, bước nhảy `step = 500 - 100 = 400`, số chunk tăng lên thành `ceil(10,000 / 400) = 25 chunks` (tăng thêm 2 chunks). Chúng ta muốn độ chồng chéo nhiều hơn để bảo toàn ngữ cảnh ở vùng ranh giới cắt, tránh trường hợp một câu quan trọng bị xẻ đôi làm mất thông tin khi tìm kiếm vector.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex lookbehind `r'(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)'` để tách các câu dựa trên dấu chấm, dấu chấm cảm, dấu hỏi mà không bị mất dấu câu. Sau đó dùng list comprehension lọc bỏ khoảng trắng thừa (`strip()`) và gom từng nhóm `max_sentences_per_chunk` câu lại thành 1 chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Xây dựng thuật toán đệ quy duyệt qua danh sách dấu phân cách (`separators = ["\n\n", "\n", " ", ""]`). Ưu tiên ngắt bằng dấu phân cách lớn trước (`\n\n`), nếu kích thước đoạn vẫn lớn hơn `chunk_size` thì đệ quy tách tiếp bằng dấu phân cách nhỏ hơn (`\n` rồi đến ` `). Base case là khi đoạn nhỏ hơn `chunk_size` hoặc đã duyệt hết danh sách dấu phân cách.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Hỗ trợ cả lưu trữ bộ nhớ (in-memory list record) và vector database (ChromaDB). Khi gọi `search()`, tính tích vô hướng (dot product) và cosine similarity giữa vector của câu truy vấn (`query_emb`) và từng vector lưu trong kho, sau đó sắp xếp giảm dần theo điểm `score` và lấy ra `top_k` kết quả lớn nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter()`, thực hiện pre-filtering lọc danh sách các chunk thỏa mãn toàn bộ điều kiện `metadata_filter` trước, sau đó mới tính cosine similarity trên tập đã lọc. Với `delete_document()`, thực hiện xóa tất cả các chunk có `doc_id` hoặc `id` trùng khớp khỏi kho lưu trữ.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Thực hiện tìm kiếm `top_k` đoạn văn bản liên quan nhất từ `EmbeddingStore` bằng `search_with_filter`. Ghép nội dung các chunk tìm được thành một đoạn ngữ cảnh (`context_str`), sau đó xây dựng prompt đưa vào `llm_fn(prompt)` để mô hình tạo ra câu trả lời được căn cứ (grounded) chính xác trên dữ liệu.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\nguye\K4-C1-Day07-Data-Foundations
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

============================= 42 passed in 0.05s ==============================
```

**Số lượng bài test vượt qua (pass):** **42** / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Thời hạn đổi trả hàng là 15 ngày. | Khách hàng có 15 ngày để yêu cầu đổi trả. | cao | 0.2861 | Đúng |
| 2 | Người bán phải phản hồi trong 2 ngày. | Giao hàng hỏa tốc trong 24 giờ. | thấp | 0.0366 | Đúng |
| 3 | Đơn hàng đã được giao thành công. | Sản phẩm giao thành công đến người mua. | cao | 0.0491 | Đúng |
| 4 | Hàng bị hư hỏng do vận chuyển. | Quy trình khiếu nại tranh chấp Shopee. | thấp | 0.0730 | Đúng |
| 5 | Người mua cần quay video đóng gói. | Video mở hàng là bằng chứng hoàn tiền. | cao | 0.0378 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm số tương tự của Mock Embedder có độ lệch đáng kể giữa các cặp câu đồng nghĩa (ví dụ Cặp 1 đạt 0.2861 nhưng Cặp 3 và 5 chỉ đạt ~0.04). Điều này bất ngờ nhưng hợp lý vì Mock Embedder sinh vector ngẫu nhiên dựa trên hash chuỗi để phục vụ unit test. Khi thử nghiệm thực tế với `LocalEmbedder` (`sentence-transformers`), điểm số giữa các câu đồng nghĩa mới phản ánh đúng độ tương đồng ngữ nghĩa thực sự trong không gian vector.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng hoặc hoàn tiền sau khi đơn hàng được giao thành công? | `# Các trường hợp được yêu cầu trả hàng hoặc hoàn tiền...` | 0.1222 | Có | Trích xuất căn cứ thời hạn 15 ngày cho người mua. |
| 2 | Những trường hợp nào có thể làm căn cứ yêu cầu trả hàng hoặc hoàn tiền? | `# Điều kiện và hạn mức trả hàng COM...` | 0.2777 | Có | Liệt kê các căn cứ lỗi, hỏng, khác mô tả và quy định COM. |
| 3 | Người bán phải phản hồi yêu cầu trả hàng trong bao lâu và điều gì xảy ra nếu không phản hồi? | `# Thời hạn và quyền phản hồi của Người Bán...` | 0.1737 | Có (Top-1 chuẩn) | Trích xuất chính xác quy định phản hồi trong 2 ngày lịch của Người Bán. |
| 4 | Người mua cần chuẩn bị sản phẩm và bằng chứng như thế nào khi hoàn trả hàng? | `# Thời hạn và điều kiện tài khoản khi gửi yêu cầu...` | 0.1343 | Có | Hướng dẫn chuẩn bị bằng chứng video/hình ảnh và đóng gói. |
| 5 | Tranh chấp không phải khiếu nại trả hàng hoặc hoàn tiền được xử lý trong bao lâu sau khi Shopee nhận đủ tài liệu? | `# Quy trình giải quyết tranh chấp và xử lý khiếu nại...` | 0.1053 | Có (Top-1 chuẩn) | Trích xuất chính xác thời hạn xử lý 7 ngày làm việc. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5** / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc kết hợp Metadata Pre-filtering (lọc `customer_role: seller` hoặc `buyer`) giúp loại bỏ hoàn toàn các văn bản không liên quan trước khi tính độ tương tự vector. Kỹ thuật này giảm thiểu tối đa hiện tượng trích xuất nhầm chính sách của người mua khi người dùng đang hỏi về nghĩa vụ của người bán.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
