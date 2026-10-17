```markdown
# 🎵🎬 Easy Peasy Chatbot

**Easy Peasy Chatbot** là một bot Telegram thông minh và thân thiện, giúp cải thiện tâm trạng của bạn bằng cách đề xuất âm nhạc từ **Last.fm** và phim ảnh từ **IMDb** dựa trên cảm xúc của bạn.

---

## ✨ Các tính năng chính

1. **Phân tích cảm xúc (Sentiment Analysis):** Sử dụng thư viện `TextBlob` để phân tích phản hồi của bạn đối với các câu hỏi thời tiết, cuộc sống để đưa ra các đề xuất phù hợp.
2. **Gợi ý âm nhạc (Last.fm API):**
   - Đề xuất bài hát theo nghệ sĩ yêu thích của bạn.
   - Nếu không có nghệ sĩ cụ thể, bot sẽ chọn ngẫu nhiên các bài hát dựa theo nhãn (tags) phù hợp với tâm trạng.
   - Cho phép bạn tiếp tục tìm kiếm hoặc chuyển qua phần gợi ý phim.
3. **Gợi ý phim ảnh (IMDb Scraping):**
   - Thu thập dữ liệu phim trực tiếp từ IMDb bằng `BeautifulSoup4`.
   - Cung cấp tiêu đề phim, tóm tắt nội dung (synopsis) và ảnh poster.
   - Gợi ý thể loại Drama nếu bạn đang buồn, hoặc Comedy nếu bạn đang vui.
4. **Nhận phản hồi người dùng:** Bot sẽ hỏi cảm nhận của bạn về chất lượng phục vụ sau khi kết thúc phiên trò chuyện.

---

## 🛠️ Công nghệ và Thư viện sử dụng

- **Ngôn ngữ:** Python 3.x
- **Thư viện chính:**
  - [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) - Giao tiếp với Telegram Bot API.
  - [TextBlob](https://textblob.readthedocs.io/) - Phân tích cú pháp và cảm xúc văn bản.
  - [BeautifulSoup4 (bs4)](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - Cào dữ liệu phim từ IMDb.
  - [Requests](https://requests.readthedocs.io/) - Gửi HTTP requests tới Last.fm API và IMDb.

---

## 🚀 Hướng dẫn cài đặt và sử dụng

### 1. Cài đặt thư viện bắt buộc
Chạy lệnh sau để cài đặt các thư viện cần thiết:
```bash
pip install pyTelegramBotAPI textblob beautifulsoup4 requests
```

### 2. Cấu hình các API Keys
Mở mã nguồn chính và thiết lập mã Token Telegram cùng khóa API Last.fm của bạn:
```python
# Khởi tạo Telegram Bot Token
bot = telebot.TeleBot("YOUR_TELEGRAM_BOT_TOKEN")

# API Last.fm
API_KEY = "YOUR_LASTFM_API_KEY"
API_SECRET = "YOUR_LASTFM_API_SECRET"
```

### 3. Khởi chạy Bot
Chạy tệp Python để khởi động bot:
```bash
python main.py
```
Sau đó, mở Telegram, tìm kiếm bot của bạn và gõ `/start` hoặc bấm nút bắt đầu để trò chuyện.

---

## 📋 Kịch bản trò chuyện của Bot (Flowchart)
1. **/start** -> Bot chào ngẫu nhiên -> Nhấn nút **"Ok. Let's go!!!"**.
2. Trả lời câu hỏi về thời tiết & cảm xúc hiện tại -> Bot phân tích tâm trạng tích cực/tiêu cực.
3. Lựa chọn gợi ý nhạc **(Y/N)**:
   - Nếu **Y**: Nhập tên nghệ sĩ hoặc `none` -> Trả về 10 bài hát -> Hỏi mức độ hài lòng.
4. Lựa chọn gợi ý phim **(Y/N)**:
   - Nếu **Y**: Gợi ý 5 bộ phim từ IMDb dựa theo cảm xúc hiện tại.
5. Đánh giá chất lượng bot -> Tạm biệt!

---

## 🔗 Tài liệu tham khảo
- [Vecna GitHub Repository](https://github.com/ananyathomas/Vecna)
- [Dataquest Last.fm API Tutorial](https://www.dataquest.io/blog/last-fm-api-python/)
```
