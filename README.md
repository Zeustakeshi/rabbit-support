# Gemini Live Demo với Google OAuth

Ứng dụng demo Gemini Live với tính năng đăng nhập Google OAuth.

## Tính năng

- ✅ Đăng nhập bằng Google OAuth
- ✅ Bảo vệ route - chỉ user đã đăng nhập mới truy cập được
- ✅ Hiển thị thông tin user và avatar
- ✅ Screen sharing
- ✅ Voice chat với Gemini AI
- ✅ Real-time audio streaming
- ✅ Giao diện Material Design

## Cài đặt

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình Google OAuth

Xem hướng dẫn chi tiết trong file [SETUP_GOOGLE_OAUTH.md](SETUP_GOOGLE_OAUTH.md)

Tóm tắt:
- Tạo OAuth Client ID tại [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Lấy Gemini API Key tại [Google AI Studio](https://aistudio.google.com/apikey)

### 3. Tạo file .env

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# Flask Secret Key
SECRET_KEY=your_random_secret_key
```

### 4. Chạy ứng dụng

```bash
python app.py
```

Truy cập: http://localhost:5000

## Cấu trúc dự án

```
.
├── app.py                      # Server chính (Flask + WebSocket + Gemini)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (không commit)
├── .env.example               # Template cho .env
├── SETUP_GOOGLE_OAUTH.md      # Hướng dẫn cấu hình Google OAuth
├── templates/
│   ├── login.html             # Trang đăng nhập
│   └── app.html               # Trang ứng dụng chính
└── static/
    ├── styles.css             # CSS styles
    └── pcm-processor.js       # Audio processor
```

## API Endpoints

- `GET /` - Trang đăng nhập
- `GET /app` - Trang ứng dụng chính (yêu cầu đăng nhập)
- `POST /api/auth/google` - Xác thực Google token
- `POST /api/auth/logout` - Đăng xuất
- `GET /api/auth/user` - Lấy thông tin user hiện tại
- `WS /ws` - WebSocket endpoint cho Gemini (yêu cầu đăng nhập)

## Lưu ý

- Tất cả chạy trên 1 server duy nhất tại port 5000
- WebSocket endpoint: ws://localhost:5000/ws
- Session được lưu trong filesystem (Flask-Session)
- Đảm bảo đã cấu hình đúng Authorized JavaScript origins trong Google Cloud Console
