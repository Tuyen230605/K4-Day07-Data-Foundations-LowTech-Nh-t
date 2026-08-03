# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hoàng Minh — 2A202601764
**Nhóm:** K4-C1
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung trong `REPORT_NHOM.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector embedding hướng gần giống nhau, nên hai đoạn văn bản thường thể hiện nội dung hoặc ý nghĩa tương tự dù có thể dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: Người mua có thể yêu cầu trả hàng khi sản phẩm bị lỗi.
- Câu B: Khách hàng được hoàn trả sản phẩm nếu hàng hóa bị hư hỏng.
- Tại sao tương đồng: Cả hai câu đều nói về quyền trả lại sản phẩm lỗi hoặc hư hỏng.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Người bán phải phản hồi yêu cầu trả hàng trong hai ngày.
- Câu B: Thời tiết hôm nay có mưa lớn vào buổi chiều.
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan là chính sách thương mại điện tử và thời tiết.

**Tại sao cosine similarity được ưu tiên hơn khoảng cách Euclid cho text embeddings?**

Cosine similarity tập trung vào góc và hướng của vector nên ít bị ảnh hưởng bởi độ lớn của vector. Khoảng cách Euclid nhạy với độ lớn, trong khi với text embeddings, hướng biểu diễn ý nghĩa thường quan trọng hơn độ dài tuyệt đối.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**

```text
ceil((10.000 - 50) / (500 - 50))
= ceil(9.950 / 450)
= ceil(22,111...)
= 23 chunks
```

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

```text
ceil((10.000 - 100) / (500 - 100))
= ceil(9.900 / 400)
= ceil(24,75)
= 25 chunks
```

Số chunk tăng từ 23 lên 25 vì bước dịch giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giúp giữ thông tin nằm sát ranh giới giữa hai chunk, nhưng làm tăng số chunk, dung lượng lưu trữ và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` — hướng tiếp cận:**

Tôi chuẩn hóa khoảng trắng rồi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng hoặc xuống dòng đứng sau dấu kết câu. Các câu được gom theo `max_sentences_per_chunk`; văn bản rỗng trả về danh sách rỗng và các phần chỉ chứa khoảng trắng bị loại bỏ.

**`RecursiveChunker.chunk` / `_split` — hướng tiếp cận:**

Thuật toán thử lần lượt các separator ưu tiên: đoạn văn, dòng, câu, từ và cuối cùng là ký tự. Mỗi phần vừa kích thước được gom lại; phần quá dài được xử lý đệ quy bằng separator tiếp theo. Base case là nội dung đã nhỏ hơn `chunk_size`; khi hết separator, văn bản được cắt cố định theo số ký tự để bảo đảm thuật toán luôn kết thúc.

**`compute_similarity` và `ChunkingStrategyComparator` — hướng tiếp cận:**

Cosine similarity được tính bằng tích vô hướng chia cho tích hai chuẩn vector, đồng thời trả `0.0` nếu một vector có độ lớn bằng 0 để tránh chia cho 0. Comparator chạy `FixedSizeChunker`, `SentenceChunker` và `RecursiveChunker`, sau đó trả số chunk, độ dài trung bình và danh sách chunk của từng strategy.

### Lớp EmbeddingStore

**`add_documents` + `search` — hướng tiếp cận:**

Mỗi `Document` được chuẩn hóa thành record gồm ID, nội dung, metadata, embedding và storage ID duy nhất. Store luôn giữ bản in-memory để hành vi ổn định, đồng thời có thể mirror sang ChromaDB nếu thư viện khả dụng. Khi tìm kiếm, query được embed, tính dot product với từng record, sắp xếp score giảm dần rồi lấy `top_k`.

**`search_with_filter` + `delete_document` — hướng tiếp cận:**

Metadata được lọc trước khi tính similarity để tránh xếp hạng các tài liệu sai đối tượng. `delete_document` tìm toàn bộ record có `metadata['doc_id']` tương ứng, xóa chúng khỏi bộ nhớ và khỏi ChromaDB nếu backend này đang hoạt động; hàm trả `False` khi không có tài liệu phù hợp.

### Tác tử KnowledgeBaseAgent

**`answer` — hướng tiếp cận:**

Agent truy xuất top-k chunk, đánh số từng chunk và ghép `doc_id`, `source_url` cùng nội dung vào phần context trước khi thêm câu hỏi. Prompt yêu cầu LLM chỉ sử dụng context, dẫn số thứ tự nguồn và nói rõ khi dữ liệu không đủ; nếu store rỗng, agent trả thông báo trực tiếp mà không gọi `llm_fn`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Lệnh chạy từ thư mục cá nhân:

```bash
.venv/bin/python -m pytest tests -v
```

Kết quả:

```text
platform darwin -- Python 3.11.15, pytest-9.1.1
rootdir: K4-C1-Day07-Data-Foundations
collected 42 items

tests/test_solution.py .......................................... [100%]

============================== 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass): 42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Điểm thực tế bên dưới được đo bằng `MockEmbedder` của starter repo và hàm `compute_similarity` đã triển khai. Mock embedding chỉ dùng để kiểm thử kỹ thuật, không phản ánh tốt quan hệ ngữ nghĩa tiếng Việt.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-------|-------|---------|--------------|-------|
| 1 | Người mua có thể yêu cầu trả hàng khi sản phẩm bị lỗi. | Khách hàng được hoàn trả sản phẩm nếu hàng hóa bị hư hỏng. | Cao | 0,0437 | Không |
| 2 | Thời hạn gửi yêu cầu hoàn tiền là mười lăm ngày. | Người mua cần yêu cầu hoàn tiền trong vòng 15 ngày. | Cao | -0,0570 | Không |
| 3 | Người bán phải phản hồi yêu cầu trả hàng trong hai ngày. | Thời tiết hôm nay có mưa lớn vào buổi chiều. | Thấp | -0,0628 | Có |
| 4 | Người mua cần quay video khi đóng gói hàng hoàn trả. | Khách hàng nên ghi hình quá trình đóng gói sản phẩm gửi lại. | Cao | 0,0062 | Không |
| 5 | Shopee xử lý tranh chấp sau khi nhận đủ tài liệu. | Công thức nấu phở cần nước dùng và các loại gia vị. | Thấp | -0,0146 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Ba cặp có ý nghĩa tương tự đều nhận score gần 0, thậm chí cặp 2 có score âm. Kết quả này xác nhận `MockEmbedder` sinh vector xác định từ hash toàn chuỗi chứ không học ý nghĩa; vì vậy mock phù hợp để test code nhưng không thể dùng để kết luận strategy retrieval nào tốt hơn. Benchmark chính thức cần local multilingual embedder.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Đã chạy benchmark kỹ thuật bằng `HeadingAwareChunker(chunk_size=260)` với recursive fallback và mock embedding. Store nạp 10 chunk; mock chỉ xác minh pipeline nên các score dưới đây chưa được dùng để kết luận chất lượng strategy. Năm query chung được giữ nguyên sau lần chạy này.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được | Điểm Score | Relevant? | Câu trả lời của Agent |
|---|-----------------|----------------------------|------------|-----------|-----------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng hoặc hoàn tiền sau khi đơn hàng được giao thành công? | `return-eligibility`: các trường hợp được trả hàng | 0,1222 | Không; gold chunk ở top-2 | Agent trả lời về điều kiện, chưa trả lời thời hạn. |
| 2 | Những trường hợp nào có thể làm căn cứ yêu cầu trả hàng hoặc hoàn tiền? | `return-com-rules`: điều kiện/hạn mức COM | 0,2777 | Không; gold chunk ở top-3 | Agent chỉ trả lời trường hợp COM, thiếu danh sách chung. |
| 3 | Người bán phải phản hồi yêu cầu trả hàng trong bao lâu và điều gì xảy ra nếu không phản hồi? | `seller-return-response`: phản hồi trong 2 ngày | 0,1737 | Có; gold chunk ở top-1 | Agent nêu đúng thời hạn và hệ quả không phản hồi. |
| 4 | Người mua cần chuẩn bị sản phẩm và bằng chứng như thế nào khi hoàn trả hàng? | `return-request-deadline`: thời hạn gửi yêu cầu | 0,1343 | Không; gold chunk ở top-2 | Agent trả lời về thời hạn, không trả lời bằng chứng. |
| 5 | Tranh chấp không phải khiếu nại trả hàng hoặc hoàn tiền được xử lý trong bao lâu sau khi Shopee nhận đủ tài liệu? | `dispute-resolution-process` chunk 0: bước đầu quy trình | 0,0100 | Chưa đủ; chunk chứa mốc 7 ngày không vào top-3 | Agent mô tả quy trình nhưng thiếu mốc 7 ngày. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 ở lần chạy kỹ thuật bằng mock embedding.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác:** Chưa có dữ liệu demo từ thành viên khác; sẽ bổ sung sau khi mọi thành viên chạy cùng local embedder.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | Chưa đánh giá / 10 |
| **Tổng phần cá nhân tạm thời** | **50 / 60** |
