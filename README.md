# 📖 Đọc Truyện Online

Ứng dụng đọc truyện thông minh với Text-to-Speech, được xây dựng bằng Streamlit.

## ✨ Tính năng

### 🔊 Text-to-Speech
- Đọc truyện bằng giọng nói với Web Speech API
- Hỗ trợ nhiều giọng đọc, ưu tiên giọng Việt
- Điều chỉnh tốc độ và cao độ
- Highlight từ đang đọc

### 📚 Quản lý đọc
- **Bookmarks**: Lưu vị trí đọc để tiếp tục sau
- **Lịch sử**: Theo dõi các truyện đã đọc
- **Yêu thích**: Danh sách truyện yêu thích

### ⚡ Hiệu suất
- Preload thông minh các chương tiếp theo
- Cache nội dung trên disk và memory
- Tải song song nhiều chương

### 🎨 Giao diện
- Thiết kế hiện đại với glassmorphism
- Hỗ trợ Dark/Light mode
- Responsive trên mọi thiết bị

## 🚀 Cài đặt

```bash
# Clone hoặc tải về
cd app_doc_truyen

# Cài dependencies
pip install -r requirements.txt

# Chạy ứng dụng (khuyến nghị)
./run.sh
```

Mặc định app chỉ lắng nghe trên máy hiện tại. Nếu cần mở trong mạng LAN:

```bash
BIND_ADDRESS=0.0.0.0 ./run.sh
```

Chế độ LAN chưa có đăng nhập, vì vậy chỉ nên dùng trong mạng tin cậy; không
mở trực tiếp cổng này ra Internet.

Chỉ các tên miền trong `DOC_TRUYEN_ALLOWED_DOMAINS` được tải. Mặc định là
`truyenhoan.com`; có thể cấu hình nhiều tên miền bằng dấu phẩy:

```bash
DOC_TRUYEN_ALLOWED_DOMAINS=truyenhoan.com,example.com ./run.sh
```

## ⌨️ Phím tắt

| Phím | Chức năng |
|------|-----------|
| F7 | Chương trước |
| F8 | Đọc / Tạm dừng |
| F9 | Chương sau |

## 📁 Cấu trúc thư mục

```
app_doc_truyen/
├── config/           # Cấu hình
│   └── settings.py   # Constants & settings
├── core/             # Logic cốt lõi
│   ├── cache.py      # Caching
│   ├── scraper.py    # Fetch HTML
│   └── chapter.py    # Navigation
├── data/             # Data management
│   ├── bookmarks.py  # Bookmarks
│   ├── history.py    # History
│   └── favorites.py  # Favorites
├── ui/               # UI components
│   ├── styles.py     # CSS styles
│   ├── themes.py     # Theme system
│   └── components/   # UI components
│       ├── sidebar.py
│       └── tts_player.py
├── app.py            # Main entry
├── requirements.txt
└── README.md
```

## 📋 Requirements

- Python 3.10+
- Streamlit
- Requests
- BeautifulSoup4
- Readability-lxml
- lxml

## 🛡️ Độ ổn định khi chạy web

- WebSocket có keep-alive và nén dữ liệu để giao diện tự kết nối lại tốt hơn.
- TTS chia nội dung dài thành các đoạn ngắn và highlight không dựng lại toàn bộ trang.
- Tác vụ tải trước dùng một worker có giới hạn; cache RAM và cache chương đều có giới hạn.
- Ghi cache trên đĩa theo cơ chế atomic để tiến trình bị dừng giữa chừng không làm hỏng cache.

Chạy kiểm thử nhanh trước khi triển khai:

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

## 📝 License

MIT License
