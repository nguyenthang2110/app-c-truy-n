import base64
import re
import requests
from bs4 import BeautifulSoup
from readability import Document
import streamlit as st

APP_TITLE = "📖 Đọc truyện • Chuyển chương (trước/tiếp) • Tô đậm & Auto-scroll • không tạo file"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15"}

# ===================== Helpers =====================
def fetch_html(url: str, timeout=25) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or r.encoding
    return r.text

def clean_text(text: str) -> str:
    text = re.sub(r"\u00A0", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([\.!?…])( )", r"\1\n", text)  # ngắt câu nhẹ cho dễ nghe
    return text.strip()

def extract_text_from_html(html_src: str) -> str:
    doc = Document(html_src)
    summary_html = doc.summary(html_partial=True)
    soup = BeautifulSoup(summary_html, "lxml")
    parts = [p.get_text(" ", strip=True) for p in soup.find_all(["p", "h2", "h3", "blockquote"])]
    return clean_text("\n".join([t for t in parts if t]))

def get_chapter_number_from_url(url: str) -> str | None:
    m = re.search(r"chuong[-_ ]?(\d+)", url, re.IGNORECASE)
    return m.group(1) if m else None

def change_chapter_url(url: str, step: int = 1) -> str | None:
    """Thay đổi số chương trong URL theo step (+1/-1), giữ padding (001->002)."""
    m = re.match(r"^(.*?)(\?.*|#.*)?$", url)
    if not m:
        return None
    base = m.group(1)
    suffix = m.group(2) or ""
    m2 = re.search(r"(\d+)(?!.*\d)", base)
    if not m2:
        return None
    start, end = m2.span()
    num_str = m2.group(1)
    width = len(num_str)
    num = int(num_str) + step
    if num < 1:
        num = 1
    new_num = f"{num:0{width}d}"
    return base[:start] + new_num + base[end:] + suffix

def load_content(url: str) -> tuple[str, str]:
    """Trả về (full_text, error_msg)."""
    try:
        html_src = fetch_html(url)
        txt = extract_text_from_html(html_src)
        return (txt if txt else "(Không trích xuất được nội dung)", "")
    except Exception as e:
        return ("", f"Lỗi khi tải {url}: {e}")

def load_next_n_chapters(base_url: str, count: int) -> tuple[str, str, str]:
    """Tải N chương kế tiếp; trả về (final_url, text_gộp, error)."""
    texts = []
    url = base_url
    last_ok_url = None
    for _ in range(count):
        url = change_chapter_url(url, step=1)
        if not url:
            return (base_url, "", "Không tìm thấy số chương trong URL để tăng.")
        txt, err = load_content(url)
        if err:
            texts.append(f"(Lỗi khi tải {url}: {err})")
        else:
            texts.append(txt)
            last_ok_url = url
    final_url = last_ok_url or url
    return (final_url, ("\n\n".join(texts).strip()), "")

# ===================== App =====================
st.set_page_config(page_title=APP_TITLE, page_icon="📖", layout="wide")
st.title(APP_TITLE)

# ---------- State mặc định ----------
st.session_state.setdefault("current_url", "")
st.session_state.setdefault("chapter_number", "")
st.session_state.setdefault("full_text", "")
st.session_state.setdefault("error", "")
st.session_state.setdefault("current_url_input", st.session_state["current_url"])
st.session_state.setdefault("auto_play", False)  # để JS tự đọc sau khi nạp

# ---------- XỬ LÝ HÀNH ĐỘNG PENDING (TRƯỚC KHI TẠO WIDGET) ----------
if st.session_state.get("pending_action"):
    action = st.session_state.pop("pending_action")
    if action == "load":
        base_url = (st.session_state.get("current_url_input", "") or "").strip()
        if base_url:
            text, err = load_content(base_url)
            st.session_state["current_url"] = base_url
            st.session_state["chapter_number"] = get_chapter_number_from_url(base_url) or ""
            st.session_state["full_text"] = text
            st.session_state["error"] = err
            st.session_state["current_url_input"] = st.session_state["current_url"]
            st.session_state["auto_play"] = False
    elif isinstance(action, dict) and action.get("type") in ("prev", "next"):
        base_url = (st.session_state.get("current_url_input", "") or st.session_state.get("current_url", "") or "").strip()
        if not base_url:
            st.session_state["error"] = "Hãy nhập URL chương đầu tiên trước."
        else:
            if action["type"] == "prev":
                new_url = change_chapter_url(base_url, step=-1)
                if not new_url:
                    st.session_state["error"] = "Không tìm thấy số chương trong URL để giảm."
                else:
                    text, err = load_content(new_url)
                    st.session_state["current_url"] = new_url
                    st.session_state["chapter_number"] = get_chapter_number_from_url(new_url) or ""
                    st.session_state["full_text"] = text
                    st.session_state["error"] = err
                    st.session_state["current_url_input"] = st.session_state["current_url"]
                    st.session_state["auto_play"] = True  # tự đọc chương vừa nạp
            else:  # next with count
                count = int(action.get("count", 1))
                final_url, big_text, err = load_next_n_chapters(base_url, count)
                if err:
                    st.session_state["error"] = err
                else:
                    st.session_state["current_url"] = final_url
                    st.session_state["chapter_number"] = get_chapter_number_from_url(final_url) or ""
                    st.session_state["full_text"] = big_text
                    st.session_state["error"] = ""
                    st.session_state["current_url_input"] = st.session_state["current_url"]
                    st.session_state["auto_play"] = True  # tự đọc luôn từ đầu

# ---------- UI: form điều khiển (tránh rerun khi đang gõ) ----------
with st.form("controls", clear_on_submit=False):
    st.text_input(
        "🔗 URL chương hiện tại",
        key="current_url_input",
        placeholder="https://truyenhoan.com/linh-vu-thien-ha/chuong-144.html",
    )
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    with c1:
        next_count = st.number_input("Số chương đọc tiếp", min_value=1, max_value=10, value=1, step=1, key="next_count_input")
    with c2:
        load_submit = st.form_submit_button("📥 Tải / Làm mới", use_container_width=True)
    with c3:
        prev_submit = st.form_submit_button("⏮️ Chương trước", use_container_width=True)
    with c4:
        next_submit = st.form_submit_button("⏭️ Chương tiếp", use_container_width=True)

# Xử lý submit (chỉ chạy khi bấm nút, không rerun khi gõ)
if load_submit:
    st.session_state["pending_action"] = "load"
    st.rerun()

if prev_submit:
    st.session_state["pending_action"] = {"type": "prev"}
    st.rerun()

if next_submit:
    st.session_state["pending_action"] = {"type": "next", "count": int(st.session_state.get("next_count_input", 1))}
    st.rerun()

# Hàng hiển thị số chương (readonly)
st.text_input("Số chương hiện tại", value=st.session_state.get("chapter_number", ""), disabled=True)

# ---------- Hiển thị lỗi ----------
if st.session_state.get("error"):
    st.error(st.session_state["error"])

# ---------- Văn bản hiện tại ----------
full_text = st.session_state.get("full_text", "")
text_b64 = base64.b64encode((full_text or "").encode("utf-8")).decode("ascii")
auto_play_js = "true" if st.session_state.get("auto_play", False) else "false"

# ===================== Web Speech API + Highlight/Scroll + CPS Heartbeat =====================
st.components.v1.html(f"""
<style>
  .toolbar button {{
    padding:8px 14px; border-radius:10px; border:1px solid #ccc; background:#fff; cursor:pointer; margin-right:8px;
  }}
  .toolbar select, .toolbar input[type=range] {{
    margin-right:8px;
  }}
  .label {{ font-size:12px; opacity:.75; margin-right:4px; }}
  #editor {{
    white-space:pre-wrap; border:1px solid #ddd; border-radius:10px; padding:14px;
    height:460px; overflow:auto; line-height:1.7;
    font-family: system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans",Helvetica,Arial,"Apple Color Emoji","Segoe UI Emoji";
    font-size:16px;
    background:#fff;
  }}
  .hl {{
    background:#fff3cd;
    font-weight:700;
    border-radius:4px;
  }}
</style>

<div class="toolbar" style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px">
  <button id="btnPlay">▶️ Đọc</button>
  <button id="btnStop">⏹️ Dừng</button>
  <button id="btnResume" style="display:none">⏯️ Tiếp tục</button>

  <span class="label">Giọng:</span>
  <select id="voiceSel" title="Chọn giọng (ưu tiên nữ tiếng Việt)"><option>Đang tải giọng…</option></select>

  <span class="label">Tốc độ</span>
  <button id="rateMinus" title="- tốc độ" aria-label="Giảm tốc độ">➖</button>
  <input id="rate" type="range" min="0.5" max="2.0" step="0.1" value="1.0">
  <button id="ratePlus" title="+ tốc độ" aria-label="Tăng tốc độ">➕</button>
  <span id="rateVal" class="label">1.00</span>

  <span class="label">Cao độ</span>
  <input id="pitch" type="range" min="0.0" max="2.0" step="0.1" value="1.0">
  <span id="pitchVal" class="label">1.0</span>

  <span id="status" style="opacity:.7;margin-left:auto">Sẵn sàng</span>
</div>

<div id="editor" contenteditable="true" spellcheck="false" lang="vi"></div>

<script>
(function() {{
  // ==== UTF-8 decode an toàn ====
  function b64ToUtf8(b64) {{
    const bin = window.atob("{text_b64}");
    const buf = new Uint8Array(bin.length);
    for (let i=0;i<bin.length;i++) buf[i] = bin.charCodeAt(i);
    return new TextDecoder("utf-8").decode(buf);
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
  const RATE_STEP = 0.1;
  const MAX_CHUNK_LEN = 900;  // iOS Safari hay lỗi với đoạn TTS quá dài
  const MIN_CHUNK_LEN = 400;
  const STORE_KEY = "doc-reader-voice-settings";
  let fullText = fullTextOriginal;
  editor.textContent = fullTextOriginal || "(Chưa có nội dung)";

  // ====== Voice handling + Auto-play an toàn (đợi editor & voices & user-gesture) ======
  let voices = [];
  let autoPlay = {auto_play_js};
  let autoPlayedOnce = false;
  let ttsUnlocked = false;   // cần một tương tác người dùng để "mở khóa" TTS trong vài trình duyệt
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

  // Mở khóa TTS bằng một utterance trống sau tương tác người dùng đầu tiên
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

  // Lắng nghe tương tác đầu tiên của người dùng để unlock
  ["click","keydown","touchstart"].forEach(evt => {{
    window.addEventListener(evt, function once() {{
      window.removeEventListener(evt, once, true);
      unlockTTSIfNeeded();
    }}, true);
  }});

  function maybeAutoStart() {{
    if (!wantsAutoStart || autoPlayedOnce || !fullText) return;
    if (!ttsUnlocked) return;

    // tô đậm trước khi đọc
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
    autoPlayedOnce = true;
    wantsAutoStart = true;
    if (ttsUnlocked) maybeAutoStart();
    // nếu chưa unlock, sẽ tự chạy khi người dùng tương tác (unlockTTSIfNeeded -> maybeAutoStart)
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

    // thử auto-start
    autoStartIfNeeded();
    maybeAutoStart();
  }}
  window.speechSynthesis.onvoiceschanged = loadVoices;
  loadVoices();

  // gọi thêm một lần sau khi editor có text
  autoStartIfNeeded();
  maybeAutoStart();

  // ====== Utils ======
  function caretOffset(el) {{
    const sel = window.getSelection();
    if (!sel || sel.rangeCount===0) return 0;
    const rng = sel.getRangeAt(0).cloneRange();
    const pre = rng.cloneRange();
    pre.selectNodeContents(el); pre.setEnd(rng.endContainer, rng.endOffset);
    return pre.toString().length;
  }}

  function esc(s) {{
    return s.replace(/[&<>]/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}}[ch]));
  }}

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

  // ====== Highlight + Auto-scroll (throttle) ======
  let lastPaint = 0;
  function paintHighlight(start, end) {{
    const now = performance.now();
    if (now - lastPaint < 100) return;  // throttle 100ms
    lastPaint = now;

    const before = esc(fullText.slice(0, start));
    const mid    = esc(fullText.slice(start, end));
    const after  = esc(fullText.slice(end));
    editor.innerHTML = before + '<span class="hl" id="hl">'+ (mid || '&nbsp;') + '</span>' + after;

    const el = document.getElementById('hl');
    if (el) {{
      const parent = editor;
      const elTop = el.offsetTop;
      const elBottom = elTop + el.offsetHeight;
      const viewTop = parent.scrollTop;
      const viewBottom = viewTop + parent.clientHeight;

      if (elTop < viewTop + 40 || elBottom > viewBottom - 40) {{
        const target = elTop - (parent.clientHeight/2) + (el.offsetHeight/2);
        parent.scrollTo({{ top: Math.max(target, 0), behavior: 'auto' }});
      }}
    }}
  }}

  // ====== TTS state + CPS Heartbeat (theo thời gian thực) ======
  let currentOffset = 0;
  let paused = false;
  let speaking = false;
  let lastStartOffset = 0;

  let lastBoundaryTime = 0;
  let lastBoundaryAbsOffset = 0;  // vị trí tuyệt đối boundary trước
  let heartbeatTimer = null;

  const BASE_CPS = 14.0;          // ước lượng ký tự/giây ở rate=1.0 (tiếng Việt)
  let avgCps = 0;                 // sẽ tự hiệu chỉnh từ onboundary

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
      if (sinceBoundary > 500) {{
        const targetCps = avgCps > 0 ? avgCps : (BASE_CPS * (parseFloat(rateInp.value) || 1.0));
        const deltaChars = Math.max(1, Math.floor(targetCps * dt));
        const nextPos = Math.min((currentOffset || offsetBase) + deltaChars, fullText.length - 1);
        currentOffset = nextPos;
        const s = wordStartFrom(currentOffset);
        const e = wordEndFrom(currentOffset);
        paintHighlight(s, Math.max(e, s + 1));
      }}
    }}, 80);
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

  function speakFrom(offset, preferredLen) {{
    window.speechSynthesis.cancel();
    if (!fullText || offset >= fullText.length) return;

    const chunkOffset = offset;
    const limit = preferredLen || MAX_CHUNK_LEN;
    const chunkLen = Math.max(MIN_CHUNK_LEN, Math.min(limit, MAX_CHUNK_LEN, fullText.length - chunkOffset));
    const chunkEnd = Math.min(fullText.length, chunkOffset + chunkLen);
    const chunk = fullText.substring(chunkOffset, chunkEnd);
    if (!chunk) return;

    const u = new SpeechSynthesisUtterance(chunk);
    const v = pickVoice();
    if (v) u.voice = v;
    u.lang = (v && v.lang) ? v.lang : "vi-VN";
    u.rate = parseFloat(rateInp.value);
    u.pitch= parseFloat(pitchInp.value);

    u.onstart = () => {{
      statusEl.textContent = "Đang đọc…";
      btnResume.style.display = "none";
      paused = false; speaking = true;
      lastStartOffset = chunkOffset;

      const s = wordStartFrom(chunkOffset);
      const e = wordEndFrom(chunkOffset);
      paintHighlight(s, Math.max(e, s+1));

      avgCps = BASE_CPS * (parseFloat(rateInp.value) || 1.0);
      lastBoundaryAbsOffset = chunkOffset;
      lastBoundaryTime = performance.now();

      startHeartbeat(chunkOffset);
    }};
    u.onend = () => {{
      speaking = false;
      stopHeartbeat();
      if (paused) {{
        statusEl.textContent = "Đã dừng – có thể tiếp tục";
        btnResume.style.display = "inline-block";
        return;
      }}
      if (chunkEnd < fullText.length) {{
        speakFrom(chunkEnd);
        return;
      }}
      statusEl.textContent = "Đã kết thúc / đã dừng";
      btnResume.style.display = "none";
    }};
    u.onerror = () => {{
      speaking = false;
      stopHeartbeat();
      const nextLen = Math.max(MIN_CHUNK_LEN, Math.floor(chunkLen / 2));
      if (nextLen < chunkLen) {{
        statusEl.textContent = "Lỗi khi đọc – đang rút gọn đoạn…";
        setTimeout(() => speakFrom(chunkOffset, nextLen), 60);
        return;
      }}
      statusEl.textContent = "Lỗi khi đọc (thử reload hoặc rút ngắn văn bản)";
      btnResume.style.display = "inline-block";
    }};
    u.onboundary = (e) => {{
      if (typeof e.charIndex === "number") {{
        const now = performance.now();
        const absPos = chunkOffset + e.charIndex;

        const dt = (now - lastBoundaryTime) / 1000.0;
        const dchars = Math.max(0, absPos - lastBoundaryAbsOffset);
        if (dt > 0.03 && dchars > 0) {{
          const instCps = dchars / dt;
          const alpha = 0.25;
          avgCps = (1 - alpha) * avgCps + alpha * instCps;
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

  // ====== Persisted settings (rate/pitch) ======
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
      const obj = JSON.parse(raw);
      return obj;
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
    const minRate = parseFloat(rateInp.min) || 0.5;
    const maxRate = parseFloat(rateInp.max) || 2.0;
    const stepRate = parseFloat(rateInp.step) || RATE_STEP;
    const minPitch = parseFloat(pitchInp.min) || 0.0;
    const maxPitch = parseFloat(pitchInp.max) || 2.0;
    const stepPitch = parseFloat(pitchInp.step) || 0.1;

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
    // snap to step
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
      setTimeout(() => speakFrom(resumeAt), 40); // delay nhỏ để Safari/Mac nhận rate mới
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
      // ước lượng offset đơn giản theo text trước con trỏ
      const r = sel.getRangeAt(0).cloneRange();
      const pre = r.cloneRange(); pre.selectNodeContents(editor); pre.setEnd(r.startContainer, r.startOffset);
      start = pre.toString().length;
    }}
    speakFrom(start);
  }};

  btnStop.onclick = () => {{
    if (window.speechSynthesis.speaking) {{
      window.speechSynthesis.cancel();
      paused = true; speaking = false;
      btnResume.style.display = "inline-block";
      statusEl.textContent = "Đã dừng – có thể tiếp tục";
      stopHeartbeat();
    }}
  }};

  btnResume.onclick = () => {{
    if (paused) {{
      btnResume.style.display = "none";
      speakFrom(currentOffset || lastStartOffset || 0);
    }}
  }};

  // ====== Hotkeys (F7/F8/F9) ======
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
      // nếu chưa đọc, bắt đầu đọc từ đầu
      speakFrom(0);
    }}
  }}

  function postNav(action) {{
    // thử click trực tiếp nút Streamlit ở parent
    const label = action === "prev" ? "Chương trước" : "Chương tiếp";
    const clicked = clickParentButton(label);
    if (clicked) return;

    // fallback: gửi message để parent xử lý nếu có listener
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

  // lắng nghe cả trong iframe và ở parent để phím tắt hoạt động khi focus ở ngoài
  window.addEventListener("keydown", handleHotkey, true);
  try {{
    const p = window.parent;
    if (p && !p.__docReaderHotkeysBound) {{
      p.addEventListener("keydown", handleHotkey, true);
      p.__docReaderHotkeysBound = true;
    }}
  }} catch (err) {{}}

  window.addEventListener("message", (e) => {{
    const data = e.data || {{}};
    if (data.source === "doc-reader-main" && data.target === "tts-component") {{
      if (data.action === "toggle") toggleStopOrResume();
    }}
  }});
}})();
</script>
""", height=700, scrolling=True)
