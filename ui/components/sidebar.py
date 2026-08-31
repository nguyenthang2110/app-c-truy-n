"""Sidebar navigation and library controls."""

import streamlit as st

from data.bookmarks import bookmark_manager
from data.favorites import favorites_manager
from data.history import history_manager
from ui.themes import theme_manager


def _display_title(value: str | None) -> str:
    return (value or "Không rõ").strip()[:32]


def render_sidebar() -> dict:
    """Render the sidebar and return the selected library action."""
    actions = {"selected_url": None, "action": None}

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-mark">Đ</div>
                <div>
                    <strong>Đọc truyện</strong>
                    <small>Thư viện cá nhân</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        current_theme = theme_manager.get_theme()
        is_dark = current_theme == "dark"
        theme_action = "Đổi sang giao diện sáng" if is_dark else "Đổi sang giao diện tối"
        if st.button(
            theme_action,
            key="theme_mode_button",
            help="Chuyển nhanh giữa giao diện sáng và tối",
            use_container_width=True,
        ):
            theme_manager.set_theme("light" if is_dark else "dark")
            st.rerun()

        st.divider()

        bookmarks = bookmark_manager.get_all()
        history = history_manager.get_all()
        favorites = favorites_manager.get_all()
        st.markdown(
            f"""
            <div class="sidebar-section-label">Tổng quan</div>
            <div class="sidebar-stats">
                <div class="sidebar-stat"><b>{len(bookmarks)}</b><span>Đã lưu</span></div>
                <div class="sidebar-stat"><b>{len(history)}</b><span>Đã đọc</span></div>
                <div class="sidebar-stat"><b>{len(favorites)}</b><span>Yêu thích</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown('<div class="sidebar-section-label">Thư viện</div>', unsafe_allow_html=True)
        tab_saved, tab_recent, tab_favorite = st.tabs(["Đã lưu", "Gần đây", "Yêu thích"])

        with tab_saved:
            if bookmarks:
                for bookmark in bookmarks[:10]:
                    title = _display_title(bookmark.get("title"))
                    chapter = bookmark.get("chapter") or "—"
                    url = bookmark.get("url") or ""
                    if st.button(
                        f"{title} · Chương {chapter}",
                        key=f"bm_{bookmark.get('id')}",
                        use_container_width=True,
                    ):
                        actions["selected_url"] = url
                        actions["action"] = "load_bookmark"
            else:
                st.info("Chưa có chương nào được lưu.")

        with tab_recent:
            recent_history = history[:10]
            if recent_history:
                for index, item in enumerate(recent_history):
                    title = _display_title(item.get("title"))
                    chapter = item.get("chapter") or "—"
                    url = item.get("url") or ""
                    if st.button(
                        f"{title} · Chương {chapter}",
                        key=f"hist_{index}",
                        use_container_width=True,
                    ):
                        actions["selected_url"] = url
                        actions["action"] = "load_history"
            else:
                st.info("Lịch sử đọc đang trống.")

        with tab_favorite:
            if favorites:
                for index, favorite in enumerate(favorites):
                    title = _display_title(favorite.get("title"))
                    url = favorite.get("url") or ""
                    open_col, remove_col = st.columns([5, 1])
                    with open_col:
                        if st.button(
                            title,
                            key=f"fav_{index}",
                            use_container_width=True,
                        ):
                            actions["selected_url"] = url
                            actions["action"] = "load_favorite"
                    with remove_col:
                        if st.button("×", key=f"fav_del_{index}", help="Xóa khỏi yêu thích"):
                            favorites_manager.remove(url)
                            st.rerun()
            else:
                st.info("Chưa có truyện yêu thích.")

        st.divider()
        with st.expander("Quản lý dữ liệu", expanded=False):
            clear_history, clear_bookmarks = st.columns(2)
            with clear_history:
                if st.button("Xóa lịch sử", use_container_width=True):
                    history_manager.clear_all()
                    st.toast("Đã xóa lịch sử.")
                    st.rerun()
            with clear_bookmarks:
                if st.button("Xóa đã lưu", use_container_width=True):
                    bookmark_manager.clear_all()
                    st.toast("Đã xóa danh sách đã lưu.")
                    st.rerun()

        st.markdown(
            """
            <div class="sidebar-footer">
                F7 chương trước · F8 phát/dừng · F9 chương sau
            </div>
            """,
            unsafe_allow_html=True,
        )

    return actions
