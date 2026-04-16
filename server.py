"""
AI Reader — TTS Backend Server
Provides Kokoro TTS API endpoints. Runs as an internal service on localhost.
"""

import io
import os
import sys
import time
import socket
import threading
import logging

import onnxruntime as ort
from kokoro_onnx import Kokoro
import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify, Response

# ── Setup paths ──────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    try:
        for path in [BASE_DIR, os.path.join(BASE_DIR, "onnxruntime", "capi")]:
            if os.path.exists(path):
                os.add_dll_directory(path)
    except Exception:
        pass
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(MODEL_DIR, "voices-v1.0.bin")

# ── Available voices ─────────────────────────────────────
VOICES = [
    {"id": "af_sarah",   "name": "Sarah",   "gender": "Female", "accent": "American", "style": "Clear & natural"},
    {"id": "af_bella",   "name": "Bella",   "gender": "Female", "accent": "American", "style": "Warm & friendly"},
    {"id": "af_nicole",  "name": "Nicole",  "gender": "Female", "accent": "American", "style": "Expressive"},
    {"id": "af_sky",     "name": "Sky",     "gender": "Female", "accent": "American", "style": "Bright & cheerful"},
    {"id": "am_adam",    "name": "Adam",    "gender": "Male",   "accent": "American", "style": "Confident"},
    {"id": "am_michael", "name": "Michael", "gender": "Male",   "accent": "American", "style": "Deep & warm"},
    {"id": "bf_emma",    "name": "Emma",    "gender": "Female", "accent": "British",  "style": "Elegant"},
    {"id": "bm_george",  "name": "George",  "gender": "Male",   "accent": "British",  "style": "Refined"},
]

# ── Kokoro TTS Engine (lazy-loaded) ──────────────────────
kokoro = None
kokoro_lock = threading.Lock()

def get_kokoro():
    """Lazy-load Kokoro TTS engine with safe sequential CPU execution."""
    global kokoro
    if kokoro is None:
        with kokoro_lock:
            if kokoro is None:
                # Check models exist
                if not os.path.exists(MODEL_PATH) or not os.path.exists(VOICES_PATH):
                    print("⚠️  Model files not found. Running setup...")
                    setup_path = os.path.join(BASE_DIR, "setup.py")
                    if os.path.exists(setup_path):
                        from setup import setup
                        setup()

                print("🔄 Loading Kokoro TTS model (STRICT SEQUENTIAL CPU MODE)...")
                load_start = time.time()
                
                try:
                    # ──────────────────────────────────────────────────────
                    # ABSOLUTE PATH FIX: Force Espeak Configuration
                    # This ensures the frozen app finds its internal binaries
                    # ──────────────────────────────────────────────────────
                    from kokoro_onnx import EspeakConfig
                    
                    # Point to the 'espeak' folder we manually bundled in build.ps1
                    espeak_dir = os.path.join(BASE_DIR, "espeak")
                    
                    # espeakng-loader on Windows uses 'espeak-ng.dll'
                    lib_path = os.path.join(espeak_dir, "espeak-ng.dll")
                    
                    # Check for existence before failing
                    if not os.path.exists(lib_path):
                        print(f"⚠️  Speech library not found: {lib_path}")
                        # Fallback to simple init if manual path fails
                        kokoro = Kokoro(MODEL_PATH, VOICES_PATH)
                    else:
                        print(f"📌 Using manual speech config: {espeak_dir}")
                        config = EspeakConfig(lib_path=lib_path, data_path=espeak_dir)
                        kokoro = Kokoro(MODEL_PATH, VOICES_PATH, espeak_config=config)
                    # ──────────────────────────────────────────────────────
                    
                    load_time = time.time() - load_start
                    print(f"✅ Kokoro TTS loaded in {load_time:.1f}s")
                except Exception as e:
                    print(f"❌ Error initializing AI engine: {e}")
                    raise
    return kokoro


# ── Flask App ────────────────────────────────────────────
app = Flask(__name__)

# Suppress Flask request logs
log = logging.getLogger("werkzeug")
log.setLevel(logging.WARNING)

# Track generation state
generation_lock = threading.Lock()
should_stop = threading.Event()


@app.route("/api/voices", methods=["GET"])
def get_voices():
    """Return list of available voices."""
    return jsonify({"voices": VOICES})


@app.route("/api/speak", methods=["POST"])
def speak():
    """Generate speech from text and return WAV audio."""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    voice = data.get("voice", "af_sarah")
    speed = float(data.get("speed", 1.0))
    speed = max(0.5, min(3.0, speed))

    valid_voices = {v["id"] for v in VOICES}
    if voice not in valid_voices:
        voice = "af_sarah"

    should_stop.clear()

    try:
        with generation_lock:
            tts = get_kokoro()
            print(f"🎙️  Generating: voice={voice}, speed={speed:.1f}, {len(text)} chars")
            gen_start = time.time()

            max_chunk_chars = 2000
            chunks = split_text_into_chunks(text, max_chunk_chars)

            all_samples = []
            sample_rate = 24000

            for i, chunk in enumerate(chunks):
                if should_stop.is_set():
                    print("⛔ Generation stopped")
                    return jsonify({"error": "Stopped"}), 499

                samples, sr = tts.create(
                    chunk, voice=voice, speed=speed, lang="en-us"
                )
                sample_rate = sr
                all_samples.append(samples)

                if i < len(chunks) - 1:
                    silence = np.zeros(int(sample_rate * 0.3), dtype=samples.dtype)
                    all_samples.append(silence)

            final_audio = np.concatenate(all_samples)

            gen_time = time.time() - gen_start
            duration = len(final_audio) / sample_rate
            print(f"✅ {duration:.1f}s audio in {gen_time:.1f}s (RTF: {gen_time/duration:.2f})")

            buf = io.BytesIO()
            sf.write(buf, final_audio, sample_rate, format="WAV", subtype="PCM_16")
            buf.seek(0)

            return Response(
                buf.read(),
                mimetype="audio/wav",
                headers={
                    "Content-Type": "audio/wav",
                    "X-Audio-Duration": str(round(duration, 2)),
                    "X-Generation-Time": str(round(gen_time, 2)),
                }
            )

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def stop():
    """Signal any ongoing generation to stop."""
    should_stop.set()
    return jsonify({"status": "stopped"})


@app.route("/api/translate", methods=["POST"])
def translate():
    """Translate text using Google Translate (online, free)."""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    target_lang = data.get("target", "en")
    source_lang = data.get("source", "auto")

    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source_lang, target=target_lang)

        # Chunk long texts (Google Translate limit ~5000 chars)
        if len(text) > 4500:
            chunks = split_text_into_chunks(text, 4500)
            translated_chunks = [translator.translate(c) for c in chunks]
            translated = " ".join(translated_chunks)
        else:
            translated = translator.translate(text)

        print(f"🌐 Translated {len(text)} chars → {target_lang}")
        return jsonify({
            "translated": translated,
            "source": source_lang,
            "target": target_lang
        })

    except Exception as e:
        print(f"❌ Translation error: {e}")
        return jsonify({"error": f"Translation failed: {str(e)}"}), 500


@app.route("/api/translate/languages", methods=["GET"])
def translate_languages():
    """Return list of supported languages."""
    try:
        from deep_translator import GoogleTranslator
        langs = GoogleTranslator().get_supported_languages(as_dict=True)
        return jsonify({"languages": langs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def split_text_into_chunks(text, max_chars=2000):
    """Split text into chunks at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk = ""
    sentences = []
    current_sentence = ""

    for char in text:
        current_sentence += char
        if char in ".!?\n" and len(current_sentence.strip()) > 0:
            sentences.append(current_sentence)
            current_sentence = ""
    if current_sentence.strip():
        sentences.append(current_sentence)

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


def find_free_port():
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port=0):
    """Start the Flask TTS server in a background thread. Returns the port."""
    if port == 0:
        port = find_free_port()

    server_thread = threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1", port=port, debug=False, threaded=True
        ),
        daemon=True,
    )
    server_thread.start()

    # Wait for server to be ready
    import urllib.request
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/voices")
            break
        except Exception:
            time.sleep(0.1)

    print(f"🌐 TTS server running on port {port}")
    return port


# Allow standalone testing
if __name__ == "__main__":
    port = start_server()
    print(f"Server running at http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
