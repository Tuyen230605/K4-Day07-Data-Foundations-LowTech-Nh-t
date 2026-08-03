# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đoàn Văn Tuyền

**Nhóm:** K4

**Ngày:** 2026-08-03


---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) 

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Có nghĩa là góc giữa 2 vector biểu diễn văn bản rất nhỏ, chứng tỏ hai văn bản đó có chung chủ đề, ngữ cảnh hoặc có ý nghĩa ngữ nghĩa (semantic) rất giống nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Chính sách đổi trả hàng hóa trong vòng 7 ngày"
- Câu B: "Quy định hoàn trả sản phẩm sau 1 tuần mua hàng"
- Tại sao tương đồng: Khác biệt hoàn toàn về từ vựng (đổi trả/hoàn trả, 7 ngày/1 tuần) nhưng ý nghĩa đằng sau (semantic) lại y hệt nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả hàng hóa trong vòng 7 ngày"
- Câu B: "Ngân hàng nhà nước thay đổi chính sách lãi suất"
- Tại sao khác: Có chung một số từ khóa ("chính sách", "thay đổi") nhưng chủ đề hoàn toàn khác biệt (Thương mại điện tử so với Tài chính).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng (góc) của vector thay vì độ lớn. Điều này giúp hệ thống so sánh được mức độ giống nhau về mặt ý nghĩa bất kể độ dài của hai văn bản (văn bản dài hay ngắn không làm sai lệch kết quả).

### Bài toán tính toán Chunking

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Bước nhảy (step) = chunk_size - overlap = 500 - 50 = 450. Số chunk = làm tròn lên của (10000 - overlap) / step = 9950 / 450 = 22.11 -> 23 chunks. (Chính xác: 22 chunks đầu mỗi chunk nhảy 450 ký tự, chunk cuối sẽ chứa phần còn lại).
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
>Số chunk sẽ tăng lên thành 25. Tăng độ chồng chéo giúp đảm bảo các ý tưởng/ngữ cảnh không bị cắt đứt đột ngột ở ranh giới giữa 2 chunk, từ đó LLM có đủ ngữ cảnh liên kết để sinh ra câu trả lời chính xác.

---

## 2. Hướng tiếp cận của tôi

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng Regex `re.split(r'(?<=[.!?])\s+', text)` để tách chuỗi bằng các dấu câu kết thúc. Sau đó gom nhóm tối đa `max_sentences_per_chunk` lại với nhau, có xử lý bỏ qua các chuỗi rỗng để không tạo chunk dư thừa.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy. Base case: Nếu đoạn text đã ngắn hơn `chunk_size` thì trả về luôn. Đệ quy: Dùng mảng `separators` (ví dụ `\n\n`, `\n`, ` `) để thử tách. Nếu tách được, gọi đệ quy kiểm tra từng nửa. Đảm bảo luôn cố gắng giữ văn bản lớn nhất có thể nằm trong `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Lưu trữ:* Quản lý một `self.records = []` (list of dict) để lưu metadata và nội dung text khi không có ChromaDB.  
> *Tính tương tự:* Hàm `search` gọi thuật toán Cosine Similarity để so sánh vector câu hỏi với tất cả vector trong kho, sort giảm dần theo score và lấy top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Lọc trước (Pre-filtering):* Duyệt từng document và kiểm tra xem metadata của document đó có chứa tất cả các khóa-giá trị của filter hay không rồi mới đưa vào hàm search.  
> *Xóa:* Xóa bằng list comprehension, loại bỏ các document có `id` hoặc `metadata['doc_id']` khớp với ID cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Cấu trúc prompt được thiết kế rành mạch: "Context: {context_str}\n\nQuestion: {question}". Ngữ cảnh được đưa vào (inject) bằng cách join các chunk thu được từ `self.store.search` rồi gọi `llm_fn` để sinh câu trả lời tự động mà không bị "ảo giác" (hallucination).

---

## 3. Hoàn thiện code

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử

```
============================= test session starts =============================
platform win32 -- Python 3.12.6, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
...
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.11s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự 

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Bao lâu thì được trả hàng" | "Thời hạn đổi trả sản phẩm là bao lâu" | cao | 0.85 | Đúng |
| 2 | "Phí vận chuyển ai trả" | "Người mua phải chịu phí ship hoàn hàng không" | cao | 0.82 | Đúng |
| 3 | "Tôi muốn khiếu nại shop" | "Cửa hàng bán đồ giả" | thấp | 0.65 | Chưa đúng |
| 4 | "Shop lừa đảo" | "Chính sách bảo mật thông tin" | thấp | 0.15 | Đúng |
| 5 | "Sản phẩm lỗi" | "Thời hạn bảo hành" | thấp | 0.55 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 (Khiếu nại - Cửa hàng bán đồ giả) có điểm số thực tế cao hơn dự đoán ban đầu. Điều này chứng tỏ Embeddings biểu diễn ý nghĩa dựa trên không gian ẩn (latent space), nhận diện được hai câu này cùng chung sắc thái tiêu cực và rủi ro người dùng trong ngữ cảnh TMĐT.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src` (Sử dụng FixedSizeChunker làm chuẩn). 

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng? | Thời hạn chung là 15 ngày kể từ khi đơn hàng giao thành công... | 0.89 | Có | 15 ngày đối với hàng hóa thông thường, 24 giờ với hàng tươi sống. |
| 2 | Những trường hợp nào có thể làm căn cứ yêu cầu trả hàng? | Các căn cứ gồm không nhận đủ hàng, hàng giả, hàng hư hại, giao sai... | 0.85 | Có | Không đủ hàng, hàng giả, hàng lỗi hoặc giao sai so với mô tả. |
| 3 | Người bán phải phản hồi yêu cầu trả hàng trong bao lâu? | Người Bán có 2 ngày lịch để phản hồi... | 0.87 | Có | 2 ngày lịch kể từ lúc nhận được thông báo. |
| 4 | Chuẩn bị sản phẩm và bằng chứng như thế nào khi hoàn trả? | Đóng gói đúng quy định, quay video và chụp ảnh khi đóng gói... | 0.84 | Có | Cần quay video/chụp ảnh, giữ nguyên vẹn tem và đóng gói đúng chuẩn. |
| 5 | Tranh chấp không phải khiếu nại xử lý trong bao lâu? | Shopee đưa ra hướng giải quyết trong 7 ngày làm việc... | 0.88 | Có | Khoảng 7 ngày làm việc, có thể lâu hơn với vụ việc phức tạp. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Sử dụng siêu dữ liệu (`metadata_filter`) để phân chia vùng tài liệu (như `customer_role=seller`) có thể cải thiện độ chính xác (Precision) của Vector Search lên tới 100%, vì nó đã thu hẹp ngay lập tức tập kết quả loại bỏ mọi tài liệu không liên quan.

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
