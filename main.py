## pip install --upgrade google-genai==0.3.0##
import asyncio
import json
import os
import websockets
from google import genai
from google.genai import types
import base64

# Load API key from environment
os.environ['GOOGLE_API_KEY'] = 'AIzaSyBCIzWq0A5MKhRIbj6TREhkNX7DD9mhV-U'
MODEL = "models/gemini-2.5-flash-native-audio-preview-09-2025"

client = genai.Client(
    http_options={'api_version': 'v1beta'},
    api_key=os.environ.get("GOOGLE_API_KEY"),
)

# Config theo Google example
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
)


async def gemini_session_handler(client_websocket: websockets.WebSocketServerProtocol):
    """Handles the interaction with Gemini API within a websocket session.

    Args:
        client_websocket: The websocket connection to the client.
    """
    audio_queue = asyncio.Queue()
    
    try:
        # Nhận config message từ client
        config_message = await client_websocket.recv()
        config_data = json.loads(config_message)
        
        # Tạo config mới kết hợp CONFIG template và system instruction
        session_config = types.LiveConnectConfig(
            response_modalities=CONFIG.response_modalities,
            media_resolution=CONFIG.media_resolution,
            speech_config=CONFIG.speech_config,
            context_window_compression=CONFIG.context_window_compression,
            system_instruction="""You are a helpful assistant for screen sharing sessions. Your role is to: 
                                1) Analyze and describe the content being shared on screen 
                                2) Answer questions about the shared content 
                                3) Provide relevant information and context about what's being shown 
                                4) Assist with technical issues related to screen sharing 
                                5) Maintain a professional and helpful tone. Focus on being concise and clear in your responses."""
        )

        async with client.aio.live.connect(model=MODEL, config=session_config) as session:
            print("Connected to Gemini API")

            async def send_to_gemini():
                """Sends messages from the client websocket to the Gemini API."""
                try:
                    async for message in client_websocket:
                        try:
                            data = json.loads(message)
                            if "realtime_input" in data:
                                for chunk in data["realtime_input"]["media_chunks"]:
                                    mime_type = chunk["mime_type"]
                                    chunk_data = chunk["data"]
                                    
                                    # Gửi theo format mới của Google
                                    await session.send(
                                        input={"mime_type": mime_type, "data": chunk_data}
                                    )

                        except Exception as e:
                            print(f"Error sending to Gemini: {e}")
                    print("Client connection closed (send)")
                except Exception as e:
                    print(f"Error sending to Gemini: {e}")
                finally:
                    print("send_to_gemini closed")

            async def receive_from_gemini():
                """Receives responses from the Gemini API and forwards them to the client."""
                try:
                    while True:
                        try:
                            # Sử dụng session.receive() để lấy turn
                            turn = session.receive()
                            
                            async for response in turn:
                                # Xử lý audio data
                                if data := response.data:
                                    audio_queue.put_nowait(data)
                                    continue
                                
                                # Xử lý text response
                                if text := response.text:
                                    await client_websocket.send(json.dumps({"text": text}))
                                    print(text, end="")
                                
                                # Xử lý turn complete (interruption handling)
                                if response.server_content and response.server_content.turn_complete:
                                    print('\n<Turn complete>')
                                    # Clear audio queue khi bị interrupt
                                    while not audio_queue.empty():
                                        audio_queue.get_nowait()
                                        
                        except websockets.exceptions.ConnectionClosedOK:
                            print("Client connection closed normally (receive)")
                            break
                        except Exception as e:
                            print(f"Error receiving from Gemini: {e}")
                            break

                except Exception as e:
                    print(f"Error receiving from Gemini: {e}")
                finally:
                    print("Gemini connection closed (receive)")

            async def send_audio_to_client():
                """Sends audio from queue to client websocket."""
                try:
                    while True:
                        audio_data = await audio_queue.get()
                        base64_audio = base64.b64encode(audio_data).decode('utf-8')
                        await client_websocket.send(json.dumps({"audio": base64_audio}))
                        print("Audio sent to client")
                except Exception as e:
                    print(f"Error sending audio to client: {e}")
                finally:
                    print("send_audio_to_client closed")

            # Start all tasks
            send_task = asyncio.create_task(send_to_gemini())
            receive_task = asyncio.create_task(receive_from_gemini())
            audio_task = asyncio.create_task(send_audio_to_client())
            
            await asyncio.gather(send_task, receive_task, audio_task)

    except Exception as e:
        print(f"Error in Gemini session: {e}")
    finally:
        print("Gemini session closed.")


async def main() -> None:
    async with websockets.serve(gemini_session_handler, "localhost", 9083):
        print("Running websocket server localhost:9083...")
        await asyncio.Future()  # Keep the server running indefinitely


if __name__ == "__main__":
    asyncio.run(main())