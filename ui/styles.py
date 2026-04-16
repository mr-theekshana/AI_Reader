"""
AI Reader — Qt Stylesheets (QSS)
AIMP-inspired dark glassmorphism theme with purple/indigo accents.
"""

# ── Color Palette ─────────────────────────────────────────
COLORS = {
    "bg_dark":      "#08081a",
    "bg_main":      "#0e0e28",
    "bg_card":      "#14143a",
    "bg_card_alt":  "#1a1a4a",
    "bg_input":     "#0c0c2a",
    "bg_hover":     "#1e1e55",
    "bg_pressed":   "#28286a",

    "accent":       "#7c3aed",
    "accent_light": "#a78bfa",
    "accent_glow":  "#8b5cf6",
    "accent_dim":   "#5b21b6",

    "success":      "#22c55e",
    "warning":      "#f59e0b",
    "error":        "#ef4444",

    "text_primary": "#e8e8ff",
    "text_secondary":"#9898cc",
    "text_dim":     "#6868aa",

    "border":       "#2a2a5a",
    "border_light": "#3a3a7a",
    "border_accent":"#7c3aed",

    "scrollbar":    "#2a2a5a",
    "scrollbar_hover": "#3a3a7a",
}


def get_main_stylesheet():
    """Return the main application stylesheet."""
    c = COLORS
    return f"""
    /* ── Global ───────────────────────────────────────── */
    QWidget {{
        background-color: {c['bg_main']};
        color: {c['text_primary']};
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 13px;
        selection-background-color: {c['accent']};
        selection-color: white;
    }}

    /* ── Labels ───────────────────────────────────────── */
    QLabel {{
        background: transparent;
        padding: 0px;
        border: none;
    }}

    /* ── Buttons ──────────────────────────────────────── */
    QPushButton {{
        background-color: {c['bg_card']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: {c['bg_hover']};
        border-color: {c['accent']};
    }}
    QPushButton:pressed {{
        background-color: {c['bg_pressed']};
    }}
    QPushButton:disabled {{
        background-color: {c['bg_dark']};
        color: {c['text_dim']};
        border-color: {c['bg_card']};
    }}

    /* ── Accent Buttons ───────────────────────────────── */
    QPushButton[class="accent"] {{
        background-color: {c['accent']};
        border: 1px solid {c['accent_light']};
        color: white;
        font-weight: bold;
    }}
    QPushButton[class="accent"]:hover {{
        background-color: {c['accent_glow']};
    }}
    QPushButton[class="accent"]:pressed {{
        background-color: {c['accent_dim']};
    }}

    /* ── Combo Box ────────────────────────────────────── */
    QComboBox {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 12px;
        min-height: 22px;
    }}
    QComboBox:hover {{
        border-color: {c['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {c['text_secondary']};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['bg_card']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        selection-background-color: {c['accent']};
        selection-color: white;
        outline: none;
    }}

    /* ── Slider ───────────────────────────────────────── */
    QSlider::groove:horizontal {{
        height: 6px;
        background: {c['bg_card']};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {c['accent']};
        border: 2px solid {c['accent_light']};
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {c['accent_glow']};
        border-color: white;
    }}
    QSlider::sub-page:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c['accent_dim']}, stop:1 {c['accent']});
        border-radius: 3px;
    }}

    /* ── Text Edit / Plain Text ──────────────────────── */
    QTextEdit, QPlainTextEdit {{
        background-color: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
        line-height: 1.6;
    }}
    QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {c['accent']};
    }}

    /* ── Scrollbars ──────────────────────────────────── */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['scrollbar']};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['scrollbar_hover']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c['scrollbar']};
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c['scrollbar_hover']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ── Tab Widget ──────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        border-radius: 8px;
        background: {c['bg_card']};
        top: -1px;
    }}
    QTabBar::tab {{
        background: {c['bg_dark']};
        color: {c['text_secondary']};
        border: 1px solid {c['border']};
        border-bottom: none;
        padding: 10px 24px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: {c['bg_card']};
        color: {c['accent_light']};
        border-color: {c['accent']};
    }}
    QTabBar::tab:hover:!selected {{
        background: {c['bg_hover']};
        color: {c['text_primary']};
    }}

    /* ── Group Box ────────────────────────────────────── */
    QGroupBox {{
        background: {c['bg_card']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        margin-top: 12px;
        padding-top: 18px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 6px;
        color: {c['accent_light']};
    }}

    /* ── Tool Tips ─────────────────────────────────────── */
    QToolTip {{
        background: {c['bg_card']};
        color: {c['text_primary']};
        border: 1px solid {c['accent']};
        border-radius: 6px;
        padding: 6px 10px;
    }}

    /* ── Menu ──────────────────────────────────────────── */
    QMenu {{
        background: {c['bg_card']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background: {c['accent']};
        color: white;
    }}
    QMenu::separator {{
        height: 1px;
        background: {c['border']};
        margin: 4px 8px;
    }}
    """


def get_topbar_stylesheet():
    """Return stylesheet for the auto-hiding top bar."""
    c = COLORS
    return f"""
    QWidget#TopBar {{
        background: transparent;
        border: none;
    }}

    QWidget#TopBar > * {{
        background: transparent;
    }}

    QLabel#TextPreview {{
        color: {c['text_primary']};
        font-size: 13px;
        background: transparent;
        padding: 0 8px;
    }}

    QLabel#StatusLabel {{
        color: {c['accent_light']};
        font-size: 11px;
        background: transparent;
    }}

    QPushButton#PlayBtn {{
        background: {c['accent']};
        border: none;
        border-radius: 15px;
        color: white;
        font-size: 14px;
        font-weight: bold;
        min-width: 30px;
        min-height: 30px;
        max-width: 30px;
        max-height: 30px;
    }}
    QPushButton#PlayBtn:hover {{
        background: {c['accent_glow']};
    }}
    QPushButton#PlayBtn:pressed {{
        background: {c['accent_dim']};
    }}

    QPushButton#PauseBtn {{
        background: {c['accent']};
        border: none;
        border-radius: 15px;
        color: white;
        font-size: 16px;
        font-weight: bold;
        min-width: 30px;
        min-height: 30px;
        max-width: 30px;
        max-height: 30px;
        letter-spacing: -2px;
        padding-bottom: 2px;
    }}
    QPushButton#PauseBtn:hover {{
        background: {c['accent_glow']};
    }}
    QPushButton#PauseBtn:pressed {{
        background: {c['accent_dim']};
    }}

    QPushButton#StopBtn {{
        background: {c['error']};
        border: none;
        border-radius: 15px;
        color: white;
        font-size: 12px;
        font-weight: bold;
        min-width: 30px;
        min-height: 30px;
        max-width: 30px;
        max-height: 30px;
    }}
    QPushButton#StopBtn:hover {{
        background: #dc2626;
    }}

    QComboBox#VoiceCombo {{
        background: {c['bg_input']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 4px 8px;
        min-width: 90px;
        max-height: 28px;
        font-size: 12px;
    }}

    QSlider#SpeedSlider::groove:horizontal {{
        height: 4px;
        background: {c['bg_dark']};
        border-radius: 2px;
    }}
    QSlider#SpeedSlider::handle:horizontal {{
        background: {c['accent']};
        border: 1px solid {c['accent_light']};
        width: 12px;
        height: 12px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider#SpeedSlider::sub-page:horizontal {{
        background: {c['accent']};
        border-radius: 2px;
    }}
    """


def get_titlebar_stylesheet():
    """Return stylesheet for custom title bar."""
    c = COLORS
    return f"""
    QWidget#TitleBar {{
        background: {c['bg_dark']};
        border-bottom: 1px solid {c['border']};
    }}

    QLabel#TitleLabel {{
        color: {c['accent_light']};
        font-size: 13px;
        font-weight: bold;
        background: transparent;
    }}

    QPushButton#MinBtn, QPushButton#CloseBtn {{
        background: transparent;
        border: none;
        border-radius: 4px;
        color: {c['text_secondary']};
        font-size: 14px;
        min-width: 32px;
        min-height: 28px;
        max-width: 32px;
        max-height: 28px;
    }}
    QPushButton#MinBtn:hover {{
        background: {c['bg_hover']};
        color: {c['text_primary']};
    }}
    QPushButton#CloseBtn:hover {{
        background: {c['error']};
        color: white;
    }}
    """
