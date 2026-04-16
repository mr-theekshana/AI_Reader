# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for AI Reader v3 — Native AIMP-Style Windows App
"""

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files

BASE = os.path.abspath('.')

# Collect all binaries, data, and submodules for complex packages
onnx_datas, onnx_binaries, onnx_hidden = collect_all('onnxruntime')
kokoro_datas, kokoro_binaries, kokoro_hidden = collect_all('kokoro_onnx')
lang_datas = collect_data_files('language_tags')
phonemizer_datas, phonemizer_binaries, phonemizer_hidden = collect_all('phonemizer')

a = Analysis(
    ['main.py'],
    pathex=[BASE],
    binaries=onnx_binaries + kokoro_binaries,
    datas=[
        # Models
        ('models/kokoro-v1.0.onnx', 'models'),
        ('models/voices-v1.0.bin', 'models'),
        # CRT (Microsoft Visual C++ Redistributable 2015-2022)
        ('C:/Windows/System32/msvcp140.dll', '.'),
        ('C:/Windows/System32/msvcp140_1.dll', '.'),
        ('C:/Windows/System32/msvcp140_2.dll', '.'),
        ('C:/Windows/System32/vcruntime140.dll', '.'),
        ('C:/Windows/System32/vcruntime140_1.dll', '.'),
        ('C:/Windows/System32/vccorlib140.dll', '.'),
        # ONNX Native DLLs (Forced into root)
        ('venv_311/Lib/site-packages/onnxruntime/capi/onnxruntime.dll', '.'),
        ('venv_311/Lib/site-packages/onnxruntime/capi/onnxruntime_providers_shared.dll', '.'),
        # ESpeak Backend (Forced into root as requested by error)
        ('venv_311/Lib/site-packages/phonemizer/backend/espeak', 'espeak'),
    ] + onnx_datas + kokoro_datas + lang_datas + phonemizer_datas,
    hiddenimports=[
        'soundfile',
        'numpy',
        'onnxruntime',
        'kokoro_onnx',
        'phonemizer',
        'flask',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtMultimedia',
        'PyQt6.sip',
        'pynput',
        'pynput.mouse',
        'pynput.mouse._win32',
        'pyperclip',
        'pyautogui',
        'fitz',
        'pymupdf',
        'requests',
        'PIL',
        'PIL.Image',
        'ui',
        'ui.styles',
        'ui.widgets',
        'ui.tray',
        'ui.top_bar',
        'ui.reader_window',
        'audio_player',
        'selection_monitor',
        'server',
        'setup',
        'deep_translator',
        'deep_translator.google',
        'webbrowser',
    ] + onnx_hidden + kokoro_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PySide6', 'PySide2', 'PyQt5', 'onnxruntime.quantization', 'onnx'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI Reader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AI Reader',
)
