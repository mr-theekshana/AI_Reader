"""
AI Reader — System Tray Icon
Provides system tray integration with right-click menu.
"""

from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QLinearGradient, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication


def create_tray_icon_pixmap():
    """Create a programmatic tray icon (headphones emoji style)."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    grad = QLinearGradient(0, 0, size, size)
    grad.setColorAt(0, QColor("#7c3aed"))
    grad.setColorAt(1, QColor("#5b21b6"))
    p.setBrush(grad)
    p.setPen(QColor("#a78bfa"))
    p.drawRoundedRect(4, 4, size - 8, size - 8, 14, 14)

    # "AI" text
    p.setPen(QColor("white"))
    font = QFont("Segoe UI", 18, QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(pixmap.rect(), 0x0084, "AI")  # AlignCenter

    p.end()
    return pixmap


class SystemTray(QSystemTrayIcon):
    """System tray icon with context menu."""

    open_reader = pyqtSignal()
    toggle_selection = pyqtSignal(bool)
    quit_app = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create icon
        pixmap = create_tray_icon_pixmap()
        self.setIcon(QIcon(pixmap))
        self.setToolTip("AI Reader — Natural AI Voice")

        # Build menu
        self._menu = QMenu()
        self._menu.setStyleSheet("""
            QMenu {
                background: #14143a;
                color: #e8e8ff;
                border: 1px solid #2a2a5a;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #7c3aed;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #2a2a5a;
                margin: 4px 8px;
            }
        """)

        # Open Reader
        self._open_action = self._menu.addAction("📖  Open Reader")
        self._open_action.triggered.connect(self.open_reader.emit)

        self._menu.addSeparator()

        # Selection toggle
        self._selection_action = self._menu.addAction("✅  Selection Reader: ON")
        self._selection_action.triggered.connect(self._toggle_selection)
        self._selection_on = True

        self._menu.addSeparator()

        # Exit
        self._exit_action = self._menu.addAction("❌  Exit")
        self._exit_action.triggered.connect(self.quit_app.emit)

        self.setContextMenu(self._menu)

        # Double-click opens reader
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_reader.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_reader.emit()

    def _toggle_selection(self):
        self._selection_on = not self._selection_on
        if self._selection_on:
            self._selection_action.setText("✅  Selection Reader: ON")
        else:
            self._selection_action.setText("⬜  Selection Reader: OFF")
        self.toggle_selection.emit(self._selection_on)

    def set_selection_state(self, enabled):
        """Sync the menu state from external toggle."""
        self._selection_on = enabled
        if enabled:
            self._selection_action.setText("✅  Selection Reader: ON")
        else:
            self._selection_action.setText("⬜  Selection Reader: OFF")

    def show_notification(self, title, message, duration=3000):
        """Show a system notification."""
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, duration)
