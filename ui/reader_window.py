"""
AI Reader — AIMP-Style Reader Window
Compact, dark, glassmorphism window for reading PDF and TXT files.
"""

import os
import json
import threading
import webbrowser

from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QFont, QColor, QPixmap, QImage, QIcon, QPainter, QLinearGradient
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QTextEdit, QTabWidget, QFileDialog,
    QScrollArea, QSizePolicy, QFrame, QProgressBar, QSpacerItem,
    QApplication
)

from ui.styles import get_main_stylesheet, get_titlebar_stylesheet, COLORS
from ui.widgets import TitleBar, WaveformWidget, GlowButton, ToggleSwitch, PauseButton


class ReaderWindow(QWidget):
    """AIMP-style compact reader window for PDF and TXT files."""

    # Cross-thread signals for translation
    _translate_done = pyqtSignal(str)
    _translate_failed = pyqtSignal()

    def __init__(self, audio_player, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("AI Reader")
        self.setMinimumSize(680, 520)
        self.resize(780, 620)

        self._audio = audio_player
        self._current_file = None
        self._pdf_doc = None
        self._pdf_page = 0
        self._pdf_total_pages = 0
        self._settings_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "settings.json"
        )

        self.setStyleSheet(get_main_stylesheet() + get_titlebar_stylesheet())
        self._build_ui()
        self._connect_signals()

        # Connect translation signals
        self._translate_done.connect(self._show_translate_result)
        self._translate_failed.connect(self._show_translate_error)

    def _build_ui(self):
        """Build the reader window UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Custom Title Bar ──
        self._titlebar = TitleBar("AI Reader", self)
        self._titlebar.close_clicked.connect(self.hide)
        self._titlebar.minimize_clicked.connect(self.showMinimized)
        main_layout.addWidget(self._titlebar)

        # ── Content area ──
        content = QWidget()
        content.setStyleSheet(f"background: {COLORS['bg_main']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 16)
        content_layout.setSpacing(12)

        # ── Tab Widget ──
        self._tabs = QTabWidget()
        content_layout.addWidget(self._tabs, 1)

        # Text Tab
        text_tab = QWidget()
        self._build_text_tab(text_tab)
        self._tabs.addTab(text_tab, "📝  Text")

        # PDF Tab
        pdf_tab = QWidget()
        self._build_pdf_tab(pdf_tab)
        self._tabs.addTab(pdf_tab, "📄  PDF")

        # Translate Tab
        translate_tab = QWidget()
        self._build_translate_tab(translate_tab)
        self._tabs.addTab(translate_tab, "🌐  Translate")

        # About Tab
        about_tab = QWidget()
        self._build_about_tab(about_tab)
        self._tabs.addTab(about_tab, "ℹ️  About")

        # ── Playback Controls (shared) ──
        controls_card = self._build_controls()
        content_layout.addWidget(controls_card)

        main_layout.addWidget(content, 1)

    def _build_text_tab(self, parent):
        """Build the text tab content."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        import_btn = GlowButton("📂 Import .txt")
        import_btn.setFixedHeight(34)
        import_btn.clicked.connect(self._import_txt)
        toolbar.addWidget(import_btn)

        paste_btn = GlowButton("📋 Paste")
        paste_btn.setFixedHeight(34)
        paste_btn.clicked.connect(self._paste_text)
        toolbar.addWidget(paste_btn)

        clear_btn = GlowButton("🗑️ Clear")
        clear_btn.setFixedHeight(34)
        clear_btn.clicked.connect(self._clear_text)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()

        # Character count
        self._char_count = QLabel("0 chars")
        self._char_count.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            font-size: 11px;
            background: transparent;
        """)
        toolbar.addWidget(self._char_count)

        layout.addLayout(toolbar)

        # Text area
        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText(
            "Type, paste, or import text here...\n\n"
            "You can also select text anywhere on your screen and use the top bar to read it."
        )
        self._text_edit.setFont(QFont("Segoe UI", 13))
        self._text_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._text_edit, 1)

    def _build_pdf_tab(self, parent):
        """Build the PDF tab content."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        open_pdf_btn = GlowButton("📂 Open PDF")
        open_pdf_btn.setFixedHeight(34)
        open_pdf_btn.clicked.connect(self._open_pdf)
        toolbar.addWidget(open_pdf_btn)

        extract_btn = GlowButton("📄 Extract Page Text")
        extract_btn.setFixedHeight(34)
        extract_btn.clicked.connect(self._extract_page_text)
        toolbar.addWidget(extract_btn)

        toolbar.addStretch()

        # Page navigation
        nav_btn_style = f"""
            QPushButton {{
                background: {COLORS['bg_card']};
                color: {COLORS['accent_light']};
                border: 1px solid {COLORS['border_light']};
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['accent']};
                color: white;
                border-color: {COLORS['accent_light']};
            }}
            QPushButton:disabled {{
                background: {COLORS['bg_dark']};
                color: {COLORS['text_dim']};
                border-color: {COLORS['border']};
            }}
        """

        self._prev_page_btn = QPushButton("  ◀  ")
        self._prev_page_btn.setFixedSize(38, 32)
        self._prev_page_btn.setStyleSheet(nav_btn_style)
        self._prev_page_btn.clicked.connect(self._prev_pdf_page)
        self._prev_page_btn.setEnabled(False)
        toolbar.addWidget(self._prev_page_btn)

        self._page_label = QLabel("No PDF loaded")
        self._page_label.setStyleSheet(f"""
            color: {COLORS['accent_light']};
            font-size: 13px;
            font-weight: bold;
            background: transparent;
            padding: 0 10px;
        """)
        toolbar.addWidget(self._page_label)

        self._next_page_btn = QPushButton("  ▶  ")
        self._next_page_btn.setFixedSize(38, 32)
        self._next_page_btn.setStyleSheet(nav_btn_style)
        self._next_page_btn.clicked.connect(self._next_pdf_page)
        self._next_page_btn.setEnabled(False)
        toolbar.addWidget(self._next_page_btn)

        layout.addLayout(toolbar)

        # PDF viewer area (scrollable image)
        self._pdf_scroll = QScrollArea()
        self._pdf_scroll.setWidgetResizable(True)
        self._pdf_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        self._pdf_label = QLabel("Open a PDF file to view it here")
        self._pdf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pdf_label.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            font-size: 14px;
            background: transparent;
            padding: 40px;
        """)
        self._pdf_scroll.setWidget(self._pdf_label)

        layout.addWidget(self._pdf_scroll, 1)

    def _build_translate_tab(self, parent):
        """Build the Translate tab — paste text, pick language, see translation."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        paste_btn = GlowButton("📋 Paste Text")
        paste_btn.setFixedHeight(34)
        paste_btn.clicked.connect(self._translate_paste)
        toolbar.addWidget(paste_btn)

        clear_btn = GlowButton("🗑️ Clear")
        clear_btn.setFixedHeight(34)
        clear_btn.clicked.connect(self._translate_clear)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()

        # Language selector
        lang_label = QLabel("🌐 Translate to:")
        lang_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 12px;")
        toolbar.addWidget(lang_label)

        self._translate_lang_combo = QComboBox()
        self._translate_lang_combo.setFixedWidth(120)
        self._translate_lang_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 18px;
            }}
            QComboBox QAbstractItemView {{
                background: {COLORS['bg_main']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                selection-background-color: {COLORS['accent']};
            }}
        """)
        common_langs = [
            ("Sinhala", "si"), ("Hindi", "hi"), ("Tamil", "ta"),
            ("Spanish", "es"), ("French", "fr"), ("German", "de"),
            ("Chinese", "zh-CN"), ("Japanese", "ja"), ("Korean", "ko"),
            ("Arabic", "ar"), ("Russian", "ru"), ("Portuguese", "pt"),
            ("Italian", "it"), ("Dutch", "nl"), ("Turkish", "tr"),
            ("Thai", "th"), ("Vietnamese", "vi"), ("Indonesian", "id"),
            ("Malay", "ms"), ("Bengali", "bn"), ("English", "en"),
        ]
        for name, code in common_langs:
            self._translate_lang_combo.addItem(name, code)
        # Restore saved language
        saved_lang = self._load_setting("target_lang", "si")
        idx = self._translate_lang_combo.findData(saved_lang)
        if idx >= 0:
            self._translate_lang_combo.setCurrentIndex(idx)
        self._translate_lang_combo.currentIndexChanged.connect(self._on_translate_lang_changed)
        toolbar.addWidget(self._translate_lang_combo)

        # Translate button
        self._translate_btn = GlowButton("⚡ Translate")
        self._translate_btn.setFixedHeight(34)
        self._translate_btn.setProperty("class", "accent")
        self._translate_btn.clicked.connect(self._do_translate)
        toolbar.addWidget(self._translate_btn)

        layout.addLayout(toolbar)

        # Input text area
        input_label = QLabel("Source Text:")
        input_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 12px; font-weight: bold;")
        layout.addWidget(input_label)

        self._translate_input = QTextEdit()
        self._translate_input.setPlaceholderText("Paste or type text here to translate...")
        self._translate_input.setFont(QFont("Segoe UI", 13))
        self._translate_input.setMaximumHeight(100)
        layout.addWidget(self._translate_input)

        # Status
        self._translate_status = QLabel("")
        self._translate_status.setStyleSheet(f"color: {COLORS['accent_light']}; background: transparent; font-size: 11px;")
        layout.addWidget(self._translate_status)

        # Output text area
        output_label = QLabel("Translation:")
        output_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 12px; font-weight: bold;")
        layout.addWidget(output_label)

        self._translate_output = QTextEdit()
        self._translate_output.setReadOnly(True)
        self._translate_output.setPlaceholderText("Translated text will appear here...")
        self._translate_output.setFont(QFont("Segoe UI", 13))
        self._translate_output.setStyleSheet(f"""
            QTextEdit {{
                background: {COLORS['bg_card']};
                color: {COLORS['accent_light']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        layout.addWidget(self._translate_output, 1)

    def _build_about_tab(self, parent):
        """Build the About tab with creator info and social links."""
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        content = QVBoxLayout(container)
        content.setContentsMargins(20, 30, 20, 30)
        content.setSpacing(16)
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # App icon / logo
        logo_label = QLabel("🎧")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet(f"""
            font-size: 52px;
            background: transparent;
            padding: 8px;
        """)
        content.addWidget(logo_label)

        # App name
        app_name = QLabel("AI Reader")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 28px;
            font-weight: bold;
            background: transparent;
            letter-spacing: 1px;
        """)
        content.addWidget(app_name)

        # Version
        version_label = QLabel("Version 3.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet(f"""
            color: {COLORS['accent_light']};
            font-size: 13px;
            background: transparent;
        """)
        content.addWidget(version_label)

        # Separator
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background: {COLORS['border']}; margin: 8px 60px;")
        content.addWidget(sep1)

        # Description
        desc = QLabel(
            "AI Reader is a powerful offline text-to-speech application powered by "
            "Kokoro AI voices. Select any text on your screen and hear it read aloud "
            "with natural, human-like voices. Supports TXT and PDF files, multiple "
            "voices, adjustable speed, and real-time text translation."
        )
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 13px;
            background: transparent;
            padding: 4px 20px;
            line-height: 1.6;
        """)
        content.addWidget(desc)

        # Separator
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {COLORS['border']}; margin: 8px 60px;")
        content.addWidget(sep2)

        # Creator
        created_label = QLabel("Created by")
        created_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        created_label.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            font-size: 11px;
            background: transparent;
        """)
        content.addWidget(created_label)

        creator_name = QLabel("Mr_Theekshana")
        creator_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        creator_name.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 20px;
            font-weight: bold;
            background: transparent;
            padding: 4px;
        """)
        content.addWidget(creator_name)

        # Social links container
        links_layout = QHBoxLayout()
        links_layout.setSpacing(16)
        links_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # GitHub button
        github_btn = QPushButton("  GitHub")
        github_btn.setFixedSize(140, 40)
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.setStyleSheet(f"""
            QPushButton {{
                background: #24292e;
                color: white;
                border: 1px solid #444;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
                padding-left: 8px;
            }}
            QPushButton:hover {{
                background: #2ea44f;
                border-color: #2ea44f;
            }}
        """)
        github_btn.clicked.connect(
            lambda: webbrowser.open("https://github.com/mr-theekshana")
        )
        links_layout.addWidget(github_btn)

        # Facebook button
        fb_btn = QPushButton("  Facebook")
        fb_btn.setFixedSize(140, 40)
        fb_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fb_btn.setStyleSheet(f"""
            QPushButton {{
                background: #1877f2;
                color: white;
                border: 1px solid #1877f2;
                border-radius: 20px;
                font-size: 13px;
                font-weight: bold;
                padding-left: 8px;
            }}
            QPushButton:hover {{
                background: #166fe5;
                border-color: #0d65d9;
            }}
        """)
        fb_btn.clicked.connect(
            lambda: webbrowser.open("https://www.facebook.com/Mr.Theekshana.Official")
        )
        links_layout.addWidget(fb_btn)

        content.addLayout(links_layout)

        # Footer
        footer = QLabel("Made with ❤️ in Sri Lanka")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"""
            color: {COLORS['text_dim']};
            font-size: 11px;
            background: transparent;
            padding-top: 16px;
        """)
        content.addWidget(footer)

        content.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _build_controls(self):
        """Build the shared playback controls panel."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Top row: playback controls
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Play
        self._play_btn = QPushButton("▶  Play")
        self._play_btn.setProperty("class", "accent")
        self._play_btn.setFixedHeight(38)
        self._play_btn.setMinimumWidth(100)
        self._play_btn.clicked.connect(self._on_play)
        top_row.addWidget(self._play_btn)

        # Pause
        self._pause_btn = QPushButton("❚❚  Pause")
        self._pause_btn.setFixedHeight(38)
        self._pause_btn.setMinimumWidth(100)
        self._pause_btn.clicked.connect(self._on_pause)
        self._pause_btn.setVisible(False)
        top_row.addWidget(self._pause_btn)

        # Stop
        self._stop_btn = QPushButton("■  Stop")
        self._stop_btn.setFixedHeight(38)
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        top_row.addWidget(self._stop_btn)

        # Loading progress bar (shown during generation)
        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(80)
        self._progress_bar.setFixedHeight(10)
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border']};
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['accent']};
                border-radius: 4px;
            }}
        """)
        self._progress_bar.hide()
        top_row.addWidget(self._progress_bar)

        # Waveform (shown only during actual playback)
        self._waveform = WaveformWidget(bar_count=7)
        self._waveform.hide()
        top_row.addWidget(self._waveform)

        top_row.addStretch()

        # Status
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            background: transparent;
        """)
        top_row.addWidget(self._status_label)

        layout.addLayout(top_row)

        # Bottom row: voice, speed, volume
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        # Voice
        voice_label = QLabel("🎙️ Voice:")
        voice_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 12px;")
        bottom_row.addWidget(voice_label)

        self._voice_combo = QComboBox()
        self._voice_combo.setMinimumWidth(120)
        self._voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        bottom_row.addWidget(self._voice_combo)

        bottom_row.addSpacing(12)

        # Speed
        speed_icon = QLabel("⚡ Speed:")
        speed_icon.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 12px;")
        bottom_row.addWidget(speed_icon)

        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(50, 200)
        self._speed_slider.setValue(100)
        self._speed_slider.setFixedWidth(120)
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        bottom_row.addWidget(self._speed_slider)

        self._speed_label = QLabel("1.0x")
        self._speed_label.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent; font-size: 12px; min-width: 30px;")
        bottom_row.addWidget(self._speed_label)

        bottom_row.addSpacing(12)

        # Volume
        vol_icon = QLabel("🔊 Volume:")
        vol_icon.setStyleSheet(f"color: {COLORS['text_secondary']}; background: transparent; font-size: 12px;")
        bottom_row.addWidget(vol_icon)

        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setValue(100)
        self._vol_slider.setFixedWidth(100)
        self._vol_slider.valueChanged.connect(self._on_volume_changed)
        bottom_row.addWidget(self._vol_slider)

        bottom_row.addStretch()

        layout.addLayout(bottom_row)

        return card

    def _connect_signals(self):
        """Connect audio player signals."""
        self._audio.playback_started.connect(self._on_play_started)
        self._audio.playback_finished.connect(self._on_play_finished)
        self._audio.playback_paused.connect(self._on_play_paused)
        self._audio.playback_resumed.connect(self._on_play_resumed)
        self._audio.generation_started.connect(self._on_generating)
        self._audio.generation_finished.connect(self._on_gen_finished)
        self._audio.playback_error.connect(self._on_error)

    def load_voices(self, voices):
        """Populate voice selector."""
        self._voice_combo.blockSignals(True)
        self._voice_combo.clear()
        for v in voices:
            self._voice_combo.addItem(f"{v['name']} ({v['accent']})", v["id"])
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
        # Restore saved volume
        saved_vol = self._load_setting("volume")
        if saved_vol is not None:
            self._vol_slider.setValue(int(saved_vol))
            self._audio.set_volume(int(saved_vol) / 100.0)

    # ── Text Tab Actions ─────────────────────────────────

    def _import_txt(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Text File", "",
            "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
                self._text_edit.setPlainText(text)
                self._current_file = filepath
                self._status_label.setText(f"Loaded: {os.path.basename(filepath)}")
            except Exception as e:
                self._status_label.setText(f"Error: {e}")

    def _paste_text(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self._text_edit.insertPlainText(text)

    def _clear_text(self):
        self._text_edit.clear()
        self._current_file = None
        self._status_label.setText("Cleared")

    def _on_text_changed(self):
        text = self._text_edit.toPlainText()
        count = len(text)
        self._char_count.setText(f"{count:,} chars")

    # ── PDF Tab Actions ──────────────────────────────────

    def _open_pdf(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "",
            "PDF Files (*.pdf)"
        )
        if filepath:
            try:
                import fitz  # PyMuPDF
                self._pdf_doc = fitz.open(filepath)
                self._pdf_total_pages = len(self._pdf_doc)
                self._pdf_page = 0
                self._current_file = filepath
                self._render_pdf_page()
                self._update_page_nav()
                self._status_label.setText(f"Loaded: {os.path.basename(filepath)}")
            except ImportError:
                self._status_label.setText("Error: PyMuPDF not installed")
            except Exception as e:
                self._status_label.setText(f"Error: {e}")

    def _render_pdf_page(self):
        """Render the current PDF page scaled to fit the scroll area width."""
        if not self._pdf_doc:
            return

        try:
            page = self._pdf_doc.load_page(self._pdf_page)
            import fitz

            # Get available width (scroll area minus padding/margins)
            available_width = self._pdf_scroll.viewport().width() - 16
            if available_width < 200:
                available_width = 700

            # Calculate zoom to fit width
            page_rect = page.rect
            page_width = page_rect.width
            zoom = available_width / page_width
            zoom = max(zoom, 0.5)  # Don't go too small

            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # Convert to QImage
            if pix.alpha:
                fmt = QImage.Format.Format_RGBA8888
            else:
                fmt = QImage.Format.Format_RGB888

            qt_img = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            pixmap = QPixmap.fromImage(qt_img)

            # Display
            self._pdf_label.setPixmap(pixmap)
            self._pdf_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
            self._pdf_label.setStyleSheet("background: white; padding: 4px;")

        except Exception as e:
            self._pdf_label.setText(f"Error rendering page: {e}")

    def _update_page_nav(self):
        """Update page navigation UI."""
        self._page_label.setText(f"Page {self._pdf_page + 1} / {self._pdf_total_pages}")
        self._prev_page_btn.setEnabled(self._pdf_page > 0)
        self._next_page_btn.setEnabled(self._pdf_page < self._pdf_total_pages - 1)

    def _prev_pdf_page(self):
        if self._pdf_page > 0:
            self._pdf_page -= 1
            self._render_pdf_page()
            self._update_page_nav()

    def _next_pdf_page(self):
        if self._pdf_page < self._pdf_total_pages - 1:
            self._pdf_page += 1
            self._render_pdf_page()
            self._update_page_nav()

    def _extract_page_text(self):
        """Extract text from the current PDF page and put it in the text tab."""
        if not self._pdf_doc:
            self._status_label.setText("No PDF loaded")
            return

        try:
            page = self._pdf_doc.load_page(self._pdf_page)
            text = page.get_text("text")
            if text.strip():
                self._text_edit.setPlainText(text)
                self._tabs.setCurrentIndex(0)  # Switch to text tab
                self._status_label.setText(f"Extracted page {self._pdf_page + 1} text")
            else:
                self._status_label.setText("No text found on this page")
        except Exception as e:
            self._status_label.setText(f"Error: {e}")

    # ── Playback Controls ────────────────────────────────

    def _on_play(self):
        # If paused, resume
        if self._audio.is_paused:
            self._audio.resume()
            return
        text = self._text_edit.toPlainText().strip()
        if not text:
            self._status_label.setText("No text to read")
            return
        self._audio.speak(text)

    def _on_pause(self):
        self._audio.pause()

    def _on_stop(self):
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
        self._save_setting("speed", value)

    def _on_volume_changed(self, value):
        self._audio.set_volume(value / 100.0)
        self._save_setting("volume", value)

    # ── Translation Actions ─────────────────────────────

    def _translate_paste(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self._translate_input.setPlainText(text)

    def _translate_clear(self):
        self._translate_input.clear()
        self._translate_output.clear()
        self._translate_status.setText("")

    def _on_translate_lang_changed(self, index):
        lang_code = self._translate_lang_combo.currentData()
        if lang_code:
            self._save_setting("target_lang", lang_code)

    def _do_translate(self):
        """Translate the input text."""
        text = self._translate_input.toPlainText().strip()
        if not text:
            self._translate_status.setText("⚠️ No text to translate")
            return
        self._translate_btn.setEnabled(False)
        self._translate_status.setText("⏳ Translating...")
        self._translate_output.clear()
        target = self._translate_lang_combo.currentData()
        thread = threading.Thread(
            target=self._run_translation,
            args=(text, target),
            daemon=True
        )
        thread.start()

    def _run_translation(self, text, target_lang):
        """Run translation in background thread."""
        translated = self._audio.translate(text, target_lang=target_lang)
        if translated:
            self._translate_done.emit(translated)
        else:
            self._translate_failed.emit()

    def _show_translate_result(self, translated):
        self._translate_output.setPlainText(translated)
        self._translate_status.setText(f"✅ Translated to {self._translate_lang_combo.currentText()}")
        self._translate_btn.setEnabled(True)

    def _show_translate_error(self):
        self._translate_status.setText("❌ Translation failed — check internet connection")
        self._translate_btn.setEnabled(True)

    # ── Settings Persistence ────────────────────────────

    def _load_setting(self, key, default=None):
        try:
            if os.path.exists(self._settings_path):
                with open(self._settings_path, "r") as f:
                    settings = json.load(f)
                return settings.get(key, default)
        except Exception:
            pass
        return default

    def _save_setting(self, key, value):
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

    # ── Audio Signal Handlers ────────────────────────────

    def _on_play_started(self):
        self._progress_bar.hide()
        self._waveform.show()
        self._waveform.set_playing(True)
        self._play_btn.setVisible(False)
        self._play_btn.setEnabled(True)
        self._pause_btn.setVisible(True)
        self._stop_btn.setEnabled(True)
        self._status_label.setText("Playing...")

    def _on_play_paused(self):
        self._waveform.set_playing(False)
        self._pause_btn.setVisible(False)
        self._play_btn.setVisible(True)
        self._play_btn.setText("▶  Resume")
        self._status_label.setText("Paused")

    def _on_play_resumed(self):
        self._waveform.set_playing(True)
        self._play_btn.setVisible(False)
        self._pause_btn.setVisible(True)
        self._status_label.setText("Playing...")

    def _on_play_finished(self):
        self._waveform.set_playing(False)
        self._waveform.hide()
        self._progress_bar.hide()
        self._play_btn.setVisible(True)
        self._play_btn.setEnabled(True)
        self._play_btn.setText("▶  Play")
        self._pause_btn.setVisible(False)
        self._stop_btn.setEnabled(False)
        self._status_label.setText("Ready")

    def _on_generating(self):
        self._status_label.setText("⏳ Generating speech...")
        self._progress_bar.show()
        self._waveform.hide()
        self._waveform.set_playing(False)
        self._play_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

    def _on_gen_finished(self, duration):
        self._play_btn.setEnabled(True)
        self._progress_bar.hide()
        self._status_label.setText(f"Generated {duration:.1f}s of audio")

    def _on_error(self, msg):
        self._play_btn.setVisible(True)
        self._play_btn.setEnabled(True)
        self._play_btn.setText("▶  Play")
        self._pause_btn.setVisible(False)
        self._stop_btn.setEnabled(False)
        self._waveform.set_playing(False)
        self._waveform.hide()
        self._progress_bar.hide()
        self._status_label.setText(f"❌ {msg}")
        QTimer.singleShot(5000, lambda: self._status_label.setText("Ready"))

    # ── Window Events ────────────────────────────────────

    def closeEvent(self, event):
        """Hide instead of close."""
        event.ignore()
        self.hide()

    def resizeEvent(self, event):
        """Re-render PDF when window is resized to maintain fit-to-width."""
        super().resizeEvent(event)
        if self._pdf_doc:
            # Delay slightly so layout settles
            QTimer.singleShot(50, self._render_pdf_page)

    def paintEvent(self, event):
        """Custom paint for rounded corners and border."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(COLORS['bg_dark']))
        grad.setColorAt(1, QColor(COLORS['bg_main']))
        p.setBrush(grad)
        p.setPen(QColor(COLORS['border']))

        if self.isMaximized():
            p.drawRect(0, 0, self.width() - 1, self.height() - 1)
        else:
            p.drawRoundedRect(0, 0, self.width() - 1, self.height() - 1, 12, 12)
        p.end()

