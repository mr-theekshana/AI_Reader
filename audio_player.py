"""
AI Reader — Audio Player
Centralized TTS request + audio playback manager.
Uses QMediaPlayer for WAV playback with pause/resume support.
ONNX Runtime is pre-loaded before PyQt6 in main.py to avoid DLL conflicts.
"""

import os
import time
import tempfile
import threading
import requests

from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioPlayer(QObject):
    """Manages TTS generation requests and audio playback."""

    # Signals
    playback_started = pyqtSignal()
    playback_finished = pyqtSignal()
    playback_paused = pyqtSignal()
    playback_resumed = pyqtSignal()
    playback_error = pyqtSignal(str)
    generation_started = pyqtSignal()
    generation_finished = pyqtSignal(float)  # duration in seconds
    position_changed = pyqtSignal(int, int)  # current_ms, total_ms

    # Internal cross-thread signals
    _play_signal = pyqtSignal(str)
    _error_signal = pyqtSignal(str)
    _gen_done_signal = pyqtSignal(float)

    def __init__(self, server_port, parent=None):
        super().__init__(parent)
        self._port = server_port
        self._base_url = f"http://127.0.0.1:{server_port}"
        self._current_voice = "af_sarah"
        self._current_speed = 1.0
        self._volume = 1.0
        self._temp_files = []
        self._is_generating = False
        self._should_stop = False

        # Qt media player
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._audio_output.setVolume(self._volume)

        # Connect player signals
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_player_error)
        self._player.positionChanged.connect(self._on_position)

        # Connect cross-thread signals
        self._play_signal.connect(self._do_play)
        self._error_signal.connect(lambda msg: self.playback_error.emit(msg))
        self._gen_done_signal.connect(lambda d: self.generation_finished.emit(d))

    @property
    def is_playing(self):
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    @property
    def is_paused(self):
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PausedState

    @property
    def is_generating(self):
        return self._is_generating

    def set_voice(self, voice_id):
        self._current_voice = voice_id

    def set_speed(self, speed):
        self._current_speed = max(0.5, min(3.0, speed))

    def set_volume(self, volume):
        self._volume = max(0.0, min(1.0, volume))
        self._audio_output.setVolume(self._volume)

    def speak(self, text):
        """Generate TTS and play."""
        if not text or not text.strip():
            return
        self.stop()
        self._is_generating = True
        self._should_stop = False
        self.generation_started.emit()

        thread = threading.Thread(
            target=self._generate_audio,
            args=(text,),
            daemon=True,
        )
        thread.start()

    def _generate_audio(self, text):
        """Generate audio via TTS API (runs in bg thread)."""
        try:
            if self._should_stop:
                return

            response = requests.post(
                f"{self._base_url}/api/speak",
                json={
                    "text": text,
                    "voice": self._current_voice,
                    "speed": self._current_speed,
                },
                timeout=120,
            )

            if self._should_stop:
                return

            if response.status_code != 200:
                try:
                    error_msg = response.json().get("error", "Unknown error")
                except Exception:
                    error_msg = f"HTTP {response.status_code}"
                self._is_generating = False
                self._error_signal.emit(f"TTS Error: {error_msg}")
                return

            # Save to temp file
            temp_path = os.path.join(
                tempfile.gettempdir(),
                f"aireader_{int(time.time() * 1000)}.wav"
            )
            with open(temp_path, "wb") as f:
                f.write(response.content)
            self._temp_files.append(temp_path)

            duration = float(response.headers.get("X-Audio-Duration", 0))
            self._is_generating = False
            self._gen_done_signal.emit(duration)

            if self._should_stop:
                return

            # Signal main thread to play
            self._play_signal.emit(temp_path)

        except requests.exceptions.ConnectionError:
            self._is_generating = False
            self._error_signal.emit("Cannot connect to TTS server")
        except Exception as e:
            self._is_generating = False
            self._error_signal.emit(str(e))

    def _do_play(self, filepath):
        """Play WAV file (main thread)."""
        try:
            url = QUrl.fromLocalFile(filepath)
            self._player.setSource(url)
            self._player.play()
            self.playback_started.emit()
        except Exception as e:
            self.playback_error.emit(f"Playback error: {e}")

    def pause(self):
        """Pause playback."""
        if self.is_playing:
            self._player.pause()
            self.playback_paused.emit()

    def resume(self):
        """Resume playback."""
        if self.is_paused:
            self._player.play()
            self.playback_resumed.emit()

    def toggle_pause(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self.pause()
        elif self.is_paused:
            self.resume()

    def stop(self):
        """Stop playback and cancel generation."""
        self._should_stop = True
        self._player.stop()
        self._player.setSource(QUrl())
        self._is_generating = False

        # Signal TTS server to stop
        try:
            requests.post(f"{self._base_url}/api/stop", timeout=2)
        except Exception:
            pass

        self.playback_finished.emit()

    def get_voices(self):
        """Fetch available voices from the server."""
        try:
            r = requests.get(f"{self._base_url}/api/voices", timeout=5)
            return r.json().get("voices", [])
        except Exception:
            return []

    def translate(self, text, target_lang="en", source_lang="auto"):
        """Translate text via the server's Google Translate API."""
        try:
            r = requests.post(
                f"{self._base_url}/api/translate",
                json={"text": text, "source": source_lang, "target": target_lang},
                timeout=30,
            )
            if r.status_code == 200:
                return r.json().get("translated", text)
            else:
                print(f"⚠️ Translation failed: {r.json().get('error', 'Unknown')}")
                return None
        except Exception as e:
            print(f"⚠️ Translation error: {e}")
            return None

    def get_translation_languages(self):
        """Fetch supported translation languages."""
        try:
            r = requests.get(f"{self._base_url}/api/translate/languages", timeout=10)
            return r.json().get("languages", {})
        except Exception:
            return {}

    def _on_media_status(self, status):
        """Handle media status changes."""
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.playback_finished.emit()

    def _on_player_error(self, error):
        if error != QMediaPlayer.Error.NoError:
            self.playback_error.emit(f"Media error: {self._player.errorString()}")

    def _on_position(self, position):
        duration = self._player.duration()
        if duration > 0:
            self.position_changed.emit(position, duration)

    def _cleanup_temp(self):
        """Remove temporary audio files."""
        for path in self._temp_files:
            try:
                os.unlink(path)
            except Exception:
                pass
        self._temp_files.clear()

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        self._cleanup_temp()
