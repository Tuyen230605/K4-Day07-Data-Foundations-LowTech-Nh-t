# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Quy định trả hàng, hoàn tiền và giải quyết tranh chấp của Shopee dành cho Người Mua và Người Bán. Corpus gồm 7 tài liệu theo điều/khoản, được tóm lược có truy vết từ 2 trang chính sách chính thức của Shopee.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Các trường hợp được yêu cầu trả hàng hoặc hoàn tiền | [Shopee 77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / 2026-03-11 | 566 | `buyer`, `return-eligibility`, Điều 3.1 |
| 2 | Thời hạn và điều kiện tài khoản khi gửi yêu cầu | [Shopee 77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / 2026-03-11 | 578 | `buyer`, `return-deadline`, Điều 3.2–3.4 |
| 3 | Điều kiện và hạn mức trả hàng COM | [Shopee 77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / 2026-03-11 | 542 | `buyer`, `return-com`, Điều 4 |
| 4 | Thời hạn và quyền phản hồi của Người Bán | [Shopee 77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / 2026-03-11 | 557 | `seller`, `seller-response`, Điều 5 |
| 5 | Đóng gói và bằng chứng cho sản phẩm hoàn trả | [Shopee 77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / 2026-03-11 | 570 | `buyer`, `return-evidence`, Điều 6 |
| 6 | Chi phí vận chuyển hoàn trả và điều kiện hoàn tiền | [Shopee 77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / 2026-03-11 | 642 | `both`, `shipping-refund`, Điều 7–9 |
| 7 | Quy trình giải quyết tranh chấp và xử lý khiếu nại | [Shopee 77265](https://help.shopee.vn/portal/4/article/77265) | 2026-08-03 / 2024-03-15 | 830 | `both`, `dispute-resolution`, Mục 1–2 |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `seller-return-response` | Định danh duy nhất, liên kết gold answer với tài liệu và hỗ trợ xóa toàn bộ chunk của một tài liệu. |
| `title` | string | `Thời hạn và quyền phản hồi của Người Bán` | Giúp đọc và truy vết kết quả. |
| `source_url` | URL | `https://help.shopee.vn/portal/4/article/77251` | Cho phép kiểm tra thông tin tại nguồn chính thức. |
| `retrieved_at` | date | `2026-08-03` | Cho biết thời điểm nhóm lấy dữ liệu. |
| `document_version` | date/string | `2026-03-11` | Phân biệt phiên bản chính sách được dùng để benchmark. |
| `effective_date` | date | `2026-03-11` | Hỗ trợ kiểm tra hiệu lực của quy định. |
| `customer_role` | enum | `buyer`, `seller`, `both` | Cho phép pre-filter đúng đối tượng và giảm nhiễu. |
| `category` | string | `seller-response` | Thu hẹp theo chủ đề như thời hạn, bằng chứng hoặc tranh chấp. |
| `platform` | string | `shopee` | Giữ khả năng mở rộng corpus sang nền tảng khác mà không trộn chính sách. |
| `language` | string | `vi` | Hỗ trợ lọc ngôn ngữ. |
| `source_section` | string | `Điều 5` | Truy vết gold answer đến đúng điều/khoản trên trang nguồn. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `dispute-resolution-process` | FixedSizeChunker (`fixed_size`) | 2 | 252,00 | Một số ranh giới có thể cắt giữa ý. |
| `dispute-resolution-process` | SentenceChunker (`by_sentences`) | 2 | 238,50 | Có, giữ trọn câu nhưng chunk khá dài. |
| `dispute-resolution-process` | RecursiveChunker (`recursive`) | 4 | 118,50 | Giữ ranh giới tự nhiên nhưng ý bị chia nhỏ hơn. |
| `return-com-rules` | FixedSizeChunker (`fixed_size`) | 1 | 225,00 | Có, toàn bộ tài liệu nằm trong một chunk. |
| `return-com-rules` | SentenceChunker (`by_sentences`) | 1 | 225,00 | Có, toàn bộ tài liệu nằm trong một chunk. |
| `return-com-rules` | RecursiveChunker (`recursive`) | 1 | 225,00 | Có, toàn bộ tài liệu nằm trong một chunk. |
| `return-eligibility` | FixedSizeChunker (`fixed_size`) | 1 | 219,00 | Có, toàn bộ tài liệu nằm trong một chunk. |
| `return-eligibility` | SentenceChunker (`by_sentences`) | 1 | 219,00 | Có, toàn bộ tài liệu nằm trong một chunk. |
| `return-eligibility` | RecursiveChunker (`recursive`) | 1 | 219,00 | Có, toàn bộ tài liệu nằm trong một chunk. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Hoàng Minh (2A202601764)**
- **Loại chiến lược:** Custom `HeadingAwareChunker(chunk_size=260)` với `RecursiveChunker` fallback.
- **Mô tả & lý do chọn cho chủ đề này:** Chính sách Shopee được tổ chức theo tiêu đề và điều/khoản, nên heading là ranh giới ngữ nghĩa tự nhiên. Section vượt 260 ký tự được chia recursive; heading được gắn lại vào mọi mảnh con để chunk sau không mất ngữ cảnh.
- **Code snippet (nếu custom):**
```python
sections = re.split(r"(?=^#{1,6}\s+)", text, flags=re.MULTILINE)
for section in sections:
    if len(section) <= self.chunk_size:
        chunks.append(section.strip())
    else:
        pieces = RecursiveChunker(chunk_size=available_size).chunk(body)
        chunks.extend(f"{heading}\n{piece}" for piece in pieces)
```

**Thành viên 2 — Nguyễn Việt Hải**
- **Loại chiến lược:** `SentenceChunker` (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Lựa chọn chiến lược ngắt theo ranh giới câu bằng biểu thức chính quy (`r'(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)'`). Văn bản chính sách TMĐT tiếng Việt có cấu trúc câu quy định thời hạn/điều kiện rất rõ ràng; việc chia theo ranh giới câu giúp đảm bảo từng quy định được giữ nguyên vẹn ngữ nghĩa, không bị ngắt rách từ hay ngắt giữa câu như `FixedSizeChunker`.
- **Code snippet:**
```python
class SentenceChunker:
    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        pattern = r'(?<=\. )|(?<=\! )|(?<=\? )|(?<=\.\n)'
        parts = re.split(pattern, text)
        sentences = [p.strip() for p in parts if p.strip()]
        
        chunks = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sentences = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(chunk_sentences))
        return chunks
```

**Thành viên 3 — Nguyễn Thái Tú (2A202601504)**
- **Loại chiến lược:** `RecursiveChunker` (`chunk_size=200`)
- **Mô tả & lý do chọn:** Sử dụng `RecursiveChunker` với danh sách dấu phân cách theo thứ tự ưu tiên: `\n\n` → `\n` → `. ` → ` ` → `""`. Văn bản chính sách TMĐT thường có các đoạn (paragraph) và câu rõ ràng — chiến lược đệ quy ưu tiên tách tại ranh giới tự nhiên (paragraph, dòng, câu) trước khi phải cắt giữa từ, giúp tối ưu cả tính mạch lạc lẫn kích thước chunk đồng đều (~120-200 ký tự). So với SentenceChunker, RecursiveChunker kiểm soát được `chunk_size` tối đa, tránh chunk quá dài khi tài liệu có câu dài.
- **Code snippet:**
```python
class RecursiveChunker:
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators=None, chunk_size=200):
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text):
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text, remaining_separators):
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]
        if separator == "":
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
        parts = current_text.split(separator)
        chunks, current_chunk = [], ""
        for part in parts:
            if not current_chunk:
                current_chunk = part
            elif len(current_chunk) + len(separator) + len(part) <= self.chunk_size:
                current_chunk += separator + part
            else:
                chunks.append(current_chunk)
                current_chunk = part
        if current_chunk:
            chunks.append(current_chunk)
        final = []
        for c in chunks:
            if len(c) > self.chunk_size:
                final.extend(self._split(c, next_separators))
            else:
                final.append(c)
        return final
```

**Thành viên 4 — [Tên] ([MSSV])**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Thành viên 1 (Nguyễn Hoàng Minh) | Custom HeadingAwareChunker | 10 / 10 | Đã bảo toàn ngữ cảnh tiêu đề cho từng chunk con | Tăng kích thước chunk nếu tiêu đề quá dài |
| Thành viên 2 (Nguyễn Việt Hải) | SentenceChunker | 10 / 10 | Giữ trọn vẹn ngữ nghĩa từng câu chính sách, không rách từ | Độ dài chunk phụ thuộc độ dài câu |
| Thành viên 3 (Nguyễn Thái Tú) | RecursiveChunker(200) | 10 / 10 | Kiểm soát chunk_size tối đa, ưu tiên ranh giới tự nhiên, chunks đều | Có thể tách ý liên quan thành 2 chunk khi gần giới hạn |
| Thành viên 4 | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng hoặc hoàn tiền sau khi đơn hàng được giao thành công? | Thời hạn chung là 15 ngày kể từ khi giao thành công; riêng thực phẩm tươi sống và đông lạnh là 24 giờ. | `return-request-deadline`, Điều 3.2–3.4; filter `customer_role=buyer` |
| 2 | Những trường hợp nào có thể làm căn cứ yêu cầu trả hàng hoặc hoàn tiền? | Gồm không nhận đủ hàng, hàng giả, hàng hư hại, giao sai, khác biệt rõ với mô tả, hết hạn, có thỏa thuận với Người Bán hoặc đủ điều kiện trả hàng COM. | `return-eligibility`, Điều 3.1; filter `customer_role=buyer` |
| 3 | Người bán phải phản hồi yêu cầu trả hàng trong bao lâu và điều gì xảy ra nếu không phản hồi? | Người Bán có 2 ngày lịch kể từ khi nhận thông báo; không phản hồi được hiểu là đồng ý với quyết định xử lý của Shopee. | `seller-return-response`, Điều 5; **filter bắt buộc `customer_role=seller`** |
| 4 | Người mua cần chuẩn bị sản phẩm và bằng chứng như thế nào khi hoàn trả hàng? | Đóng gói đúng quy định, kèm đủ phụ kiện, hóa đơn và tem bảo hành, giữ hàng nguyên vẹn; quay video hoặc chụp ảnh khi nhận và khi đóng gói hoàn trả. | `returned-product-evidence`, Điều 6; filter `customer_role=buyer` |
| 5 | Tranh chấp không phải khiếu nại trả hàng hoặc hoàn tiền được xử lý trong bao lâu sau khi Shopee nhận đủ tài liệu? | Shopee đưa ra hướng giải quyết trong 7 ngày làm việc kể từ khi nhận đủ thông tin và tài liệu; vụ phức tạp có thể kéo dài hơn. | `dispute-resolution-process`, Mục 1; filter `customer_role=both` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
