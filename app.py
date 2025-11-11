from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_session import Session
from flask_sock import Sock
import os
import json
import asyncio
import base64
import secrets
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
sock = Sock(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
Session(app)

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
MODEL = "models/gemini-2.5-flash-native-audio-preview-09-2025"

# Temporary tokens for WebSocket authentication
ws_tokens = {}  # {token: {'user': user_data, 'expires': datetime}}

# Authentication decorator
def require_auth(f):
    """Decorator để kiểm tra user đã đăng nhập"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Gemini client
client = None
if GOOGLE_API_KEY:
    try:
        client = genai.Client(
            http_options={'api_version': 'v1beta'},
            api_key=GOOGLE_API_KEY,
        )
        print("✅ Gemini client initialized")
    except Exception as e:
        print(f"⚠️  Failed to initialize Gemini client: {e}")
else:
    print("⚠️  GOOGLE_API_KEY not set")

# Gemini config
CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Zephyr"
            )
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=25600,
        sliding_window=types.SlidingWindow(target_tokens=12800),
    ),
system_instruction = """BẠN LÀ MỘT GIÁO VIÊN LẬP TRÌNH CHÂN THÀNH, NGỌT NGÀO VÀ KIÊN NHẪN

# VAI TRÒ VÀ PHONG CÁCH:
- Bạn là cô giáo dạy lập trình, xưng "cô" với học sinh và gọi học sinh là "con"
- Giọng nói ấm áp, ngọt ngào, truyền cảm hứng
- Luôn kiên nhẫn, tỉ mỉ giải thích từng bước một
- Khuyến khích, động viên học sinh khi gặp khó khăn

# CHUYÊN MÔN GIẢNG DẠY:
Cô chỉ dạy các môn lập trình sau:
• Scratch - Lập trình kéo thả cho người mới bắt đầu
• Gammaker - Tạo game cơ bản
• Python - Lập trình ứng dụng và game
• HTML/CSS - Thiết kế web cơ bản
• JavaScript - Lập trình web tương tác

# PHÂN TÍCH MÀN HÌNH HỌC SINH:
Khi học sinh share màn hình, cô cần:

1. **PHÂN TÍCH NỘI DUNG HIỂN THỊ**:
   - "Cô thấy con đang làm trên [Scratch/Python/HTML...]"
   - "Con đang viết code về [mô tả chức năng]"
   - "Giao diện hiện tại đang hiển thị [mô tả cửa sổ/tool]"

2. **TRẢ LỜI CÂU HỎI VỀ NỘI DUNG**:
   - "Theo cô thấy trên màn hình, vấn đề của con là..."
   - "Đoạn code này đang gặp lỗi ở chỗ..."
   - "Cô thấy con làm đến bước này rồi, tiếp theo chúng ta sẽ..."

3. **CUNG CẤP NGỮ CẢNH LIÊN QUAN**:
   - "Chức năng này dùng để..."
   - "Trong [môn học], cách tiếp cận này thường dùng cho..."
   - "Cô giải thích ý nghĩa của công cụ này nhé..."

4. **HỖ TRỢ KỸ THUẬT SHARE MÀN HÌNH**:
   - "Cô chưa thấy rõ code, con có thể zoom lại không?"
   - "Phần bên trái màn hình bị che, con di chuyển qua một chút nhé"
   - "Cô thấy có thông báo lỗi ở góc phải, con click vào đó xem nào"

5. **GIỌNG ĐIỆU CHUYÊN NGHIỆP & RÕ RÀNG**:
   - Luôn mô tả cụ thể, tránh nói chung chung
   - Sử dụng thuật ngữ phù hợp với trình độ học sinh
   - Diễn đạt ngắn gọn, dễ hiểu

# PHƯƠNG PHÁP GIẢNG DẠY (Chain of Thought):
Khi giải thích bài tập qua màn hình, cô luôn tuân thủ:
1. **QUAN SÁT**: "Cô thấy trên màn hình con đang..."
2. **PHÂN TÍCH**: "Theo cô, vấn đề ở đây là..."
3. **HƯỚNG DẪN TỪNG BƯỚC**: "Đầu tiên, con thử... sau đó..."
4. **KIỂM TRA**: "Con làm xong bước đó chưa? Cô thấy trên màn hình..."
5. **ĐÁNH GIÁ**: "Tuyệt quá! Cô thấy code đã chạy được rồi!"

# QUY TẮC ỨNG XỬ:
• LUÔN tích cực: "Con làm tốt lắm!", "Cô rất tự hào về con!"
• KIÊN NHẪN: "Không sao đâu con, cô thấy màn hình có lỗi là chuyện bình thường"
• TẬP TRUNG VÀO MÀN HÌNH: Luôn tham chiếu đến nội dung đang hiển thị
• HỖ TRỢ TRỰC QUAN: "Con nhìn vào góc trái màn hình, thấy cái nút đó không?"

# HẠN CHẾ:
• CHỈ trả lời câu hỏi về 5 môn lập trình đã liệt kê
• KHI gặp câu hỏi ngoài phạm vi: "Cô xin lỗi, hiện tại cô chỉ dạy các môn Scratch, Gammaker, Python, HTML/CSS và JavaScript thôi con ạ. Con muốn học về môn nào trong này không?"

# MẪU CÂU GIAO TIẾP KHI XEM MÀN HÌNH:
- "Cô thấy con đang code Python, hàm này viết khá tốt đó!"
- "Ở góc trên bên phải màn hình có lỗi syntax, con để ý chưa?"
- "Cô chưa thấy rõ phần code, con có thể scroll xuống dưới được không?"
- "Theo cô quan sát màn hình, bước tiếp theo con nên làm là..."
- "Tuyệt vời! Cô thấy trên màn hình output đã chạy đúng rồi!"

Hãy luôn chú ý đến nội dung màn hình học sinh đang share và cung cấp hỗ trợ trực quan, chi tiết!"""
)

@app.route('/')
def index():
    """Trang đăng nhập"""
    if 'user' in session:
        return redirect(url_for('app_page'))
    return render_template('login.html', google_client_id=GOOGLE_CLIENT_ID)

@app.route('/app')
@require_auth
def app_page():
    """Trang ứng dụng chính"""
    return render_template('app.html')

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Xác thực Google ID token"""
    try:
        data = request.get_json()
        token = data.get('credential')
        
        if not token:
            return jsonify({"error": "Token required"}), 400
        
        # Verify token với Google
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Lưu thông tin user vào session
        session['user'] = {
            'id': idinfo['sub'],
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', '')
        }
        
        return jsonify({
            "success": True,
            "user": session['user']
        })
        
    except ValueError as e:
        return jsonify({"error": "Invalid token", "details": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Đăng xuất"""
    session.pop('user', None)
    return jsonify({"success": True})

@app.route('/api/auth/user', methods=['GET'])
def get_user():
    """Lấy thông tin user hiện tại"""
    if 'user' in session:
        return jsonify(session['user'])
    return jsonify({"error": "Not authenticated"}), 401

@app.route('/api/auth/ws-token', methods=['GET'])
def get_ws_token():
    """Tạo temporary token cho WebSocket connection"""
    if 'user' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Tạo token ngẫu nhiên
    token = secrets.token_urlsafe(32)
    
    # Lưu token với thời gian hết hạn 5 phút
    ws_tokens[token] = {
        'user': session['user'],
        'expires': datetime.now() + timedelta(minutes=5)
    }
    
    # Cleanup expired tokens
    expired_tokens = [t for t, data in ws_tokens.items() if data['expires'] < datetime.now()]
    for t in expired_tokens:
        del ws_tokens[t]
    
    return jsonify({"token": token})

@sock.route('/ws')
def websocket_route(ws):
    """WebSocket endpoint cho Gemini"""
    print("🔌 WebSocket connection attempt")
    
    # Lấy token từ query parameter (cần parse manually với flask-sock)
    # Token sẽ được validate ở client side trước khi connect
    
    try:
        # Nhận setup message
        print("⏳ Waiting for setup message from client...")
        setup_msg = ws.receive(timeout=10)
        print(f"✅ Received setup: {setup_msg}")
        
        # Parse setup message để lấy token
        try:
            setup_data = json.loads(setup_msg)
            token = setup_data.get('token')
            
            if not token or token not in ws_tokens:
                print("❌ Invalid or missing token in setup")
                ws.send(json.dumps({"error": "Invalid token"}))
                return
            
            # Kiểm tra token còn hạn không
            token_data = ws_tokens[token]
            if token_data['expires'] < datetime.now():
                print("❌ Token expired")
                del ws_tokens[token]
                ws.send(json.dumps({"error": "Token expired"}))
                return
            
            user_email = token_data['user']['email']
            print(f"✅ Authenticated user: {user_email}")
            
            # Xóa token sau khi sử dụng
            del ws_tokens[token]
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Invalid setup message: {e}")
            ws.send(json.dumps({"error": "Invalid setup message"}))
            return
        
        # Tạo async loop cho session
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def handle_gemini_session():
            if not client:
                print("❌ Gemini client not initialized")
                ws.send(json.dumps({"error": "Gemini API not configured"}))
                return
            
            audio_queue = asyncio.Queue()
            
            async with client.aio.live.connect(model=MODEL, config=CONFIG) as gemini_session:
                print("Connected to Gemini API")
                
                async def receive_from_client():
                    """Nhận messages từ client và gửi đến Gemini"""
                    try:
                        while True:
                            try:
                                message = await loop.run_in_executor(None, ws.receive)
                                if message is None:
                                    break
                                    
                                data = json.loads(message)
                                if "realtime_input" in data:
                                    for chunk in data["realtime_input"]["media_chunks"]:
                                        mime_type = chunk["mime_type"]
                                        chunk_data = chunk["data"]
                                        
                                        await gemini_session.send(
                                            input={"mime_type": mime_type, "data": chunk_data}
                                        )
                            except Exception as e:
                                print(f"Error receiving from client: {e}")
                                break
                    except Exception as e:
                        print(f"Error in receive_from_client: {e}")
                
                async def send_to_client():
                    """Nhận responses từ Gemini và gửi đến client"""
                    try:
                        while True:
                            try:
                                turn = gemini_session.receive()
                                
                                async for response in turn:
                                    if data := response.data:
                                        audio_queue.put_nowait(data)
                                        continue
                                    
                                    if text := response.text:
                                        await loop.run_in_executor(
                                            None, 
                                            ws.send, 
                                            json.dumps({"text": text})
                                        )
                                        print(text, end="")
                                    
                                    if response.server_content and response.server_content.turn_complete:
                                        print('\n<Turn complete>')
                                        while not audio_queue.empty():
                                            audio_queue.get_nowait()
                                            
                            except Exception as e:
                                print(f"Error in send_to_client: {e}")
                                break
                    except Exception as e:
                        print(f"Error receiving from Gemini: {e}")
                
                async def send_audio():
                    """Gửi audio từ queue đến client"""
                    try:
                        while True:
                            audio_data = await audio_queue.get()
                            base64_audio = base64.b64encode(audio_data).decode('utf-8')
                            await loop.run_in_executor(
                                None,
                                ws.send,
                                json.dumps({"audio": base64_audio})
                            )
                            print("Audio sent to client")
                    except Exception as e:
                        print(f"Error sending audio: {e}")
                
                await asyncio.gather(
                    receive_from_client(),
                    send_to_client(),
                    send_audio()
                )
        
        loop.run_until_complete(handle_gemini_session())
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Gemini Live Demo Server")
    print("=" * 50)
    print(f"📱 Web Interface: http://localhost:5000")
    print(f"🔌 WebSocket: ws://localhost:5000/ws")
    print(f"🔑 Google Client ID: {GOOGLE_CLIENT_ID[:30]}..." if GOOGLE_CLIENT_ID else "⚠️  Google Client ID not set!")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
