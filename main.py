"""
AI Reader — Main Application Entry Point
IMPORTANT: Loads Kokoro/ONNX Runtime BEFORE PyQt6 to avoid DLL conflicts.
"""

import sys
import os

# Fix Windows console encoding for emoji/unicode output
if sys.platform == 'win32':
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    else:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')
    if sys.stderr is not None:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    else:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')

# ──────────────────────────────────────────────────────
# CRITICAL: DLL Pre-loading for Windows
# ──────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    import ctypes
    BASE_DIR = sys._MEIPASS
    
    # Add root and _internal to DLL search path
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(BASE_DIR)
        for sub in ["_internal", "onnxruntime/capi"]:
            p = os.path.join(BASE_DIR, sub)
            if os.path.exists(p): os.add_dll_directory(p)
    
    # ──────────────────────────────────────────────────────
    # CRITICAL: Force single-threaded mode to prevent PC Lag
    # ──────────────────────────────────────────────────────
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["ORT_TBB_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    # ──────────────────────────────────────────────────────

    # Pre-load core ONNX DLL to satisfy initialization routine
    try:
        # Try root first, then _internal subfolders
        candidates = [
            os.path.join(BASE_DIR, "onnxruntime.dll"),
            os.path.join(BASE_DIR, "_internal", "onnxruntime", "capi", "onnxruntime.dll"),
            os.path.join(BASE_DIR, "onnxruntime", "capi", "onnxruntime.dll")
        ]
        
        for dll_path in candidates:
            if os.path.exists(dll_path):
                print(f"📦 Pre-loading AI engine core from {dll_path}...")
                ctypes.WinDLL(dll_path)
                print("✅ AI engine core pre-loaded.")
                break
    except Exception as e:
        print(f"⚠️  Pre-load diagnostic: {e}")

    os.environ['PATH'] = BASE_DIR + os.pathsep + os.environ.get('PATH', '')
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ──────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────
# CRITICAL: Load ONNX Runtime + Kokoro FIRST
# ──────────────────────────────────────────────────────
from server import get_kokoro, start_server
print("🔄 Initializing AI engine...")
try:
    get_kokoro()
except Exception as e:
    print(f"❌ Critical error loading AI engine: {e}")
    # Continue anyway, the UI will show the error
# ──────────────────────────────────────────────────────

def main():
    print("=" * 55)
    print("  🎧 AI Reader — Native AIMP-Style App")
    print("=" * 55)
    print()

    # ── Start TTS Server ──
    port = start_server()

    # ── NOW it's safe to import PyQt6 ──
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    app.setApplicationName("AI Reader")
    app.setApplicationDisplayName("AI Reader — Natural AI Voice")

    # ── Create Audio Player ──
    from audio_player import AudioPlayer
    audio = AudioPlayer(port)

    # ── Create Selection Monitor ──
    from selection_monitor import SelectionMonitor
    monitor = SelectionMonitor()

    # ── Create UI Components ──
    from ui.tray import SystemTray
    from ui.top_bar import TopBar
    from ui.reader_window import ReaderWindow

    # System Tray
    tray = SystemTray()

    # Top Bar (auto-hiding)
    top_bar = TopBar(audio)

    # Reader Window (hidden initially)
    reader = ReaderWindow(audio)

    # ── Load voices ──
    def load_voices():
        voices = audio.get_voices()
        if voices:
            top_bar.load_voices(voices)
            reader.load_voices(voices)
            print(f"🎙️  Loaded {len(voices)} voices")
        else:
            QTimer.singleShot(3000, load_voices)

    QTimer.singleShot(500, load_voices)

    # ── Wire up signals ──

    # Tray → Reader
    tray.open_reader.connect(lambda: (reader.show(), reader.raise_(), reader.activateWindow()))
    tray.quit_app.connect(lambda: _quit(app, monitor, audio))

    # Tray → Selection toggle
    tray.toggle_selection.connect(monitor.set_enabled)
    tray.toggle_selection.connect(top_bar._toggle.setChecked)

    # TopBar toggle → Monitor + Tray sync
    top_bar.toggle_selection.connect(monitor.set_enabled)
    top_bar.toggle_selection.connect(tray.set_selection_state)

    # Selection Monitor → Top Bar
    monitor.text_selected.connect(top_bar.set_captured_text)

    # Start monitor
    monitor.start()

    # Show tray icon
    tray.show()
    tray.show_notification(
        "AI Reader",
        "Running in system tray. Move mouse to top of screen for quick reader.\nRight-click tray icon for options.",
        5000,
    )

    print()
    print("✅ AI Reader is running!")
    print("   • System tray icon active")
    print("   • Selection reader: ON")
    print("   • Move mouse to top of screen for quick reader bar")
    print("   • Right-click tray icon → Open Reader for full UI")
    print()

    # ── Run ──
    sys.exit(app.exec())


def _quit(app, monitor, audio):
    """Clean shutdown."""
    print("\n👋 AI Reader shutting down...")
    monitor.stop()
    audio.cleanup()
    app.quit()


if __name__ == "__main__":
    main()
