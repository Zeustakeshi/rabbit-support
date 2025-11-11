"""
Script test đơn giản để kiểm tra WebSocket connection
Chạy server trước, sau đó chạy script này
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:5000/ws?token=test123"
    
    try:
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Gửi setup message
            setup = {"setup": {"generation_config": {"response_modalities": ["AUDIO"]}}}
            await websocket.send(json.dumps(setup))
            print("📤 Sent setup message")
            
            # Đợi response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
