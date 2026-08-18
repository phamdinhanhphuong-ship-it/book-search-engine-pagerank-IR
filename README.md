

## Báo cáo dự án: Xây dựng hệ thống tìm kiếm thông tin sách bằng crawl, PageRank và mô hình ranking

### 1. Giới thiệu
Dự án này tập trung vào việc xây dựng một hệ thống tìm kiếm thông tin sách dựa trên dữ liệu thu thập từ website Books to Scrape. Mục tiêu chính là tạo ra một pipeline hoàn chỉnh để crawl dữ liệu, xây dựng chỉ mục, tính toán PageRank, kết hợp với tìm kiếm theo từ khóa và đánh giá hiệu quả của hệ thống.

Hệ thống không chỉ đơn thuần tìm kiếm theo văn bản, mà còn kết hợp thêm thông tin cấu trúc liên kết giữa các trang để nâng cao chất lượng xếp hạng. Đây là hướng tiếp cận điển hình của truy hồi thông tin hiện đại, nơi độ hữu ích của một tài liệu không chỉ phụ thuộc vào nội dung mà còn phụ thuộc vào mức độ quan trọng của nó trong mạng liên kết.

---

### 2. Mục tiêu của bài toán
Mục tiêu của dự án là:
- Thu thập dữ liệu sách từ nguồn web có cấu trúc rõ ràng.
- Tạo một tập dữ liệu đủ lớn, đa dạng và có tính thực tiễn hơn so với phiên bản ban đầu.
- Xây dựng đồ thị liên kết giữa các trang sách.
- Tính toán PageRank để xác định độ quan trọng của từng tài liệu.
- Xây dựng inverted index để thực hiện tìm kiếm theo từ khóa.
- Kết hợp điểm lexical và PageRank để tăng chất lượng xếp hạng.
- Đánh giá kết quả bằng các tiêu chuẩn của IR như P@10, Recall@100 và NDCG@10.
- Cải thiện và hoàn thiện pipeline từ giai đoạn prototype tới version gần như hoàn chỉnh.

---

### 3. Phương pháp thực hiện

#### 3.1. Crawl dữ liệu
Quá trình crawl được thực hiện từ các URL seed ban đầu, sau đó thu thập các trang nội dung liên quan. Trong quá trình cải tiến, hệ thống đã:
- tăng số lượng seed URL,
- loại bỏ các link điều hướng không cần thiết,
- bỏ các link login, basket, search, duplicate và self-link,
- giới hạn crawl theo domain của website để tránh rác.

Việc này giúp dữ liệu thu thập được có tính phù hợp hơn và ít bị nhiễu.

#### 3.2. Xây dựng đồ thị liên kết
Sau khi crawl dữ liệu, mỗi tài liệu được biểu diễn như một node. Nếu tài liệu A có liên kết tới tài liệu B thì thêm một directed edge A → B. Đồng thời:
- bỏ self-loop,
- bỏ các liên kết không hợp lệ,
- lọc các edge không phản ánh nội dung thực sự.

Đây là bước quan trọng để PageRank hoạt động tốt hơn.

#### 3.3. Tính toán PageRank
PageRank được áp dụng trên đồ thị liên kết đã được xây dựng. Thuật toán này xác định tài liệu nào có độ quan trọng cao hơn dựa trên số lượng và chất lượng liên kết tới nó.

Các cải tiến quan trọng bao gồm:
- tăng damping factor tới giá trị chuẩn 0.85,
- tăng số vòng lặp tối đa cho hội tụ,
- cải thiện độ tin cậy của đồ thị đầu vào.

#### 3.4. Xây dựng inverted index
Sau khi đã có tài liệu, hệ thống tiến hành tokenize văn bản, đếm tần suất từ và tính IDF. Từ đó, xây dựng inverted index để tìm kiếm các tài liệu chứa từ khóa truy vấn nhanh chóng và hiệu quả.

#### 3.5. Tìm kiếm kết hợp
Hệ thống sử dụng kết hợp giữa:
- lexical score: độ phù hợp theo từ khóa,
- PageRank score: độ quan trọng của tài liệu trong mạng liên kết.

Cách kết hợp này giúp tránh việc chỉ dựa vào từ khóa làm sai lệch kết quả, đồng thời giữ được tính chất quan trọng của tài liệu trong đồ thị liên kết.

#### 3.6. Học máy LTR
Ngoài các phương pháp cơ bản, dự án cũng triển khai mô hình Learning to Rank, sử dụng các feature như:
- điểm lexical,
- PageRank,
- độ dài tài liệu,
- số lượng từ khớp,
- các chỉ số thống kê khác.

Mục tiêu là xếp hạng lại kết quả tìm kiếm tốt hơn theo dữ liệu thực nghiệm.

---

### 4. Kết quả đạt được

Sau khi cải tiến pipeline, hệ thống đã hoạt động thành công với dữ liệu mới. Các kết quả thực tế thu được như sau:

- Số lượng tài liệu trong graph: 567 documents
- Số lượng edge: 4121
- Pipeline crawl + index + PageRank + retrieval chạy ổn định
- Các metric đánh giá cho các phương pháp đã được thu thập rõ ràng

Bảng so sánh kết quả:

| Method | P@10 | Recall@100 | NDCG@10 |
|---|---:|---:|---:|
| ltr | 0.0600 | 0.3310 | 0.1890 |
| w0.0 | 0.1200 | 0.4821 | 0.4591 |
| w1.0 | 0.0900 | 0.4012 | 0.2845 |
| w5.0 | 0.1100 | 0.4321 | 0.2659 |

Nhận xét:
- Hệ thống đã chạy ổn định và có số liệu thật.
- Phương pháp đạt hiệu quả tốt nhất hiện tại là w0.0 và không hoàn toàn phụ thuộc vào PageRank.
- LTR chưa đạt hiệu quả tối ưu hiện tại do tập query/qrels còn hạn chế.
- Tuy nhiên, hệ thống đã tiến xa hơn rất nhiều so với bản đầu.

---

### 5. Những cải tiến quan trọng so với phiên bản đầu
So với bản nguyên mẫu, dự án đã sửa lại nhiều điểm trọng yếu:
- tăng dự liệu crawl và tập tài liệu,
- loại bỏ link điều hướng làm nhiễu,
- tăng tính hợp lý của graph,
- cải thiện PageRank,
- xây dựng lại cách kết hợp score,
- cải thiện ổn định của pipeline,
- chuẩn bị nền tảng cho LTR tốt hơn.

Đây là những thay đổi cần thiết để dự án không còn là hệ thống “quá nhỏ và quá đơn giản”, mà trở thành một pipeline thực tế của truy hồi thông tin.

---

### 6. Hạn chế còn tồn tại
Mặc dù hệ thống đã đạt được nhiều tiến bộ, vẫn còn một số hạn chế:
- tập truy vấn còn ít,
- qrels còn chưa đủ phong phú,
- lượng tài liệu crawl thực tế chưa đạt mức kỳ vọng 1000 page như mục tiêu lý tưởng,
- LTR chưa phát huy tối đa vì dữ liệu đánh giá chưa đủ mạnh.

Vì vậy, hướng phát triển tiếp theo cần tập trung vào:
- mở rộng tập truy vấn,
- tăng chất lượng qrels,
- cải thiện chiến lược crawl theo detail pages,
- tối ưu hơn nữa feature cho mô hình LTR.

---

### 7. Kết luận
Dự án đã xây dựng được một hệ thống tìm kiếm thông tin sách hoàn chỉnh ở mức cơ bản và khá chặt chẽ: từ crawl dữ liệu, xây dựng graph, PageRank, inverted index, retrieval và đánh giá thực nghiệm. Các cải tiến đã giúp tăng đáng kể chất lượng của dữ liệu đầu vào và độ ổn định của hệ thống so với phiên bản ban đầu.

Mức hiệu suất hiện tại chưa phải là tối ưu hoàn hảo, nhưng đây là một nền tảng vững chắc cho những đợt cải tiến tiếp theo. Với việc tăng thêm query, qrels và tối ưu crawl, hệ thống hoàn toàn có khả năng nâng cao chất lượng tìm kiếm đáng kể trong tương lai.

---

