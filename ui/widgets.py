"""
AI Reader — Custom Widgets
Reusable AIMP-inspired widgets: ToggleSwitch, GlowButton, WaveformWidget, TitleBar.
"""

import math
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtProperty, pyqtSignal, QSize, QRect, QPoint
)
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QFont, QPen, QBrush
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)


class ToggleSwitch(QWidget):
    """Animated on/off toggle switch with glow effect."""
    toggled = pyqtSignal(bool)

    def __init__(self, checked=True, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._circle_pos = 22.0 if checked else 3.0
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"circle_pos")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def get_circle_pos(self):
        return self._circle_pos

    def set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    circle_pos = pyqtProperty(float, get_circle_pos, set_circle_pos)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animate()
            self.toggled.emit(self._checked)

    def _animate(self):
        self._anim.stop()
        self._anim.setStartValue(self._circle_pos)
        self._anim.setEndValue(22.0 if self._checked else 3.0)
        self._anim.start()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self._animate()
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track
        if self._checked:
            # Gradient glow track
            grad = QLinearGradient(0, 0, self.width(), 0)
            grad.setColorAt(0, QColor("#5b21b6"))
            grad.setColorAt(1, QColor("#7c3aed"))
            p.setBrush(QBrush(grad))
        else:
            p.setBrush(QColor("#2a2a5a"))

        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 13, 13)

        # Circle
        circle_y = 3.0
        circle_r = 20.0
        if self._checked:
            # Glow effect
            glow = QColor("#a78bfa")
            glow.setAlpha(60)
            p.setBrush(glow)
            p.drawEllipse(int(self._circle_pos - 2), int(circle_y - 2),
                         int(circle_r + 4), int(circle_r + 4))
            p.setBrush(QColor("white"))
        else:
            p.setBrush(QColor("#6868aa"))

        p.drawEllipse(int(self._circle_pos), int(circle_y),
                     int(circle_r), int(circle_r))
        p.end()


class WaveformWidget(QWidget):
    """Animated waveform visualizer bars."""

    def __init__(self, bar_count=5, parent=None):
        super().__init__(parent)
        self.bar_count = bar_count
        self._bar_heights = [0.3] * bar_count
        self._target_heights = [0.3] * bar_count
        self._is_playing = False
        self._tick = 0

        self.setFixedSize(bar_count * 7 + 4, 30)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_bars)
        self._timer.setInterval(60)

    def set_playing(self, playing):
        self._is_playing = playing
        if playing:
            self._timer.start()
        else:
            self._timer.stop()
            self._bar_heights = [0.2] * self.bar_count
            self.update()

    def _animate_bars(self):
        import random
        self._tick += 1
        for i in range(self.bar_count):
            if self._tick % 3 == 0:
                self._target_heights[i] = random.uniform(0.2, 1.0)
            # Smooth toward target
            diff = self._target_heights[i] - self._bar_heights[i]
            self._bar_heights[i] += diff * 0.3
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar_w = 4
        gap = 3
        total_w = self.bar_count * (bar_w + gap) - gap
        x_off = (self.width() - total_w) // 2

        for i, h in enumerate(self._bar_heights):
            x = x_off + i * (bar_w + gap)
            bar_h = max(3, int(h * (self.height() - 4)))
            y = self.height() - bar_h - 2

            grad = QLinearGradient(x, y, x, self.height())
            if self._is_playing:
                grad.setColorAt(0, QColor("#a78bfa"))
                grad.setColorAt(1, QColor("#7c3aed"))
            else:
                grad.setColorAt(0, QColor("#4a4a7a"))
                grad.setColorAt(1, QColor("#2a2a5a"))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(x, y, bar_w, bar_h, 2, 2)

        p.end()


class GlowButton(QPushButton):
    """Button with subtle glow animation on hover."""

    def __init__(self, text="", icon_text="", parent=None):
        super().__init__(text, parent)
        self._glow_opacity = 0
        self._icon_text = icon_text

        self._anim = QPropertyAnimation(self, b"glow_opacity")
        self._anim.setDuration(200)

    def get_glow_opacity(self):
        return self._glow_opacity

    def set_glow_opacity(self, val):
        self._glow_opacity = val
        self.update()

    glow_opacity = pyqtProperty(int, get_glow_opacity, set_glow_opacity)

    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow_opacity)
        self._anim.setEndValue(40)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow_opacity)
        self._anim.setEndValue(0)
        self._anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._glow_opacity > 0:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            glow = QColor("#7c3aed")
            glow.setAlpha(self._glow_opacity)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(glow)
            p.drawRoundedRect(self.rect(), 8, 8)
            p.end()


class TitleBar(QWidget):
    """Custom frameless window title bar with drag support."""
    close_clicked = pyqtSignal()
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()

    def __init__(self, title="AI Reader", parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(38)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 4, 0)
        layout.setSpacing(0)

        # Icon/Logo
        logo = QLabel("🎧")
        logo.setStyleSheet("font-size: 16px; background: transparent;")
        layout.addWidget(logo)

        # Title
        title_label = QLabel(f"  {title}")
        title_label.setObjectName("TitleLabel")
        layout.addWidget(title_label)

        layout.addStretch()

        # Minimize button
        min_btn = QPushButton("─")
        min_btn.setObjectName("MinBtn")
        min_btn.setToolTip("Minimize")
        min_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(min_btn)

        # Maximize button
        self._max_btn = QPushButton("□")
        self._max_btn.setObjectName("MinBtn")  # Same style as minimize
        self._max_btn.setToolTip("Maximize")
        self._max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self._max_btn)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(close_btn)

    def _toggle_maximize(self):
        w = self.window()
        if w.isMaximized():
            w.showNormal()
            self._max_btn.setText("□")
            self._max_btn.setToolTip("Maximize")
        else:
            w.showMaximized()
            self._max_btn.setText("❐")
            self._max_btn.setToolTip("Restore")
        self.maximize_clicked.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            w = self.window()
            if w.isMaximized():
                w.showNormal()
                self._max_btn.setText("□")
                # Adjust drag position
                self._drag_pos = QPoint(w.width() // 2, 19)
            w.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        self._toggle_maximize()


class PauseButton(QPushButton):
    """Custom-painted pause button with two vertical bars."""

    def __init__(self, parent=None):
        super().__init__("", parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Circle background
        if self.underMouse():
            p.setBrush(QColor("#8b5cf6"))  # accent_glow
        else:
            p.setBrush(QColor("#7c3aed"))  # accent
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(0, 0, 36, 36)

        # Two pause bars
        p.setBrush(QColor("white"))
        bar_w = 4
        bar_h = 14
        cx = 18
        cy = 18
        gap = 3
        p.drawRoundedRect(cx - gap - bar_w, cy - bar_h // 2, bar_w, bar_h, 1, 1)
        p.drawRoundedRect(cx + gap, cy - bar_h // 2, bar_w, bar_h, 1, 1)
        p.end()
