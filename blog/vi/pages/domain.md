Trang này là một khóa học về xử lý tín hiệu số, được viết bởi một người làm firmware cho các sản phẩm **optical DSP** — những con chip biến ánh sáng trong sợi quang thành bit mà một mạng có thể định tuyến.

Phần lớn tài liệu dạy DSP bắt đầu bằng phép biến đổi rồi mới tới ứng dụng, nếu có tới được. Khóa này đi theo chiều ngược lại. Mỗi chương bắt đầu bằng một hình vẽ, chỉ suy diễn đúng những gì hình vẽ đó đòi hỏi, rồi kết thúc ở cùng một nơi: bên trong một bộ thu phải theo kịp một tuyến quang 64 GBd.

## Lĩnh vực này thực sự là gì

Một tuyến quang mang dữ liệu bằng cách điều chế ánh sáng. Ở đầu bên kia, một photodiode biến ánh sáng đó trở lại thành dòng điện, một ADC biến dòng điện thành các con số, và kể từ khoảnh khắc đó tín hiệu **chỉ còn là một dãy số** — và mọi khiếm khuyết còn lại đều phải được gỡ bỏ bằng phép tính.

Phép tính đó chính là lĩnh vực này. Tán sắc màu làm nhòe một xung qua hàng chục chu kỳ ký hiệu, nên nó bị đảo ngược bằng một bộ cân bằng miền tần số dựng trên FFT. Phân cực trôi và trộn hai luồng thu được, nên một bộ bướm thích nghi mù gỡ rối chúng. Laser có độ rộng vạch, nên chòm sao quay và một bộ bám pha sóng mang đi theo nó. Sợi quang là phi tuyến, nên méo phụ thuộc vào chính công suất của tín hiệu.

Lý do đây là một góc kỹ thuật đáng làm là vì **phép tính không miễn phí**. Một tuyến 64 GBd cho bạn 15.6 ps mỗi ký hiệu. Mỗi tap của bộ cân bằng tốn những phép nhân thật ở 128 GSa/s, mỗi tầng FFT thêm vào tốn công suất, và mỗi khối đệm tốn độ trễ mà giao thức nhìn thấy được. Tính đúng đắn là điều kiện tối thiểu; câu hỏi thiết kế luôn là thuật toán đúng nào thì vừa.

## Khóa học này được xếp như thế nào

Nó được chia thành tám phần, và thứ tự là có chủ đích:

- **Nhập môn** — tín hiệu là gì, lấy mẫu mất thông tin ra sao, lượng tử hóa tốn kém thế nào, và kỹ sư đếm bằng decibel như thế nào.
- **Trung cấp** — miền tần số, thiết kế bộ lọc và xử lý đa tốc độ: những công cụ mà mọi chương sau đều giả định là đã có.
- **Nâng cao** — ước lượng, thích nghi và DSP truyền thông: phải làm gì khi kênh truyền chưa biết và đang trôi.
- **Chuyên sâu** — chính tuyến quang, và cách làm cho bất kỳ phần nào ở trên vừa vào silicon đúng tốc độ và trong ngân sách công suất.

Các mạch kiến thức này tích lũy dần. Một chương về biến đổi Fourier nhanh không phải là phần đọc thêm cho chương tán sắc — nó chính là thứ khiến chương đó trở nên khả thi về chi phí.

## Dành cho ai

Những kỹ sư nhúng và firmware cần nửa xử lý tín hiệu trong hệ thống của mình thôi là một hộp đen. Những người chuyển sang quang, RF hoặc truyền nối tiếp tốc độ cao từ nền tảng phần mềm. Và bất kỳ ai từng đọc một cuốn sách giáo khoa DSP, hiểu nó ngay lúc đó, rồi một tháng sau không dựng lại được gì — đó chính là kiểu thất bại mà khóa học này được xây dựng riêng để tránh, bằng cách vẽ trước và suy diễn sau.
