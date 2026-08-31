# 📖 Story Reader - Modern Reading App
# Main application entry point

import streamlit as st

# Add project root to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.logging_config import configure_logging

configure_logging()

from config.settings import APP_TITLE, APP_ICON, LAYOUT
from core.chapter import (
    get_chapter_number_from_url, change_chapter_url, load_content,
    load_next_n_chapters, preload_next_chapters, get_preloaded_content,
    remove_preloaded_content
)
from data.bookmarks import bookmark_manager
from data.history import history_manager
from data.favorites import favorites_manager
from ui.styles import get_custom_css, get_theme_css
from ui.themes import theme_manager
from ui.components.sidebar import render_sidebar
from ui.components.tts_player import render_tts_player


# ===================== Page Configuration =====================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# ===================== Apply Custom Styling =====================
is_dark_theme = theme_manager.is_dark()
st.markdown(get_custom_css(), unsafe_allow_html=True)
st.markdown(get_theme_css(is_dark_theme), unsafe_allow_html=True)


# ===================== Initialize Session State =====================
def init_session_state():
    """Initialize session state with default values."""
    defaults = {
        "current_url": "",
        "chapter_number": "",
        "full_text": "",
        "error": "",
        "current_url_input": "",
        "auto_play": False,
        "pending_action": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# ===================== Action Handlers =====================
def handle_load_action(url: str, auto_play: bool = False) -> None:
    """Handle loading a chapter from URL."""
    if not url:
        st.session_state["error"] = "Vui lòng nhập URL chương truyện."
        return
    
    with st.spinner("🔄 Đang tải chương..."):
        text, err = load_content(url)
    
    st.session_state["current_url"] = url
    st.session_state["chapter_number"] = get_chapter_number_from_url(url) or ""
    st.session_state["full_text"] = text
    st.session_state["error"] = err
    st.session_state["current_url_input"] = url
    st.session_state["auto_play"] = auto_play
    
    if not err:
        # Save to history
        history_manager.add(
            url=url,
            chapter=st.session_state["chapter_number"],
            title=""
        )
        # Preload next chapters
        preload_next_chapters(url)


def handle_prev_chapter() -> None:
    """Handle navigating to previous chapter."""
    base_url = st.session_state.get("current_url", "").strip()
    if not base_url:
        st.session_state["error"] = "Hãy nhập URL chương đầu tiên trước."
        return
    
    new_url = change_chapter_url(base_url, step=-1)
    if not new_url:
        st.session_state["error"] = "Không tìm thấy số chương trong URL để giảm."
        return
    
    with st.spinner("⏮️ Đang tải chương trước..."):
        text, err = load_content(new_url)
    
    st.session_state["current_url"] = new_url
    st.session_state["chapter_number"] = get_chapter_number_from_url(new_url) or ""
    st.session_state["full_text"] = text
    st.session_state["error"] = err
    st.session_state["current_url_input"] = new_url
    st.session_state["auto_play"] = True
    
    if not err:
        history_manager.add(url=new_url, chapter=st.session_state["chapter_number"])
        preload_next_chapters(new_url)


def handle_next_chapters(count: int = 1) -> None:
    """Handle navigating to next chapter(s)."""
    base_url = st.session_state.get("current_url", "").strip()
    if not base_url:
        st.session_state["error"] = "Hãy nhập URL chương đầu tiên trước."
        return
    
    # Check preload cache for single chapter
    if count == 1:
        next_url = change_chapter_url(base_url, step=1)
        if next_url:
            cached_text = get_preloaded_content(next_url)
            if cached_text:
                # Use cached content - instant!
                st.session_state["current_url"] = next_url
                st.session_state["chapter_number"] = get_chapter_number_from_url(next_url) or ""
                st.session_state["full_text"] = cached_text
                st.session_state["error"] = ""
                st.session_state["current_url_input"] = next_url
                st.session_state["auto_play"] = True
                
                remove_preloaded_content(next_url)
                history_manager.add(url=next_url, chapter=st.session_state["chapter_number"])
                preload_next_chapters(next_url)
                return
    
    # Load normally (single or multiple chapters)
    with st.spinner(f"⏭️ Đang tải {count} chương tiếp theo..."):
        final_url, big_text, err = load_next_n_chapters(base_url, count)
    
    if err:
        st.session_state["error"] = err
    else:
        st.session_state["current_url"] = final_url
        st.session_state["chapter_number"] = get_chapter_number_from_url(final_url) or ""
        st.session_state["full_text"] = big_text
        st.session_state["error"] = ""
        st.session_state["current_url_input"] = final_url
        st.session_state["auto_play"] = True
        
        history_manager.add(url=final_url, chapter=st.session_state["chapter_number"])
        preload_next_chapters(final_url)


# ===================== Process Pending Actions =====================
if st.session_state.get("pending_action"):
    action = st.session_state.pop("pending_action")
    
    if action == "load":
        handle_load_action(st.session_state.get("current_url_input", "").strip())
    elif isinstance(action, dict):
        if action.get("type") == "prev":
            handle_prev_chapter()
        elif action.get("type") == "next":
            handle_next_chapters(action.get("count", 1))
        elif action.get("type") == "load_url":
            handle_load_action(action.get("url", ""), auto_play=True)


# ===================== Render Sidebar =====================
sidebar_actions = render_sidebar()

# Handle sidebar actions
if sidebar_actions.get("selected_url"):
    st.session_state["pending_action"] = {
        "type": "load_url",
        "url": sidebar_actions["selected_url"]
    }
    st.rerun()


# ===================== Main Content Area =====================
# Header
st.markdown(
    """
    <div class="reader-hero">
        <div class="reader-kicker">Trình đọc cá nhân</div>
        <h1>Đọc liền mạch.<br>Nghe thật tự nhiên.</h1>
        <p>Dán liên kết chương truyện để bắt đầu. Ứng dụng tự ghi nhớ tiến độ,
        tải trước chương kế tiếp và đọc thành tiếng ngay trong trình duyệt.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ===================== Control Form =====================
with st.form("controls", clear_on_submit=False):
    st.text_input(
        "Liên kết chương",
        key="current_url_input",
        placeholder="https://truyenhoan.com/.../chuong-144.html",
        help="Dán URL của chương truyện bạn muốn đọc",
    )

    load_col, bookmark_col = st.columns(2, vertical_alignment="bottom")
    with load_col:
        load_submit = st.form_submit_button(
            "Mở chương",
            type="primary",
            use_container_width=True,
        )
    with bookmark_col:
        current_url = st.session_state.get("current_url", "")
        is_bookmarked = bookmark_manager.is_bookmarked(current_url) if current_url else False
        bookmark_label = "Đã lưu chương" if is_bookmarked else "Lưu chương"
        bookmark_submit = st.form_submit_button(bookmark_label, use_container_width=True)

    prev_col, next_col, count_col = st.columns(
        [1, 1, 1],
        vertical_alignment="bottom",
    )

    with prev_col:
        prev_submit = st.form_submit_button("Chương trước", use_container_width=True)

    with next_col:
        next_submit = st.form_submit_button("Chương sau", use_container_width=True)

    with count_col:
        next_count = st.number_input(
            "Số chương đọc tiếp",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
            key="next_count_input",
        )

# Handle form submissions
if load_submit:
    st.session_state["pending_action"] = "load"
    st.rerun()

if prev_submit:
    st.session_state["pending_action"] = {"type": "prev"}
    st.rerun()

if next_submit:
    st.session_state["pending_action"] = {"type": "next", "count": int(st.session_state.get("next_count_input", 1))}
    st.rerun()

if bookmark_submit and st.session_state.get("current_url"):
    current_url = st.session_state["current_url"]
    chapter = st.session_state.get("chapter_number", "")
    if bookmark_manager.is_bookmarked(current_url):
        bookmark_manager.remove(current_url)
        st.toast("Đã xóa khỏi danh sách lưu.")
    else:
        bookmark_manager.add(current_url, "", chapter)
        st.toast("Đã lưu chương.")
    st.rerun()


# ===================== Info Row =====================
if st.session_state.get("current_url"):
    chapter_col, favorite_col, reading_col = st.columns(
        [2.4, 1.2, 1],
        vertical_alignment="center",
    )
    with chapter_col:
        chapter_number = st.session_state.get("chapter_number") or "Không rõ"
        st.markdown(
            f'<div class="chapter-context">Đang đọc · Chương {chapter_number}</div>',
            unsafe_allow_html=True,
        )

    with favorite_col:
        is_fav = favorites_manager.is_favorite(st.session_state["current_url"])
        fav_label = "Đã yêu thích" if is_fav else "Yêu thích"
        if st.button(fav_label, use_container_width=True):
            favorites_manager.toggle(st.session_state["current_url"])
            st.rerun()

    with reading_col:
        history_count = len(history_manager.get_all())
        st.caption(f"{history_count} truyện đã đọc")
else:
    st.markdown(
        '<div class="reader-empty-note">Chưa mở chương nào · F7/F8/F9 để điều khiển nhanh</div>',
        unsafe_allow_html=True,
    )


# ===================== Error Display =====================
if st.session_state.get("error"):
    st.error(st.session_state["error"])


# ===================== TTS Player =====================
full_text = st.session_state.get("full_text", "")
auto_play = st.session_state.get("auto_play", False)

render_tts_player(full_text, auto_play, is_dark=is_dark_theme)
# Auto-play is a one-shot navigation intent. Keeping it True would recreate a
# speaking iframe after unrelated reruns such as theme/bookmark changes.
if auto_play:
    st.session_state["auto_play"] = False


# ===================== Keyboard Shortcuts Info =====================
with st.expander("Phím tắt", expanded=False):
    st.markdown("""
    | Phím | Chức năng |
    |------|-----------|
    | **F7** | Chương trước |
    | **F8** | Phát / tạm dừng / tiếp tục |
    | **F9** | Chương sau |
    """)
