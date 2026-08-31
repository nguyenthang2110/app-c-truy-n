# Chapter navigation module

import logging
import re
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st

from config.settings import (
    MAX_CHAPTER_LOAD,
    PRELOAD_CACHE_SIZE,
    PRELOAD_LOOK_AHEAD,
    THREAD_POOL_SIZE,
)
from core.scraper import fetch_html, extract_text_from_html


logger = logging.getLogger(__name__)


# Pre-compiled regex patterns for better performance
CHAPTER_NUMBER_PATTERN = re.compile(r"chuong[-_ ]?(\d+)", re.IGNORECASE)
URL_PARTS_PATTERN = re.compile(r"^(.*?)(\?.*|#.*)?$")
LAST_NUMBER_PATTERN = re.compile(r"(\d+)(?!.*\d)")

# One bounded worker is shared across reruns. Creating a new executor for every
# click can accumulate network jobs and eventually make the Streamlit process
# unresponsive during long reading sessions.
_PRELOAD_CACHE: OrderedDict[str, str] = OrderedDict()
_PRELOAD_LOCK = threading.RLock()
_PRELOAD_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="chapter-preload")
_PRELOAD_FUTURE = None
_PRELOAD_GENERATION = 0


def get_chapter_number_from_url(url: str) -> str | None:
    """Extract chapter number from URL."""
    m = CHAPTER_NUMBER_PATTERN.search(url)
    return m.group(1) if m else None


def change_chapter_url(url: str, step: int = 1) -> str | None:
    """Change chapter number in URL by step (+1/-1), preserving padding (001->002)."""
    m = URL_PARTS_PATTERN.match(url)
    if not m:
        return None
    base = m.group(1)
    suffix = m.group(2) or ""
    m2 = LAST_NUMBER_PATTERN.search(base)
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
    """Load chapter content. Returns (full_text, error_msg)."""
    try:
        html_src = fetch_html(url)
        txt = extract_text_from_html(html_src)
        return (txt if txt else "(Không trích xuất được nội dung)", "")
    except ValueError as e:
        logger.warning("Yêu cầu tải chương bị từ chối (%s): %s", url, e)
        return ("", f"Lỗi khi tải {url}: {e}")
    except Exception as e:
        logger.exception("Không tải được chương %s", url)
        return ("", f"Lỗi khi tải {url}: {e}")


def load_next_n_chapters(base_url: str, count: int) -> tuple[str, str, str]:
    """
    Load N next chapters in parallel using multithreading.
    Returns (final_url, combined_text, error).
    """
    count = min(count, MAX_CHAPTER_LOAD)
    
    # Generate URLs to load
    urls_to_load = []
    url = base_url
    for i in range(count):
        url = change_chapter_url(url, step=1)
        if not url:
            if i == 0:
                return (base_url, "", "Không tìm thấy số chương trong URL để tăng.")
            break
        urls_to_load.append(url)
    
    if not urls_to_load:
        return (base_url, "", "Không có chương nào để tải.")
    
    # Parallel loading with ThreadPoolExecutor
    results = {}  # {url: (text, error)}
    progress_text = st.empty()
    progress_bar = st.progress(0.0)
    
    try:
        with ThreadPoolExecutor(max_workers=min(THREAD_POOL_SIZE, count)) as executor:
            future_to_url = {executor.submit(load_content, url): url for url in urls_to_load}
            
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    text, err = future.result()
                    results[url] = (text, err)
                except Exception as e:
                    logger.exception("Worker tải chương bị lỗi: %s", url)
                    results[url] = ("", f"Exception: {e}")
                
                completed += 1
                progress = completed / len(urls_to_load)
                progress_bar.progress(progress)
                progress_text.text(f"Đang tải... {completed}/{len(urls_to_load)} chương")
    finally:
        progress_text.empty()
        progress_bar.empty()
    
    # Combine results in order
    texts = []
    last_ok_url = None
    for url in urls_to_load:
        if url in results:
            txt, err = results[url]
            if err:
                texts.append(f"(Lỗi khi tải {url}: {err})")
            else:
                texts.append(txt)
                last_ok_url = url
    
    if last_ok_url is None:
        return (
            base_url,
            "",
            "Không tải được chương tiếp theo. Vui lòng kiểm tra kết nối hoặc URL.",
        )

    return (last_ok_url, "\n\n".join(texts).strip(), "")


def preload_next_chapters(current_url: str, look_ahead: int = PRELOAD_LOOK_AHEAD) -> None:
    """Preload next chapters in background for faster navigation."""
    if not current_url:
        return

    global _PRELOAD_FUTURE, _PRELOAD_GENERATION
    with _PRELOAD_LOCK:
        _PRELOAD_GENERATION += 1
        generation = _PRELOAD_GENERATION
        if _PRELOAD_FUTURE is not None and not _PRELOAD_FUTURE.running():
            _PRELOAD_FUTURE.cancel()
        _PRELOAD_FUTURE = _PRELOAD_EXECUTOR.submit(
            _load_chapters_in_background,
            current_url,
            max(0, look_ahead),
            generation,
        )


def _load_chapters_in_background(current_url: str, look_ahead: int, generation: int) -> None:
    """Load only the most recently requested look-ahead range."""
    for step in range(1, look_ahead + 1):
        with _PRELOAD_LOCK:
            if generation != _PRELOAD_GENERATION:
                return

        next_url = change_chapter_url(current_url, step=step)
        if not next_url:
            return

        with _PRELOAD_LOCK:
            if next_url in _PRELOAD_CACHE:
                _PRELOAD_CACHE.move_to_end(next_url)
                continue

        text, err = load_content(next_url)
        if err or not text:
            continue

        with _PRELOAD_LOCK:
            if generation != _PRELOAD_GENERATION:
                return
            _PRELOAD_CACHE[next_url] = text
            _PRELOAD_CACHE.move_to_end(next_url)
            while len(_PRELOAD_CACHE) > PRELOAD_CACHE_SIZE:
                _PRELOAD_CACHE.popitem(last=False)


def get_preloaded_content(url: str) -> str | None:
    """Get preloaded content if available."""
    with _PRELOAD_LOCK:
        text = _PRELOAD_CACHE.get(url)
        if text is not None:
            _PRELOAD_CACHE.move_to_end(url)
        return text


def remove_preloaded_content(url: str) -> None:
    """Remove URL from preload cache."""
    with _PRELOAD_LOCK:
        _PRELOAD_CACHE.pop(url, None)
