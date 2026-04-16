"""
AI Reader — Model Setup Script
Downloads the Kokoro TTS model files if they are not already present.
"""

import os
import sys
import urllib.request

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

FILES = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}


def download_with_progress(url, dest):
    """Download a file with a simple progress indicator."""
    print(f"  Downloading: {os.path.basename(dest)}")
    print(f"  From: {url}")

    def reporthook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 // total_size)
            mb_down = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            bar_len = 30
            filled = int(bar_len * pct / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            sys.stdout.write(f"\r  [{bar}] {pct:3d}%  ({mb_down:.1f} / {mb_total:.1f} MB)")
            sys.stdout.flush()

    urllib.request.urlretrieve(url, dest, reporthook)
    print()  # newline after progress bar


def setup():
    """Download model files if not already present."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    all_present = True
    for filename, url in FILES.items():
        filepath = os.path.join(MODEL_DIR, filename)
        if not os.path.exists(filepath):
            all_present = False
            print(f"\n📥 Model file missing: {filename}")
            download_with_progress(url, filepath)
            print(f"  ✅ Saved to: {filepath}")
        else:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"  ✅ {filename} already exists ({size_mb:.1f} MB)")

    if all_present:
        print("\n🎉 All model files are ready!")
    else:
        print("\n🎉 Download complete! Models are ready.")

    return MODEL_DIR


if __name__ == "__main__":
    print("=" * 50)
    print("  AI Reader — Kokoro TTS Model Setup")
    print("=" * 50)
    setup()
