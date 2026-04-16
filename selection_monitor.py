"""
AI Reader — Global Text Selection Monitor
Detects when the user selects text anywhere in Windows and captures it.
Uses mouse listener to detect mouse-up, then simulates Ctrl+C.
"""

import time
import threading

import pyperclip
import pyautogui
from pynput import mouse

from PyQt6.QtCore import QObject, pyqtSignal


class SelectionMonitor(QObject):
    """Monitors text selection across all Windows applications."""

    text_selected = pyqtSignal(str)  # Emitted when new text is selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = True
        self._listener = None
        self._running = False
        self._last_text = ""
        self._mouse_pressed = False
        self._press_time = 0
        self._ignore_next = False

        # Disable pyautogui failsafe (we handle our own safety)
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.02

    @property
    def enabled(self):
        return self._enabled

    def set_enabled(self, enabled):
        self._enabled = enabled
        if not enabled:
            self._mouse_pressed = False

    def start(self):
        """Start the mouse listener in a background thread."""
        if self._running:
            return

        self._running = True
        self._listener = mouse.Listener(
            on_click=self._on_click,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """Stop the mouse listener."""
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None

    def set_ignore_next(self):
        """Ignore the next mouse-up event (used when user clicks on our UI)."""
        self._ignore_next = True

    def _on_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        if not self._enabled or not self._running:
            return

        if button != mouse.Button.left:
            return

        if pressed:
            # Mouse button pressed — start tracking potential selection
            self._mouse_pressed = True
            self._press_time = time.time()
        else:
            # Mouse button released
            if not self._mouse_pressed:
                return
            self._mouse_pressed = False

            if self._ignore_next:
                self._ignore_next = False
                return

            # Only capture if mouse was held for a bit (indicates selection drag)
            hold_time = time.time() - self._press_time
            if hold_time < 0.15:
                # Quick click, not likely a selection
                return

            # Capture selection in background thread
            thread = threading.Thread(
                target=self._capture_selection,
                daemon=True,
            )
            thread.start()

    def _capture_selection(self):
        """Simulate Ctrl+C and read clipboard to capture selected text."""
        try:
            # Save current clipboard
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                old_clipboard = ""

            # Small delay for selection to finalize
            time.sleep(0.08)

            # Clear clipboard to detect new content
            try:
                pyperclip.copy("")
            except Exception:
                pass

            time.sleep(0.02)

            # Simulate Ctrl+C
            pyautogui.hotkey("ctrl", "c")

            # Wait for clipboard to update
            time.sleep(0.15)

            # Read new clipboard content
            try:
                new_text = pyperclip.paste()
            except Exception:
                new_text = ""

            # Check if we got new text
            if new_text and new_text.strip() and new_text != old_clipboard:
                self._last_text = new_text.strip()
                self.text_selected.emit(self._last_text)
            else:
                # Restore old clipboard if nothing new was captured
                try:
                    if old_clipboard:
                        pyperclip.copy(old_clipboard)
                except Exception:
                    pass

        except Exception as e:
            print(f"Selection capture error: {e}")
