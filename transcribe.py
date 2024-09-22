import os
import json
import pyaudio
import websocket
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define Wit.ai API keys for languages
LANGUAGE_API_KEYS = {
    'EN': os.getenv('WIT_API_KEY_ENGLISH'),
    'AR': os.getenv('WIT_API_KEY_ARABIC'),
    'FR': os.getenv('WIT_API_KEY_FRENCH'),
}

# Check if at least one API key is provided
if not any(LANGUAGE_API_KEYS.values()):
    print("Error: At least one Wit.ai API key must be provided in the .env file.")
    sys.exit(1)

# Real-time transcription parameters
RATE = 16000  # Sample rate
CHUNK = 1024  # Size of audio chunks

def on_message(ws, message):
    """Callback for processing transcription results."""
    data = json.loads(message)
    if 'text' in data:
        print(f"Transcribed text: {data['text']}")

def on_error(ws, error):
    """Callback for handling errors."""
    print(f"Error occurred: {error}")

def on_close(ws):
    """Callback for closing WebSocket."""
    print("### Connection closed ###")

def on_open(ws):
    """Send the real-time audio stream to the WebSocket."""
    def run(*args):
        # Initialize PyAudio for real-time audio capture
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)

        print("Streaming audio...")

        try:
            while True:
                # Read audio data in small chunks
                data = stream.read(CHUNK)
                ws.send(data, websocket.ABNF.OPCODE_BINARY)
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            ws.close()
            print("Audio stream stopped.")

    threading.Thread(target=run).start()

def start_real_time_transcription(language_sign):
    """Start real-time transcription with Wit.ai for the specified language."""
    wit_api_key = LANGUAGE_API_KEYS.get(language_sign.upper())
    if not wit_api_key:
        print(f"API key not found for language: {language_sign}")
        return

    # Create the WebSocket URL for Wit.ai real-time streaming
    url = f"wss://api.wit.ai/speech_ws?access_token={wit_api_key}"

    # Set up WebSocket connection
    ws = websocket.WebSocketApp(url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    # Open the WebSocket connection and start streaming audio
    ws.on_open = on_open
    ws.run_forever()

def main():
    language_sign = input("Enter the language sign (e.g., EN, AR, FR): ").strip().upper()

    print(f"Starting real-time transcription for language: {language_sign}")
    start_real_time_transcription(language_sign)

if __name__ == "__main__":
    main()
