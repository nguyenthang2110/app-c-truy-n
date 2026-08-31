# TTS Player component with modern UI

import base64
import streamlit as st

from config.settings import (
    DEFAULT_RATE, DEFAULT_PITCH, MIN_RATE, MAX_RATE,
    MIN_PITCH, MAX_PITCH, RATE_STEP, PITCH_STEP, BASE_CPS
)


def get_tts_html(
    text_b64: str,
    auto_play: bool = False,
    is_dark: bool = True,
) -> str:
    """Generate the TTS player HTML with the app's selected color mode."""
    auto_play_js = "true" if auto_play else "false"
    if is_dark:
        theme = {
            "surface": "#15181d",
            "surface_muted": "#1d2127",
            "text": "#f4f5f7",
            "muted": "#a8afb9",
            "border": "#2a3038",
            "border_strong": "#3a424d",
            "accent": "#4f7cff",
            "accent_hover": "#6a8fff",
            "editor": "#111419",
            "highlight": "#ffe074",
            "highlight_text": "#17191d",
            "scroll": "#3c444f",
        }
    else:
        theme = {
            "surface": "#ffffff",
            "surface_muted": "#f1f3f6",
            "text": "#17191d",
            "muted": "#68707b",
            "border": "#dfe3e8",
            "border_strong": "#c5cbd3",
            "accent": "#315fd6",
            "accent_hover": "#264fb7",
            "editor": "#ffffff",
            "highlight": "#ffdf6e",
            "highlight_text": "#17191d",
            "scroll": "#c4cad2",
        }
    
    return f"""
<style>
  :root {{
    --bg-primary: #0e1117;
    --bg-secondary: #1a1a2e;
    --bg-tertiary: #16213e;
    --bg-card: rgba(26, 26, 46, 0.8);
    --text-primary: #fafafa;
    --text-secondary: #a0aec0;
    --accent-primary: #667eea;
    --accent-secondary: #764ba2;
    --accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --highlight-bg: #ffd60a;
    --highlight-text: #1a1a2e;
    --border-color: rgba(255, 255, 255, 0.1);
    --glass-bg: rgba(255, 255, 255, 0.05);
    --glass-border: rgba(255, 255, 255, 0.1);
    --shadow-sm: 0 2px 4px rgba(0,0,0,0.2);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.3);
    --shadow-lg: 0 8px 24px rgba(0,0,0,0.4);
    --shadow-glow: 0 0 20px rgba(102, 126, 234, 0.3);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
  }}

  @media (prefers-color-scheme: light) {{
    :root {{
      --bg-primary: #ffffff;
      --bg-secondary: #f8f9fa;
      --bg-tertiary: #e9ecef;
      --bg-card: rgba(255, 255, 255, 0.9);
      --text-primary: #1a1a2e;
      --text-secondary: #6c757d;
      --border-color: rgba(0, 0, 0, 0.1);
      --glass-bg: rgba(255, 255, 255, 0.7);
      --glass-border: rgba(0, 0, 0, 0.1);
      --shadow-sm: 0 2px 4px rgba(0,0,0,0.05);
      --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
      --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
    }}
  }}

  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: transparent;
    color: var(--text-primary);
  }}

  /* ===================== Toolbar ===================== */
  .toolbar {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    margin-bottom: 20px;
    padding: 20px 24px;
    background: var(--accent-gradient);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-lg), var(--shadow-glow);
    backdrop-filter: blur(20px);
    position: relative;
    overflow: hidden;
  }}

  .toolbar::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
    animation: shimmer 3s infinite;
  }}

  @keyframes shimmer {{
    0% {{ transform: translateX(-100%); }}
    100% {{ transform: translateX(100%); }}
  }}

  /* ===================== Buttons ===================== */
  .toolbar button {{
    position: relative;
    z-index: 1;
    padding: 12px 20px;
    border-radius: var(--radius-md);
    border: none;
    background: rgba(255, 255, 255, 0.95);
    color: var(--accent-primary);
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--shadow-sm);
    font-family: 'Inter', sans-serif;
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .toolbar button:hover {{
    transform: translateY(-3px) scale(1.02);
    box-shadow: var(--shadow-md), 0 4px 20px rgba(255,255,255,0.2);
    background: rgba(255, 255, 255, 1);
  }}

  .toolbar button:active {{
    transform: scale(0.97) translateY(0);
    transition: transform 0.1s;
  }}

  .toolbar button.playing {{
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    animation: pulse-glow 2s infinite;
  }}

  @keyframes pulse-glow {{
    0%, 100% {{ box-shadow: 0 0 5px rgba(16, 185, 129, 0.5); }}
    50% {{ box-shadow: 0 0 20px rgba(16, 185, 129, 0.8); }}
  }}

  /* ===================== Controls ===================== */
  .control-group {{
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.1);
    padding: 8px 12px;
    border-radius: var(--radius-md);
    backdrop-filter: blur(10px);
  }}

  .toolbar select {{
    padding: 10px 14px;
    border-radius: var(--radius-sm);
    border: 2px solid rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.95);
    color: var(--accent-primary);
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    max-width: 200px;
  }}

  .toolbar select:focus {{
    outline: none;
    border-color: rgba(255, 255, 255, 0.8);
    box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.2);
  }}

  /* ===================== Range Slider ===================== */
  .toolbar input[type="range"] {{
    -webkit-appearance: none;
    appearance: none;
    width: 100px;
    height: 6px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 10px;
    outline: none;
    transition: all 0.2s ease;
  }}

  .toolbar input[type="range"]:hover {{
    background: rgba(255, 255, 255, 0.5);
  }}

  .toolbar input[type="range"]::-webkit-slider-thumb {{
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    transition: all 0.2s ease;
  }}

  .toolbar input[type="range"]::-webkit-slider-thumb:hover {{
    transform: scale(1.2);
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
  }}

  .toolbar input[type="range"]::-moz-range-thumb {{
    width: 20px;
    height: 20px;
    background: white;
    border-radius: 50%;
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }}

  /* ===================== Labels ===================== */
  .label {{
    font-size: 13px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.95);
    letter-spacing: 0.3px;
    text-shadow: 0 1px 2px rgba(0,0,0,0.2);
  }}

  .value-badge {{
    font-size: 12px;
    font-weight: 700;
    color: var(--accent-primary);
    background: white;
    padding: 4px 10px;
    border-radius: var(--radius-sm);
    min-width: 45px;
    text-align: center;
  }}

  /* ===================== Status ===================== */
  #status {{
    margin-left: auto;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.95);
    font-size: 13px;
    padding: 10px 18px;
    background: rgba(255, 255, 255, 0.15);
    border-radius: var(--radius-md);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  #status::before {{
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
  }}

  #status.reading::before {{
    animation: pulse 1s infinite;
  }}

  @keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.6; transform: scale(0.8); }}
  }}

  /* ===================== Editor ===================== */
  #editor {{
    white-space: pre-wrap;
    border: 2px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: 32px;
    height: 500px;
    overflow: auto;
    line-height: 1.9;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 17px;
    font-weight: 400;
    background: var(--bg-card);
    color: var(--text-primary);
    box-shadow: var(--shadow-lg), inset 0 1px 0 rgba(255,255,255,0.1);
    transition: all 0.3s ease;
    letter-spacing: 0.3px;
    max-width: 900px;
    margin: 0 auto;
    backdrop-filter: blur(20px);
  }}

  #editor:focus {{
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2), var(--shadow-lg);
  }}

  /* Scrollbar styling */
  #editor::-webkit-scrollbar {{
    width: 10px;
  }}

  #editor::-webkit-scrollbar-track {{
    background: var(--bg-tertiary);
    border-radius: 10px;
  }}

  #editor::-webkit-scrollbar-thumb {{
    background: var(--accent-gradient);
    border-radius: 10px;
  }}

  #editor::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(135deg, #5a6fd6, #6b4190);
  }}

  /* ===================== Highlight ===================== */
  .hl {{
    background: var(--highlight-bg);
    color: var(--highlight-text);
    font-weight: 700;
    border-radius: 6px;
    padding: 3px 8px;
    box-shadow: 0 2px 12px rgba(255, 214, 10, 0.4);
    animation: highlight-pulse 0.4s ease-out;
    display: inline-block;
  }}

  #editor::highlight(current-word) {{
    background: var(--highlight-bg);
    color: var(--highlight-text);
  }}

  @keyframes highlight-pulse {{
    0% {{ transform: scale(1); background: #ffeb3b; }}
    50% {{ transform: scale(1.05); }}
    100% {{ transform: scale(1); background: var(--highlight-bg); }}
  }}

  /* ===================== Responsive ===================== */
  @media (max-width: 768px) {{
    .toolbar {{
      padding: 16px;
      gap: 10px;
      border-radius: var(--radius-lg);
    }}

    .toolbar button {{
      padding: 10px 14px;
      font-size: 13px;
    }}

    .control-group {{
      flex-wrap: wrap;
      justify-content: center;
    }}

    #editor {{
      padding: 20px;
      font-size: 16px;
      height: 400px;
      border-radius: var(--radius-lg);
    }}

    .toolbar select {{
      max-width: 150px;
    }}

    .toolbar input[type="range"] {{
      width: 80px;
    }}
  }}
</style>

<style>
  /* Minimal reader skin. Kept after the base rules so app light/dark mode wins. */
  :root {{
    --reader-surface: {theme["surface"]};
    --reader-surface-muted: {theme["surface_muted"]};
    --reader-text: {theme["text"]};
    --reader-muted: {theme["muted"]};
    --reader-border: {theme["border"]};
    --reader-border-strong: {theme["border_strong"]};
    --reader-accent: {theme["accent"]};
    --reader-accent-hover: {theme["accent_hover"]};
    --reader-editor: {theme["editor"]};
    --reader-highlight: {theme["highlight"]};
    --reader-highlight-text: {theme["highlight_text"]};
    --reader-scroll: {theme["scroll"]};
  }}

  body {{
    background: transparent;
    color: var(--reader-text);
  }}

  .toolbar {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    padding: 12px;
    overflow: visible;
    background: var(--reader-surface);
    border: 1px solid var(--reader-border);
    border-radius: 16px;
    box-shadow: none;
    backdrop-filter: none;
  }}

  .toolbar::before {{ display: none; }}

  .toolbar button {{
    min-height: 38px;
    padding: 9px 13px;
    background: var(--reader-surface-muted);
    border: 1px solid var(--reader-border);
    border-radius: 10px;
    box-shadow: none;
    color: var(--reader-text);
    font-size: 13px;
    font-weight: 650;
    transition: background 160ms ease, border-color 160ms ease, transform 160ms ease;
  }}

  .toolbar button:hover {{
    background: var(--reader-surface-muted);
    border-color: var(--reader-border-strong);
    box-shadow: none;
    transform: none;
  }}

  #btnPlay, #btnResume {{
    background: var(--reader-accent);
    border-color: var(--reader-accent);
    color: #fff;
  }}

  #btnPlay:hover, #btnResume:hover,
  .toolbar button.playing {{
    background: var(--reader-accent-hover);
    border-color: var(--reader-accent-hover);
    color: #fff;
    animation: none;
    box-shadow: none;
  }}

  .control-group {{
    gap: 7px;
    padding: 0 4px;
    background: transparent;
    border-radius: 0;
    backdrop-filter: none;
  }}

  .label {{
    color: var(--reader-muted);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0;
    text-shadow: none;
  }}

  .toolbar select {{
    min-height: 38px;
    max-width: 170px;
    padding: 8px 30px 8px 10px;
    background: var(--reader-surface-muted);
    border: 1px solid var(--reader-border);
    border-radius: 10px;
    color: var(--reader-text);
    font-size: 12px;
  }}

  .toolbar select:focus {{
    border-color: var(--reader-accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--reader-accent) 18%, transparent);
  }}

  .toolbar input[type="range"] {{
    width: 78px;
    height: 4px;
    background: var(--reader-border-strong);
  }}

  .toolbar input[type="range"]:hover {{
    background: var(--reader-border-strong);
  }}

  .toolbar input[type="range"]::-webkit-slider-thumb {{
    width: 16px;
    height: 16px;
    background: var(--reader-accent);
    box-shadow: none;
  }}

  .toolbar input[type="range"]::-webkit-slider-thumb:hover {{
    transform: none;
    box-shadow: none;
  }}

  .value-badge {{
    min-width: 38px;
    padding: 3px 7px;
    background: var(--reader-surface-muted);
    border-radius: 7px;
    color: var(--reader-text);
    font-size: 11px;
  }}

  #status {{
    margin-left: auto;
    padding: 8px 10px;
    background: var(--reader-surface-muted);
    border: 1px solid var(--reader-border);
    border-radius: 9px;
    color: var(--reader-muted);
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
    backdrop-filter: none;
  }}

  #status::before {{
    width: 6px;
    height: 6px;
    background: var(--reader-accent);
    box-shadow: none;
  }}

  #editor {{
    height: 520px;
    max-width: none;
    margin: 0;
    padding: 42px max(32px, calc((100% - 760px) / 2));
    background: var(--reader-editor);
    border: 1px solid var(--reader-border);
    border-radius: 16px;
    box-shadow: none;
    color: var(--reader-text);
    font-family: ui-serif, Georgia, "Times New Roman", serif;
    font-size: 18px;
    font-weight: 400;
    letter-spacing: 0.005em;
    line-height: 2;
    backdrop-filter: none;
  }}

  #editor:focus {{
    border-color: var(--reader-accent);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--reader-accent) 16%, transparent);
  }}

  #editor::-webkit-scrollbar {{ width: 8px; }}
  #editor::-webkit-scrollbar-track {{ background: transparent; }}
  #editor::-webkit-scrollbar-thumb {{
    background: var(--reader-scroll);
    border: 2px solid transparent;
    border-radius: 999px;
    background-clip: padding-box;
  }}

  #editor::highlight(current-word) {{
    background: var(--reader-highlight);
    color: var(--reader-highlight-text);
  }}

  @media (max-width: 900px) {{
    .toolbar {{
      align-items: stretch;
      flex-wrap: wrap;
    }}

    #status {{ margin-left: 0; }}
  }}

  @media (max-width: 620px) {{
    .toolbar {{ padding: 10px; border-radius: 14px; }}
    .control-group {{ width: 100%; justify-content: space-between; }}
    .toolbar select {{ max-width: 210px; flex: 1; }}
    #status {{ width: 100%; justify-content: center; }}
    #editor {{
      height: 470px;
      padding: 28px 22px;
      border-radius: 14px;
      font-size: 17px;
      line-height: 1.9;
    }}
  }}
</style>

<div class="toolbar">
  <button id="btnPlay">Phát</button>
  <button id="btnStop">Dừng</button>
  <button id="btnResume" style="display:none">Tiếp tục</button>

  <div class="control-group">
    <span class="label">Giọng đọc</span>
    <select id="voiceSel" title="Chọn giọng đọc"><option>Đang tải...</option></select>
  </div>

  <div class="control-group">
    <span class="label">Tốc độ</span>
    <button id="rateMinus" title="Giảm">−</button>
    <input id="rate" type="range" min="{MIN_RATE}" max="{MAX_RATE}" step="{RATE_STEP}" value="{DEFAULT_RATE}">
    <button id="ratePlus" title="Tăng">+</button>
    <span id="rateVal" class="value-badge">{DEFAULT_RATE:.2f}</span>
  </div>

  <div class="control-group">
    <span class="label">Cao độ</span>
    <input id="pitch" type="range" min="{MIN_PITCH}" max="{MAX_PITCH}" step="{PITCH_STEP}" value="{DEFAULT_PITCH}">
    <span id="pitchVal" class="value-badge">{DEFAULT_PITCH:.1f}</span>
  </div>

  <span id="status">Sẵn sàng</span>
</div>

<div id="editor" spellcheck="false" lang="vi"></div>

<script>
(function() {{
  // ==== UTF-8 decode ====
  function b64ToUtf8(b64) {{
    try {{
      const bin = window.atob(b64);
      const buf = new Uint8Array(bin.length);
      for (let i=0;i<bin.length;i++) buf[i] = bin.charCodeAt(i);
      return new TextDecoder("utf-8").decode(buf);
    }} catch(e) {{
      return "";
    }}
  }}

  const editor    = document.getElementById('editor');
  const btnPlay   = document.getElementById('btnPlay');
  const btnStop   = document.getElementById('btnStop');
  const btnResume = document.getElementById('btnResume');
  const statusEl  = document.getElementById('status');
  const voiceSel  = document.getElementById('voiceSel');
  const rateMinus = document.getElementById('rateMinus');
  const ratePlus  = document.getElementById('ratePlus');
  const rateInp   = document.getElementById('rate');
  const pitchInp  = document.getElementById('pitch');
  const rateVal   = document.getElementById('rateVal');
  const pitchVal  = document.getElementById('pitchVal');

  const fullTextOriginal = b64ToUtf8("{text_b64}") || "";
  const RATE_STEP = {RATE_STEP};
  const BASE_CPS = {BASE_CPS};
  const STORE_KEY = "doc-reader-voice-settings";
  let fullText = fullTextOriginal;
    editor.textContent = fullTextOriginal || "Chưa có nội dung. Dán liên kết chương và chọn “Mở chương” để bắt đầu.";

  // ====== Voice handling ======
  let voices = [];
  let autoPlay = {auto_play_js};
  let autoPlayedOnce = false;
  let ttsUnlocked = false;
  let wantsAutoStart = false;

  function score(v) {{
    let s=0;
    if ((v.lang||'').toLowerCase().startsWith('vi')) s+=5;
    if (/google/i.test(v.name)) s+=3;
    if (/female|nu|woman/i.test(v.name)) s+=2;
    return s;
  }}

  function waitForVoices(cb) {{
    let tries = 0;
    const t = setInterval(() => {{
      const v = window.speechSynthesis.getVoices();
      if ((v && v.length) || tries > 30) {{
        clearInterval(t);
        cb();
      }}
      tries++;
    }}, 100);
  }}

  function ensureEditorReady(cb) {{
    let tries = 0;
    const t = setInterval(() => {{
      if (editor && editor.textContent && editor.clientHeight > 0) {{
        clearInterval(t);
        cb();
      }} else if (tries > 30) {{
        clearInterval(t);
        cb();
      }}
      tries++;
    }}, 100);
  }}

  function unlockTTSIfNeeded() {{
    if (ttsUnlocked) return;
    try {{
      const u = new SpeechSynthesisUtterance(" ");
      u.volume = 0;
      u.rate = 1;
      u.onend = () => {{ ttsUnlocked = true; maybeAutoStart(); }};
      window.speechSynthesis.speak(u);
    }} catch (e) {{
      ttsUnlocked = true;
      maybeAutoStart();
    }}
  }}

  ["click","keydown","touchstart"].forEach(evt => {{
    window.addEventListener(evt, function once() {{
      window.removeEventListener(evt, once, true);
      unlockTTSIfNeeded();
    }}, true);
  }});

  function maybeAutoStart() {{
    if (!wantsAutoStart || autoPlayedOnce || !fullText) return;
    if (!ttsUnlocked) return;

    autoPlayedOnce = true;
    wantsAutoStart = false;

    const s0 = wordStartFrom(0);
    const e0 = Math.max(wordEndFrom(0), s0 + 1);
    paintHighlight(s0, e0);

    ensureEditorReady(() => {{
      const go = () => setTimeout(() => speakFrom(0), 50);
      if ((window.speechSynthesis.getVoices() || []).length) go();
      else waitForVoices(go);
    }});
  }}

  function autoStartIfNeeded() {{
    if (!autoPlay || autoPlayedOnce || !fullText) return;
    wantsAutoStart = true;
    if (ttsUnlocked) maybeAutoStart();
  }}

  function loadVoices() {{
    const all = window.speechSynthesis.getVoices() || [];
    voices = all;
    const sorted = all.slice().sort((a,b)=>score(b)-score(a));
    voiceSel.innerHTML = "";
    for (const v of sorted) {{
      const opt = document.createElement('option');
      opt.value = v.name;
      opt.textContent = `${{v.name}} (${{v.lang}})`;
      voiceSel.appendChild(opt);
    }}
    if (voiceSel.options.length>0) voiceSel.selectedIndex = 0;

    autoStartIfNeeded();
    maybeAutoStart();
  }}
  window.speechSynthesis.addEventListener('voiceschanged', loadVoices);
  loadVoices();

  autoStartIfNeeded();
  maybeAutoStart();

  // ====== Utils ======
  function wordEndFrom(i) {{
    let j = i;
    while (j < fullText.length && !/\\s/.test(fullText[j])) j++;
    return j;
  }}
  function wordStartFrom(i) {{
    let j = i;
    while (j > 0 && !/\\s/.test(fullText[j-1])) j--;
    return j;
  }}

  // ====== Optimized Highlight ======
  let lastPaint = 0;
  let pendingPaint = null;
  let editorTextNode = editor.firstChild;

  function paintHighlight(start, end) {{
    const now = performance.now();
    if (now - lastPaint < 120) {{
      if (!pendingPaint) {{
        pendingPaint = requestAnimationFrame(() => {{
          pendingPaint = null;
          doPaint(start, end);
        }});
      }}
      return;
    }}
    doPaint(start, end);
  }}

  function doPaint(start, end) {{
    lastPaint = performance.now();
    
    if (!editorTextNode || editorTextNode.nodeType !== Node.TEXT_NODE) return;
    const safeStart = Math.max(0, Math.min(start, fullText.length));
    const safeEnd = Math.max(safeStart, Math.min(end, fullText.length));
    const range = new Range();
    range.setStart(editorTextNode, safeStart);
    range.setEnd(editorTextNode, safeEnd);

    if (window.CSS?.highlights && window.Highlight) {{
      CSS.highlights.set('current-word', new Highlight(range));
    }}

    const rect = range.getBoundingClientRect();
    const parentRect = editor.getBoundingClientRect();
    const relativeTop = rect.top - parentRect.top + editor.scrollTop;
    const relativeBottom = relativeTop + rect.height;
    if (
      relativeTop < editor.scrollTop + 40 ||
      relativeBottom > editor.scrollTop + editor.clientHeight - 40
    ) {{
      const target = relativeTop - (editor.clientHeight / 2) + (rect.height / 2);
      editor.scrollTo({{ top: Math.max(target, 0), behavior: 'smooth' }});
    }}
  }}

  // ====== TTS State ======
  let currentOffset = 0;
  let paused = false;
  let speaking = false;
  let lastStartOffset = 0;
  let speechGeneration = 0;

  let lastBoundaryTime = 0;
  let lastBoundaryAbsOffset = 0;
  let heartbeatTimer = null;

  let avgCps = 0;
  const EMA_ALPHA = 0.2;

  function startHeartbeat(offsetBase) {{
    stopHeartbeat();
    lastBoundaryTime = performance.now();
    let lastTick = lastBoundaryTime;
    heartbeatTimer = setInterval(() => {{
      if (!speaking) return;

      const now = performance.now();
      const dt = (now - lastTick) / 1000.0;
      lastTick = now;

      const sinceBoundary = now - lastBoundaryTime;
      if (sinceBoundary > 400) {{
        const targetCps = avgCps > 0 ? avgCps : (BASE_CPS * (parseFloat(rateInp.value) || 1.0));
        const deltaChars = Math.max(1, Math.floor(targetCps * dt));
        const nextPos = Math.min((currentOffset || offsetBase) + deltaChars, fullText.length - 1);
        currentOffset = nextPos;
        const s = wordStartFrom(currentOffset);
        const e = wordEndFrom(currentOffset);
        paintHighlight(s, Math.max(e, s + 1));
      }}
    }}, 180);
  }}

  function stopHeartbeat() {{
    if (heartbeatTimer) {{
      clearInterval(heartbeatTimer);
      heartbeatTimer = null;
    }}
  }}

  function pickVoice() {{
    const name = voiceSel.value;
    return (voices||[]).find(v => v.name===name) || null;
  }}

  const MAX_UTTERANCE_CHARS = 1200;
  const MIN_UTTERANCE_CHARS = 300;

  function skipWhitespace(offset) {{
    let next = offset;
    while (next < fullText.length && /\\s/.test(fullText[next])) next++;
    return next;
  }}

  function findChunkEnd(offset) {{
    const hardEnd = Math.min(offset + MAX_UTTERANCE_CHARS, fullText.length);
    if (hardEnd >= fullText.length) return fullText.length;

    const searchStart = Math.min(offset + MIN_UTTERANCE_CHARS, hardEnd);
    const candidate = fullText.slice(searchStart, hardEnd);
    let sentenceEnd = -1;
    const sentencePattern = /[.!?…][\"”']?\\s/g;
    for (const match of candidate.matchAll(sentencePattern)) {{
      sentenceEnd = match.index + match[0].length;
    }}
    if (sentenceEnd >= 0) return searchStart + sentenceEnd;

    const whitespaceEnd = candidate.lastIndexOf(' ');
    return whitespaceEnd >= 0 ? searchStart + whitespaceEnd + 1 : hardEnd;
  }}

  function speakFrom(offset) {{
    const token = ++speechGeneration;
    window.speechSynthesis.cancel();
    stopHeartbeat();
    offset = skipWhitespace(Math.max(0, offset || 0));
    if (!fullText || offset >= fullText.length) {{
      speaking = false;
      return;
    }}
    currentOffset = offset;
    lastStartOffset = offset;
    setTimeout(() => speakChunk(offset, token), 30);
  }}

  function speakChunk(offset, token) {{
    if (token !== speechGeneration || offset >= fullText.length) return;

    const chunkEnd = findChunkEnd(offset);
    const chunk = fullText.slice(offset, chunkEnd);
    const u = new SpeechSynthesisUtterance(chunk);
    const v = pickVoice();
    if (v) u.voice = v;
    u.lang = (v && v.lang) ? v.lang : "vi-VN";
    u.rate = parseFloat(rateInp.value);
    u.pitch= parseFloat(pitchInp.value);

    u.onstart = () => {{
      if (token !== speechGeneration) return;
      statusEl.textContent = "Đang đọc…";
      statusEl.classList.add('reading');
      btnPlay.classList.add('playing');
      btnResume.style.display = "none";
      paused = false; speaking = true;
      lastStartOffset = offset;

      const s = wordStartFrom(offset);
      const e = wordEndFrom(offset);
      paintHighlight(s, Math.max(e, s+1));

      avgCps = BASE_CPS * (parseFloat(rateInp.value) || 1.0);
      lastBoundaryAbsOffset = offset;
      lastBoundaryTime = performance.now();

      startHeartbeat(offset);
    }};
    u.onend = () => {{
      if (token !== speechGeneration) return;
      stopHeartbeat();
      const nextOffset = skipWhitespace(chunkEnd);
      currentOffset = nextOffset;
      if (nextOffset < fullText.length && speaking) {{
        setTimeout(() => speakChunk(nextOffset, token), 20);
        return;
      }}
      statusEl.textContent = "Hoàn thành";
      statusEl.classList.remove('reading');
      btnPlay.classList.remove('playing');
      btnResume.style.display = "none";
      speaking = false;
    }};
    u.onerror = (event) => {{
      if (token !== speechGeneration) return;
      if (event.error === 'interrupted' || event.error === 'canceled') return;
      statusEl.textContent = "Lỗi khi đọc";
      statusEl.classList.remove('reading');
      btnPlay.classList.remove('playing');
      speaking = false;
      stopHeartbeat();
    }};
    u.onboundary = (e) => {{
      if (token === speechGeneration && typeof e.charIndex === "number") {{
        const now = performance.now();
        const absPos = offset + e.charIndex;

        const dt = (now - lastBoundaryTime) / 1000.0;
        const dchars = Math.max(0, absPos - lastBoundaryAbsOffset);
        if (dt > 0.03 && dchars > 0) {{
          const instCps = dchars / dt;
          avgCps = avgCps === 0 ? instCps : (1 - EMA_ALPHA) * avgCps + EMA_ALPHA * instCps;
        }}

        lastBoundaryTime = now;
        lastBoundaryAbsOffset = absPos;

        currentOffset = absPos;
        const s2 = wordStartFrom(currentOffset);
        const e2 = wordEndFrom(currentOffset);
        paintHighlight(s2, Math.max(e2, s2+1));
      }}
    }};
    window.speechSynthesis.speak(u);
  }}

  // ====== Settings Persistence ======
  function clamp(val, min, max) {{
    return Math.min(max, Math.max(min, val));
  }}

  function sanitize(val, min, max, step) {{
    let v = parseFloat(val);
    if (Number.isNaN(v)) v = 1.0;
    v = clamp(v, min, max);
    if (step > 0) v = Math.round(v / step) * step;
    return v;
  }}

  function loadSavedSettings() {{
    try {{
      const raw = localStorage.getItem(STORE_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    }} catch (e) {{
      return null;
    }}
  }}

  function saveSettings(rate, pitch) {{
    try {{
      localStorage.setItem(STORE_KEY, JSON.stringify({{ rate, pitch }}));
    }} catch (e) {{}}
  }}

  function applySavedSettings() {{
    const minRate = parseFloat(rateInp.min) || {MIN_RATE};
    const maxRate = parseFloat(rateInp.max) || {MAX_RATE};
    const stepRate = parseFloat(rateInp.step) || RATE_STEP;
    const minPitch = parseFloat(pitchInp.min) || {MIN_PITCH};
    const maxPitch = parseFloat(pitchInp.max) || {MAX_PITCH};
    const stepPitch = parseFloat(pitchInp.step) || {PITCH_STEP};

    const saved = loadSavedSettings();
    if (saved) {{
      if (saved.rate != null) {{
        rateInp.value = sanitize(saved.rate, minRate, maxRate, stepRate).toFixed(2);
      }}
      if (saved.pitch != null) {{
        pitchInp.value = sanitize(saved.pitch, minPitch, maxPitch, stepPitch).toFixed(1);
      }}
    }}
  }}

  applySavedSettings();

  // ====== Controls ======
  function updateRateDisplay() {{
    rateVal.textContent = parseFloat(rateInp.value).toFixed(2);
  }}

  function adjustRate(delta) {{
    const min = parseFloat(rateInp.min) || 0.1;
    const max = parseFloat(rateInp.max) || 3.0;
    const step = parseFloat(rateInp.step) || RATE_STEP;
    let v = parseFloat(rateInp.value) || 1.0;
    v = v + delta;
    v = Math.max(min, Math.min(max, v));
    v = Math.round(v / step) * step;
    rateInp.value = v.toFixed(2);
    updateRateDisplay();
    saveSettings(parseFloat(rateInp.value), parseFloat(pitchInp.value));
    retuneAndResume();
  }}

  function retuneAndResume() {{
    const newRate = parseFloat(rateInp.value) || 1.0;
    avgCps = BASE_CPS * newRate;
    saveSettings(newRate, parseFloat(pitchInp.value));
    if (speaking) {{
      const resumeAt = currentOffset || lastStartOffset || 0;
      window.speechSynthesis.cancel();
      setTimeout(() => speakFrom(resumeAt), 40);
    }}
  }}

  rateInp.addEventListener('input', () => {{
    rateVal.textContent = parseFloat(rateInp.value).toFixed(2);
    retuneAndResume();
  }});
  rateInp.addEventListener('change', () => {{
    rateVal.textContent = parseFloat(rateInp.value).toFixed(2);
    retuneAndResume();
  }});
  pitchInp.addEventListener('input', () => {{
    pitchVal.textContent = parseFloat(pitchInp.value).toFixed(1);
    saveSettings(parseFloat(rateInp.value), parseFloat(pitchInp.value));
    retuneAndResume();
  }});
  pitchInp.addEventListener('change', () => {{
    pitchVal.textContent = parseFloat(pitchInp.value).toFixed(1);
    saveSettings(parseFloat(rateInp.value), parseFloat(pitchInp.value));
    retuneAndResume();
  }});
  rateMinus.addEventListener('click', () => adjustRate(-RATE_STEP));
  ratePlus.addEventListener('click', () => adjustRate(RATE_STEP));
  updateRateDisplay();
  pitchVal.textContent = parseFloat(pitchInp.value).toFixed(1);

  btnPlay.onclick = () => {{
    unlockTTSIfNeeded();
    let start = 0;
    const sel = window.getSelection();
    if (sel && sel.rangeCount>0 && editor.contains(sel.getRangeAt(0).startContainer)) {{
      const r = sel.getRangeAt(0).cloneRange();
      const pre = r.cloneRange(); pre.selectNodeContents(editor); pre.setEnd(r.startContainer, r.startOffset);
      start = pre.toString().length;
    }}
    speakFrom(start);
  }};

  btnStop.onclick = () => {{
    if (window.speechSynthesis.speaking) {{
      speechGeneration++;
      window.speechSynthesis.cancel();
      paused = true; speaking = false;
      btnPlay.classList.remove('playing');
      btnResume.style.display = "inline-flex";
      statusEl.textContent = "Đã tạm dừng";
      statusEl.classList.remove('reading');
      stopHeartbeat();
    }}
  }};

  btnResume.onclick = () => {{
    if (paused) {{
      btnResume.style.display = "none";
      speakFrom(currentOffset || lastStartOffset || 0);
    }}
  }};

  // ====== Hotkeys ======
  function clickParentButton(text) {{
    try {{
      const doc = window.parent?.document;
      if (!doc) return false;
      const btns = Array.from(doc.querySelectorAll('button'));
      const target = btns.find(b => ((b.innerText || b.textContent || "")).includes(text));
      if (target) {{
        target.click();
        return true;
      }}
    }} catch (err) {{}}
    return false;
  }}

  function toggleStopOrResume() {{
    const resumeVisible = window.getComputedStyle(btnResume).display !== 'none';
    if (resumeVisible) {{
      btnResume.click();
      return;
    }}
    if (window.speechSynthesis.speaking) {{
      btnStop.click();
    }} else if (paused) {{
      btnResume.click();
    }} else {{
      speakFrom(0);
    }}
  }}

  function postNav(action) {{
    const label = action === "prev" ? "Chương trước" : "Chương sau";
    const clicked = clickParentButton(label);
    if (clicked) return;

    window.parent?.postMessage({{
      source: "doc-reader-component",
      action
    }}, "*");
  }}

  function handleHotkey(e) {{
    if (!["F7", "F8", "F9"].includes(e.key)) return;
    e.preventDefault();
    if (e.key === "F8") {{
      toggleStopOrResume();
    }} else if (e.key === "F7") {{
      postNav("prev");
    }} else if (e.key === "F9") {{
      postNav("next");
    }}
  }}

  window.addEventListener("keydown", handleHotkey, true);
  try {{
    const p = window.parent;
    if (p) {{
      if (p.__docReaderHotkeyHandler) {{
        p.removeEventListener("keydown", p.__docReaderHotkeyHandler, true);
      }}
      p.__docReaderHotkeyHandler = handleHotkey;
      p.addEventListener("keydown", handleHotkey, true);
    }}
  }} catch (err) {{}}

  window.addEventListener("message", (e) => {{
    const data = e.data || {{}};
    if (data.source === "doc-reader-main" && data.target === "tts-component") {{
      if (data.action === "toggle") toggleStopOrResume();
    }}
  }});

  window.addEventListener('pagehide', () => {{
    speechGeneration++;
    speaking = false;
    stopHeartbeat();
    window.speechSynthesis.cancel();
    window.speechSynthesis.removeEventListener('voiceschanged', loadVoices);
    if (window.CSS?.highlights) CSS.highlights.delete('current-word');
    try {{
      const p = window.parent;
      if (p?.__docReaderHotkeyHandler === handleHotkey) {{
        p.removeEventListener("keydown", handleHotkey, true);
        delete p.__docReaderHotkeyHandler;
      }}
    }} catch (err) {{}}
  }}, {{ once: true }});
}})();
</script>
"""


def render_tts_player(
    full_text: str,
    auto_play: bool = False,
    height: int = 720,
    is_dark: bool = True,
) -> None:
    """Render the TTS player component."""
    text_b64 = base64.b64encode((full_text or "").encode("utf-8")).decode("ascii")
    html_content = get_tts_html(text_b64, auto_play, is_dark=is_dark)
    st.iframe(html_content, height=height)
