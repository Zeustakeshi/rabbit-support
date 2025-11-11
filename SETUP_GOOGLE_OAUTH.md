# Hướng dẫn cấu hình Google OAuth

## Bước 1: Tạo Google OAuth Client ID

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project có sẵn
3. Vào **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Chọn **Application type**: Web application
6. Điền thông tin:
   - **Name**: Gemini Live Demo (hoặc tên bạn muốn)
   - **Authorized JavaScript origins**: 
     - `http://localhost:5000`
     - `http://127.0.0.1:5000`
   - **Authorized redirect URIs**: (có thể để trống cho ứng dụng này)
7. Click **Create**
8. Copy **Client ID** (dạng: `xxxxx.apps.googleusercontent.com`)

## Bước 2: Lấy Google Gemini API Key

1. Truy cập [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **Create API Key**
3. Copy API key

## Bước 3: Cấu hình file .env

Tạo file `.env` trong thư mục gốc của project:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# Flask Secret Key (tạo random string)
SECRET_KEY=your_random_secret_key_here
```

## Bước 4: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## Bước 5: Chạy ứng dụng

```bash
python app.py
```

Truy cập: http://localhost:5000

## Lưu ý

- Đảm bảo đã thêm đúng **Authorized JavaScript origins** trong Google Cloud Console
- Nếu gặp lỗi CORS, kiểm tra lại cấu hình origins
- Secret key nên là chuỗi ngẫu nhiên dài và phức tạp trong production
