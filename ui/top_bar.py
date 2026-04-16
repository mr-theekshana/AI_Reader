"""
AI Reader — Auto-Hiding Top Bar
Shows a small trigger button when mouse hits top edge.
Click to expand full bar. Auto-expands on text selection.
"""

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtSignal
)
from PyQt6.QtGui import (
    QCursor, QGuiApplication, QPainter, QColor, QLinearGradient, QBrush, QPen,
    QPainterPath, QRegion
)
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSlider, QProgressBar
)
import threading
import json
import os

from ui.styles import get_topbar_stylesheet, COLORS
from ui.widgets import ToggleSwitch, WaveformWidget, PauseButton


class TriggerButton(QWidget):
    """Small floating button shown at top of screen as a pull-down handle."""
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(60, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Position at top-center of screen
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        self.move(geo.width() // 2 - 30, geo.top())

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Rounded tab shape
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor("#5b21b6"))
        grad.setColorAt(0.5, QColor("#7c3aed"))
        grad.setColorAt(1, QColor("#5b21b6"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#a78bfa"), 1))
        p.drawRoundedRect(0, -4, self.width(), self.height() + 4, 10, 10)

        # Down arrow
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("white"))
        cx = self.width() // 2
        cy = self.height() // 2 + 1
        p.drawPolygon([
            QPoint(cx - 6, cy - 3),
            QPoint(cx + 6, cy - 3),
            QPoint(cx, cy + 4),
        ])
        p.end()

    def mousePressEvent(self, event):
        self.clicked.emit()


class TopBar(QWidget):
    """Auto-hiding top bar for text selection reading."""

    BAR_HEIGHT = 45
    TRIGGER_ZONE = 6
    HIDE_DELAY_MS = 2000

    play_requested = pyqtSignal(str)
    stop_requested = pyqtSignal()
    toggle_selection = pyqtSignal(bool)

    def __init__(self, audio_player, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool
                         | Qt.WindowType.NoDropShadowWindowHint)
        self.setObjectName("TopBar")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        self._audio = audio_player
        self._captured_text = ""
        self._is_visible = False
        self._mouse_inside = False
        self._settings_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "settings.json"
        )
        self._bar_y = -self.BAR_HEIGHT

        # Get screen geometry
        screen = QGuiApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        self._screen_width = screen_geo.width()
        self._screen_top = screen_geo.top()

        # Dynamic Island: 70% width, centered
        self._bar_width = int(self._screen_width * 0.7)
        self._start_x = (self._screen_width - self._bar_width) // 2

        self.setFixedHeight(self.BAR_HEIGHT)
        self.setFixedWidth(self._bar_width)
        self.move(self._start_x, -self.BAR_HEIGHT)

        self.setStyleSheet(get_topbar_stylesheet())
        self._build_ui()

        # ── Trigger button (small tab at top) ──
        self._trigger = TriggerButton()
        self._trigger.clicked.connect(self._on_trigger_clicked)
        self._trigger.hide()

        # Timer to check mouse position for trigger button
        self._mouse_timer = QTimer(self)
        self._mouse_timer.timeout.connect(self._check_mouse)
        self._mouse_timer.start(100)

        # Timer for auto-hide delay
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._slide_up)

        # Animation for sliding
        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setDuration(300)
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Connect audio signals
        self._audio.playback_started.connect(self._on_play_started)
        self._audio.playback_finished.connect(self._on_play_finished)
        self._audio.playback_paused.connect(self._on_play_paused)
        self._audio.playback_resumed.connect(self._on_play_resumed)
        self._audio.generation_started.connect(self._on_generating)
        self._audio.generation_finished.connect(self._on_gen_finished)
        self._audio.playback_error.connect(self._on_error)

        self.show()

    def resizeEvent(self, event):
        """Clip the window to a rounded shape — this IS the curve."""
        super().resizeEvent(event)
        path = QPainterPath()
        # Use moderate rounding (not full pill, just nicely curved corners)
        path.addRoundedRect(0, 0, self.width(), self.height(), 17, 17)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def paintEvent(self, event):
        """Fill the masked area with gradient — mask handles the curve."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background gradient
        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(14, 14, 40, 255))
        grad.setColorAt(0.5, QColor(20, 20, 58, 255))
        grad.setColorAt(1, QColor(14, 14, 40, 255))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)

        # Fill entire area — the mask clips it to the rounded shape
        p.drawRect(0, 0, self.width(), self.height())
        p.end()

    def _build_ui(self):
        """Build the top bar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 4, 24, 4)
        layout.setSpacing(10)

        # ── Toggle switch ──
        self._toggle = ToggleSwitch(checked=True)
        self._toggle.toggled.connect(self._on_toggle)
        layout.addWidget(self._toggle)

        # ── AI label ──
        ai_label = QLabel("AI")
        ai_label.setStyleSheet(f"""
            color: {COLORS['accent_light']};
            font-size: 14px;
            font-weight: bold;
            background: transparent;
        """)
        layout.addWidget(ai_label)

        # ── Divider ──
        div1 = QLabel("│")
        div1.setStyleSheet(f"color: {COLORS['border']}; background: transparent;")
        layout.addWidget(div1)

        # ── Text preview ──
        self._text_preview = QLabel("Select text anywhere to read aloud...")
        self._text_preview.setObjectName("TextPreview")
        self._text_preview.setMinimumWidth(200)
        self._text_preview.setMaximumWidth(500)
        layout.addWidget(self._text_preview, 1)

        # ── Loading progress bar (shown during generation) ──
        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(60)
        self._progress_bar.setFixedHeight(8)
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
        self._progress_bar.hide()
        layout.addWidget(self._progress_bar)

        # ── Waveform (shown only during actual playback) ──
        self._waveform = WaveformWidget(bar_count=5)
        self._waveform.hide()
        layout.addWidget(self._waveform)

        # ── Play button ──
        self._play_btn = QPushButton("▶")
        self._play_btn.setObjectName("PlayBtn")
        self._play_btn.setToolTip("Play selected text")
        self._play_btn.clicked.connect(self._on_play_click)
        layout.addWidget(self._play_btn)

        # ── Pause button (custom painted) ──
        self._pause_btn = PauseButton()
        self._pause_btn.setToolTip("Pause")
        self._pause_btn.clicked.connect(self._on_pause_click)
        self._pause_btn.hide()
        layout.addWidget(self._pause_btn)

        # ── Stop button ──
        self._stop_btn = QPushButton("■")
        self._stop_btn.setObjectName("StopBtn")
        self._stop_btn.setToolTip("Stop")
        self._stop_btn.clicked.connect(self._on_stop_click)
        self._stop_btn.hide()
        layout.addWidget(self._stop_btn)

        # ── Divider ──
        div2 = QLabel("│")
        div2.setStyleSheet(f"color: {COLORS['border']}; background: transparent;")
        layout.addWidget(div2)

        # ── Voice selector ──
        self._voice_combo = QComboBox()
        self._voice_combo.setObjectName("VoiceCombo")
        self._voice_combo.setToolTip("Voice")
        self._voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        layout.addWidget(self._voice_combo)

        # ── Speed ──
        speed_label = QLabel("⚡")
        speed_label.setStyleSheet("background: transparent; font-size: 14px;")
        speed_label.setToolTip("Speed")
        layout.addWidget(speed_label)

        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setObjectName("SpeedSlider")
        self._speed_slider.setRange(50, 200)
        self._speed_slider.setValue(100)
        self._speed_slider.setFixedWidth(80)
        self._speed_slider.setToolTip("Speed: 1.0x")
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        layout.addWidget(self._speed_slider)

        self._speed_label = QLabel("1.0x")
        self._speed_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 11px;
            background: transparent;
            min-width: 28px;
        """)
        layout.addWidget(self._speed_label)

        # ── Status ──
        self._status = QLabel("")
        self._status.setObjectName("StatusLabel")
        self._status.setMinimumWidth(50)
        layout.addWidget(self._status)

    def load_voices(self, voices):
        """Populate voice selector."""
        self._voice_combo.blockSignals(True)
        self._voice_combo.clear()
        for v in voices:
            self._voice_combo.addItem(v["name"], v["id"])
        # Restore saved voice
        saved_voice = self._load_setting("voice")
        if saved_voice:
            idx = self._voice_combo.findData(saved_voice)
            if idx >= 0:
                self._voice_combo.setCurrentIndex(idx)
                self._audio.set_voice(saved_voice)
        self._voice_combo.blockSignals(False)
        # Restore saved speed
        saved_speed = self._load_setting("speed")
        if saved_speed is not None:
            self._speed_slider.setValue(int(saved_speed))
            speed = int(saved_speed) / 100.0
            self._audio.set_speed(speed)
            self._speed_label.setText(f"{speed:.1f}x")

    def set_captured_text(self, text):
        """Set the captured text and show the full bar (auto on selection)."""
        self._captured_text = text
        preview = text[:80].replace("\n", " ")
        if len(text) > 80:
            preview += "..."
        self._text_preview.setText(f'"{ preview}"')
        self._text_preview.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 13px;
            background: transparent;
            padding: 0 8px;
        """)
        # Auto-show full bar on text selection
        self._trigger.hide()
        self._slide_down()

    # ── Trigger button behavior ──────────────────────────

    def _on_trigger_clicked(self):
        """User clicked the small trigger tab → expand full bar."""
        self._trigger.hide()
        self._slide_down()

    def _check_mouse(self):
        """Check mouse position for trigger/bar visibility."""
        cursor_pos = QCursor.pos()
        bar_rect = self.geometry()

        # If bar is visible, check if mouse is inside it
        if self._is_visible:
            if bar_rect.contains(cursor_pos):
                self._mouse_inside = True
                self._hide_timer.stop()
                return

            # Mouse left the bar
            if self._mouse_inside:
                self._mouse_inside = False
                # Don't hide during playback/generation
                if not self._audio.is_playing and not self._audio.is_generating:
                    self._hide_timer.start(self.HIDE_DELAY_MS)
            return

        # Bar is hidden — check if mouse is at top edge
        if cursor_pos.y() <= self._screen_top + self.TRIGGER_ZONE:
            # Show the small trigger button (not the full bar)
            if not self._trigger.isVisible() and not self._is_visible:
                self._trigger.show()
                self._trigger.raise_()
        else:
            # Mouse moved away from top
            trigger_rect = self._trigger.geometry()
            if not trigger_rect.contains(cursor_pos):
                self._trigger.hide()

    # ── Slide animation ──────────────────────────────────

    def _slide_down(self):
        """Slide the full bar down into view."""
        if self._is_visible:
            return
        self._is_visible = True
        self._hide_timer.stop()
        self._slide_anim.stop()
        self._slide_anim.setStartValue(self.pos())
        self._slide_anim.setEndValue(QPoint(self._start_x, self._screen_top + 8))
        self._slide_anim.start()

    def _slide_up(self):
        """Slide the bar up to hide."""
        if not self._is_visible:
            return
        if self._mouse_inside:
            return
        if self._audio.is_playing or self._audio.is_generating or self._audio.is_paused:
            return  # Don't hide during activity

        self._is_visible = False
        self._slide_anim.stop()
        self._slide_anim.setStartValue(self.pos())
        self._slide_anim.setEndValue(QPoint(self._start_x, -self.BAR_HEIGHT))
        self._slide_anim.start()

    # ── Callbacks ────────────────────────────────────────

    def _on_toggle(self, checked):
        self.toggle_selection.emit(checked)
        if checked:
            self._status.setText("Monitoring")
        else:
            self._status.setText("OFF")
        QTimer.singleShot(2000, lambda: self._status.setText(""))

    def _on_play_click(self):
        # If paused, resume instead of regenerating
        if self._audio.is_paused:
            self._audio.resume()
            return
        if self._captured_text:
            self._audio.speak(self._captured_text)

    def _load_setting(self, key, default=None):
        """Load a setting from the settings file."""
        try:
            if os.path.exists(self._settings_path):
                with open(self._settings_path, "r") as f:
                    settings = json.load(f)
                return settings.get(key, default)
        except Exception:
            pass
        return default

    def _save_setting(self, key, value):
        """Save a setting to the settings file."""
        try:
            settings = {}
            if os.path.exists(self._settings_path):
                with open(self._settings_path, "r") as f:
                    settings = json.load(f)
            settings[key] = value
            with open(self._settings_path, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save setting: {e}")

    def _on_pause_click(self):
        self._audio.pause()

    def _on_stop_click(self):
        self._audio.stop()

    def _on_voice_changed(self, index):
        voice_id = self._voice_combo.currentData()
        if voice_id:
            self._audio.set_voice(voice_id)
            self._save_setting("voice", voice_id)

    def _on_speed_changed(self, value):
        speed = value / 100.0
        self._audio.set_speed(speed)
        self._speed_label.setText(f"{speed:.1f}x")
        self._speed_slider.setToolTip(f"Speed: {speed:.1f}x")
        self._save_setting("speed", value)

    # ── Audio state handlers ─────────────────────────────

    def _on_generating(self):
        """TTS is generating audio — show progress bar."""
        self._status.setText("Generating...")
        self._progress_bar.show()
        self._waveform.hide()
        self._waveform.set_playing(False)
        self._play_btn.hide()
        self._pause_btn.hide()
        self._stop_btn.show()
        self._hide_timer.stop()
        self._slide_down()

    def _on_gen_finished(self, duration):
        """Generation complete, about to play."""
        self._progress_bar.hide()
        self._status.setText(f"Playing {duration:.1f}s...")

    def _on_play_started(self):
        """Audio playback started — show waveform."""
        self._progress_bar.hide()
        self._waveform.show()
        self._waveform.set_playing(True)
        self._play_btn.hide()
        self._pause_btn.show()
        self._stop_btn.show()
        self._status.setText("Playing...")
        self._hide_timer.stop()

    def _on_play_paused(self):
        """Playback paused."""
        self._waveform.set_playing(False)
        self._pause_btn.hide()
        self._play_btn.show()
        self._play_btn.setToolTip("Resume")
        self._status.setText("Paused")

    def _on_play_resumed(self):
        """Playback resumed."""
        self._waveform.set_playing(True)
        self._play_btn.hide()
        self._pause_btn.show()
        self._status.setText("Playing...")

    def _on_play_finished(self):
        """Playback finished — reset everything."""
        self._waveform.set_playing(False)
        self._waveform.hide()
        self._progress_bar.hide()
        self._play_btn.show()
        self._play_btn.setToolTip("Play selected text")
        self._pause_btn.hide()
        self._stop_btn.hide()
        self._status.setText("")
        # Start hide timer after playback ends
        if not self._mouse_inside:
            self._hide_timer.start(self.HIDE_DELAY_MS)

    def _on_error(self, msg):
        """Error occurred."""
        self._waveform.set_playing(False)
        self._waveform.hide()
        self._progress_bar.hide()
        self._play_btn.show()
        self._pause_btn.hide()
        self._stop_btn.hide()
        self._status.setText("Error!")
        QTimer.singleShot(3000, lambda: self._status.setText(""))
