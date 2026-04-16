/* ============================================================
   AI Reader — Core TTS Engine & UI Logic
   v2: Kokoro TTS via Python backend
   ============================================================ */

(function () {
  'use strict';

  const API_BASE = window.location.origin;

  // ────────────────────────────────────────────
  // DOM References
  // ────────────────────────────────────────────
  const textInput       = document.getElementById('text-input');
  const charCount       = document.getElementById('char-count');
  const fileInput       = document.getElementById('file-input');
  const dropOverlay     = document.getElementById('drop-overlay');
  const voiceSelect     = document.getElementById('voice-select');
  const btnPaste       = document.getElementById('btn-paste');
  const btnClear       = document.getElementById('btn-clear');

  const speedSlider     = document.getElementById('speed-slider');
  const volumeSlider    = document.getElementById('volume-slider');
  const speedValue      = document.getElementById('speed-value');
  const volumeValue     = document.getElementById('volume-value');

  const btnPlay         = document.getElementById('btn-play');
  const btnPlayIcon     = document.getElementById('btn-play-icon');
  const btnPlayLabel    = document.getElementById('btn-play-label');
  const btnPause        = document.getElementById('btn-pause');
  const btnStop         = document.getElementById('btn-stop');

  const statusDot       = document.getElementById('status-dot');
  const statusText      = document.getElementById('status-text');
  const waveform        = document.getElementById('waveform');

  const progressFill    = document.getElementById('progress-fill');
  const progressPct     = document.getElementById('progress-pct');
  const progressElapsed = document.getElementById('progress-elapsed');

  const readingDisplay  = document.getElementById('reading-display');

  // ────────────────────────────────────────────
  // State
  // ────────────────────────────────────────────
  let currentState    = 'idle'; // idle | loading | speaking | paused
  let audioElement    = null;
  let sentences       = [];
  let sentenceSpans   = [];
  let elapsedTimer    = null;
  let startTime       = 0;
  let pauseElapsed    = 0;
  let previousVolume  = 1;

  // ────────────────────────────────────────────
  // Voice Manager — Load from Backend
  // ────────────────────────────────────────────
  async function loadVoices() {
    try {
      const res = await fetch(`${API_BASE}/api/voices`);
      const data = await res.json();

      voiceSelect.innerHTML = '';
      data.voices.forEach((v) => {
        const opt = document.createElement('option');
        opt.value = v.id;
        const genderIcon = v.gender === 'Female' ? '👩' : '👨';
        const flag = v.accent === 'British' ? '🇬🇧' : '🇺🇸';
        opt.textContent = `${genderIcon} ${v.name} — ${v.style} ${flag}`;
        voiceSelect.appendChild(opt);
      });

      // Restore saved voice
      const savedVoice = localStorage.getItem('ai-reader-voice');
      if (savedVoice) {
        const exists = Array.from(voiceSelect.options).some(o => o.value === savedVoice);
        if (exists) voiceSelect.value = savedVoice;
      }
    } catch (err) {
      console.error('Failed to load voices:', err);
      voiceSelect.innerHTML = '<option value="af_sarah">Sarah (default)</option>';
    }
  }

  loadVoices();

  voiceSelect.addEventListener('change', () => {
    localStorage.setItem('ai-reader-voice', voiceSelect.value);
  });

  // ────────────────────────────────────────────
  // Settings Sliders
  // ────────────────────────────────────────────
  function loadSettings() {
    const s = localStorage.getItem('ai-reader-speed');
    const v = localStorage.getItem('ai-reader-volume');
    if (s) speedSlider.value  = s;
    if (v) volumeSlider.value = v;
    updateSliderLabels();
  }

  function updateSliderLabels() {
    speedValue.textContent  = parseFloat(speedSlider.value).toFixed(1) + '×';
    volumeValue.textContent = Math.round(volumeSlider.value * 100) + '%';
  }

  function saveSettings() {
    localStorage.setItem('ai-reader-speed', speedSlider.value);
    localStorage.setItem('ai-reader-volume', volumeSlider.value);
  }

  speedSlider.addEventListener('input', () => { updateSliderLabels(); saveSettings(); });
  volumeSlider.addEventListener('input', () => {
    updateSliderLabels();
    saveSettings();
    if (audioElement) {
      audioElement.volume = parseFloat(volumeSlider.value);
    }
  });
  loadSettings();

  // ────────────────────────────────────────────
  // Character Count
  // ────────────────────────────────────────────
  textInput.addEventListener('input', () => {
    const len = textInput.value.length;
    charCount.textContent = len.toLocaleString() + ' character' + (len !== 1 ? 's' : '');
  });

  // ────────────────────────────────────────────
  // File Import
  // ────────────────────────────────────────────
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) readFile(file);
  });

  function readFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      textInput.value = e.target.result;
      textInput.dispatchEvent(new Event('input'));
    };
    reader.readAsText(file);
  }

  // Drag & Drop
  const textareaWrapper = textInput.parentElement;

  textareaWrapper.addEventListener('dragenter', (e) => {
    e.preventDefault();
    dropOverlay.classList.add('active');
  });

  textareaWrapper.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  textareaWrapper.addEventListener('dragleave', (e) => {
    if (!textareaWrapper.contains(e.relatedTarget)) {
      dropOverlay.classList.remove('active');
    }
  });

  textareaWrapper.addEventListener('drop', (e) => {
    e.preventDefault();
    dropOverlay.classList.remove('active');
    const file = e.dataTransfer.files[0];
    if (file) readFile(file);
  });

  // ────────────────────────────────────────────
  // State Management
  // ────────────────────────────────────────────
  function setState(state) {
    currentState = state;

    // Status indicator
    statusDot.className = 'status-dot ' + (state === 'loading' ? 'speaking' : state);
    const labels = {
      idle: 'Ready',
      loading: 'Generating AI voice…',
      speaking: 'Reading…',
      paused: 'Paused'
    };
    statusText.textContent = labels[state] || 'Ready';

    // Waveform
    waveform.className = 'waveform' + (
      state === 'speaking' ? ' active' :
      state === 'loading' ? ' active' :
      state === 'paused' ? ' paused' : ''
    );

    // Buttons
    if (state === 'idle') {
      btnPlayIcon.textContent  = '▶';
      btnPlayLabel.textContent = 'Play';
      btnPause.disabled = true;
      btnStop.disabled  = true;
      btnPlay.disabled  = false;
      progressFill.classList.remove('active');
    } else if (state === 'loading') {
      btnPlayIcon.textContent  = '⏳';
      btnPlayLabel.textContent = 'Generating…';
      btnPause.disabled = true;
      btnStop.disabled  = false;
      btnPlay.disabled  = true;
      progressFill.classList.add('active');
    } else if (state === 'speaking') {
      btnPlayIcon.textContent  = '▶';
      btnPlayLabel.textContent = 'Playing';
      btnPause.disabled = false;
      btnStop.disabled  = false;
      btnPlay.disabled  = true;
      progressFill.classList.add('active');
    } else if (state === 'paused') {
      btnPlayIcon.textContent  = '▶';
      btnPlayLabel.textContent = 'Resume';
      btnPause.disabled = true;
      btnStop.disabled  = false;
      btnPlay.disabled  = false;
      progressFill.classList.remove('active');
    }
  }

  // ────────────────────────────────────────────
  // Reading Display — sentence-level highlighting
  // ────────────────────────────────────────────
  function buildReadingDisplay(text) {
    readingDisplay.innerHTML = '';
    sentences    = [];
    sentenceSpans = [];

    // Split into sentences
    const parts = text.match(/[^.!?\n]+[.!?\n]?/g) || [text];

    parts.forEach((sentence) => {
      const trimmed = sentence.trim();
      if (!trimmed) return;

      const span = document.createElement('span');
      span.className = 'word'; // reuse the .word styles
      span.textContent = trimmed + ' ';
      readingDisplay.appendChild(span);
      sentences.push(trimmed);
      sentenceSpans.push(span);
    });
  }

  function highlightSentenceAtTime(currentTime, duration) {
    if (!sentenceSpans.length || !duration) return;

    const progress = currentTime / duration;
    const idx = Math.min(
      Math.floor(progress * sentenceSpans.length),
      sentenceSpans.length - 1
    );

    sentenceSpans.forEach((span, i) => {
      if (i < idx) {
        span.classList.add('spoken');
        span.classList.remove('active');
      } else if (i === idx) {
        span.classList.add('active');
        span.classList.remove('spoken');
        // Auto-scroll
        const displayRect = readingDisplay.getBoundingClientRect();
        const spanRect = span.getBoundingClientRect();
        if (spanRect.top < displayRect.top || spanRect.bottom > displayRect.bottom) {
          span.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
      } else {
        span.classList.remove('active', 'spoken');
      }
    });
  }

  function clearHighlights() {
    sentenceSpans.forEach(span => span.classList.remove('active', 'spoken'));
  }

  function markAllSpoken() {
    sentenceSpans.forEach(span => {
      span.classList.add('spoken');
      span.classList.remove('active');
    });
  }

  // ────────────────────────────────────────────
  // Progress / Timer
  // ────────────────────────────────────────────
  function updateProgress(pct) {
    progressFill.style.width = pct + '%';
    progressPct.textContent  = Math.round(pct) + '%';
  }

  function startTimer() {
    startTime = Date.now() - (pauseElapsed || 0);
    elapsedTimer = setInterval(() => {
      if (currentState !== 'speaking') return;
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const mins = Math.floor(elapsed / 60);
      const secs = elapsed % 60;
      progressElapsed.textContent = mins + ':' + String(secs).padStart(2, '0');

      // Update progress from audio element
      if (audioElement && audioElement.duration) {
        const pct = (audioElement.currentTime / audioElement.duration) * 100;
        updateProgress(pct);
        highlightSentenceAtTime(audioElement.currentTime, audioElement.duration);
      }
    }, 200);
  }

  function stopTimer() {
    clearInterval(elapsedTimer);
  }

  function resetProgress() {
    progressFill.style.width = '0%';
    progressPct.textContent  = '0%';
    progressElapsed.textContent = '0:00';
  }

  // ────────────────────────────────────────────
  // TTS Playback via Backend
  // ────────────────────────────────────────────
  async function speak() {
    const text = textInput.value.trim();
    if (!text) {
      textInput.focus();
      return;
    }

    // If paused, resume
    if (currentState === 'paused' && audioElement) {
      audioElement.play();
      setState('speaking');
      startTimer();
      return;
    }

    // Stop any existing playback
    stopPlayback();

    // Build display
    buildReadingDisplay(text);
    resetProgress();
    pauseElapsed = 0;

    // Set loading state
    setState('loading');

    try {
      const res = await fetch(`${API_BASE}/api/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          voice: voiceSelect.value,
          speed: parseFloat(speedSlider.value),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(err.error || `HTTP ${res.status}`);
      }

      // Get audio blob
      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      // Create audio element
      audioElement = new Audio(audioUrl);
      audioElement.volume = parseFloat(volumeSlider.value);

      audioElement.addEventListener('canplaythrough', () => {
        audioElement.play();
        setState('speaking');
        startTimer();
      }, { once: true });

      audioElement.addEventListener('ended', () => {
        markAllSpoken();
        updateProgress(100);
        stopTimer();
        setState('idle');
        URL.revokeObjectURL(audioUrl);
      });

      audioElement.addEventListener('error', (e) => {
        console.error('Audio playback error:', e);
        stopTimer();
        setState('idle');
        URL.revokeObjectURL(audioUrl);
      });

      audioElement.load();

    } catch (err) {
      console.error('TTS Error:', err);
      setState('idle');
      statusText.textContent = 'Error: ' + err.message;
    }
  }

  function pause() {
    if (currentState === 'speaking' && audioElement) {
      audioElement.pause();
      pauseElapsed = Date.now() - startTime;
      stopTimer();
      setState('paused');
    }
  }

  function stopPlayback() {
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
      audioElement = null;
    }
    // Tell backend to stop any ongoing generation
    fetch(`${API_BASE}/api/stop`, { method: 'POST' }).catch(() => {});
    stopTimer();
    resetProgress();
    clearHighlights();
    setState('idle');
  }

  // ────────────────────────────────────────────
  // Button Handlers
  // ────────────────────────────────────────────
  btnPlay.addEventListener('click', speak);
  btnPause.addEventListener('click', pause);
  btnStop.addEventListener('click', stopPlayback);

  // Clear Text
  btnClear.addEventListener('click', () => {
    textInput.value = '';
    textInput.dispatchEvent(new Event('input'));
    textInput.focus();
    if (currentState === 'speaking' || currentState === 'paused') {
      stopPlayback();
    }
  });

  // Paste Text
  btnPaste.addEventListener('click', async () => {
    try {
      let text = '';
      
      // Check if running in native app mode (pywebview)
      if (typeof pywebview !== 'undefined' && pywebview.api && pywebview.api.get_clipboard) {
        text = await pywebview.api.get_clipboard();
      } else if (navigator.clipboard) {
        // Fallback to standard web API
        text = await navigator.clipboard.readText();
      }

      if (text) {
        textInput.value = text;
        // Trigger input event to update char count and other listeners
        textInput.dispatchEvent(new Event('input'));
        textInput.focus();
      }
    } catch (err) {
      console.error('Failed to paste:', err);
      alert('Could not access clipboard. Please paste manually (Ctrl+V).');
    }
  });

  // ────────────────────────────────────────────
  // Keyboard Shortcuts
  // ────────────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    // Don't capture shortcuts when typing in textarea
    if (e.target === textInput) return;

    switch (e.code) {
      case 'Space':
        e.preventDefault();
        if (currentState === 'speaking') pause();
        else if (currentState === 'paused' || currentState === 'idle') speak();
        break;

      case 'Escape':
        e.preventDefault();
        stopPlayback();
        break;

      case 'ArrowUp':
        e.preventDefault();
        speedSlider.value = Math.min(3, parseFloat(speedSlider.value) + 0.1);
        updateSliderLabels();
        saveSettings();
        break;

      case 'ArrowDown':
        e.preventDefault();
        speedSlider.value = Math.max(0.5, parseFloat(speedSlider.value) - 0.1);
        updateSliderLabels();
        saveSettings();
        break;

      case 'KeyM':
        e.preventDefault();
        if (parseFloat(volumeSlider.value) > 0) {
          previousVolume = volumeSlider.value;
          volumeSlider.value = 0;
        } else {
          volumeSlider.value = previousVolume;
        }
        updateSliderLabels();
        saveSettings();
        if (audioElement) {
          audioElement.volume = parseFloat(volumeSlider.value);
        }
        break;
    }
  });

  // ────────────────────────────────────────────
  // Init
  // ────────────────────────────────────────────
  setState('idle');

  // Restore text from sessionStorage
  const savedText = sessionStorage.getItem('ai-reader-text');
  if (savedText) {
    textInput.value = savedText;
    textInput.dispatchEvent(new Event('input'));
  }
  textInput.addEventListener('input', () => {
    sessionStorage.setItem('ai-reader-text', textInput.value);
  });

})();
