# Web scraping and HTML parsing module

import ipaddress
import logging
import re
import socket
import threading
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import (
    ALLOWED_DOMAINS, BACKOFF_FACTOR, HEADERS, MAX_REDIRECTS,
    MAX_RESPONSE_BYTES, MAX_RETRIES, POOL_CONNECTIONS, POOL_MAX_SIZE,
    REQUEST_TIMEOUT, RETRY_STATUS_CODES,
)
from core.cache import disk_cache, memory_cache


logger = logging.getLogger(__name__)
REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


# ===================== HTTP Session with Connection Pooling =====================
def create_http_session() -> requests.Session:
    """Create HTTP session with retry strategy and connection pooling."""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=RETRY_STATUS_CODES,
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=POOL_CONNECTIONS,
        pool_maxsize=POOL_MAX_SIZE,
        pool_block=True,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session


# requests.Session is not guaranteed to be thread-safe. Each worker reuses its
# own connection pool instead of sharing mutable session state across threads.
_THREAD_LOCAL = threading.local()
_FETCH_LOCKS = tuple(threading.Lock() for _ in range(32))


def get_http_session() -> requests.Session:
    session = getattr(_THREAD_LOCAL, "http_session", None)
    if session is None:
        session = create_http_session()
        _THREAD_LOCAL.http_session = session
    return session


# ===================== Text Processing =====================
def clean_text(text: str) -> str:
    """Clean and normalize text for reading."""
    text = re.sub(r"\u00A0", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([\.!?…])( )", r"\1\n", text)  # Break sentences for easier listening
    return text.strip()


def extract_text_from_html(html_src: str) -> str:
    """Extract readable text from HTML using readability."""
    doc = Document(html_src)
    summary_html = doc.summary(html_partial=True)
    soup = BeautifulSoup(summary_html, "lxml")
    parts = [p.get_text(" ", strip=True) for p in soup.find_all(["p", "h2", "h3", "blockquote"])]
    return clean_text("\n".join([t for t in parts if t]))


# ===================== HTML Fetching =====================
def validate_url(url: str, *, resolve_dns: bool = False) -> str:
    """Validate a reader URL and reject internal/untrusted destinations."""
    normalized_url = url.strip()
    parsed = urlparse(normalized_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL phải bắt đầu bằng http:// hoặc https://")
    if parsed.username or parsed.password:
        raise ValueError("URL không được chứa thông tin đăng nhập")

    hostname = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    if not any(hostname == domain or hostname.endswith(f".{domain}") for domain in ALLOWED_DOMAINS):
        allowed = ", ".join(ALLOWED_DOMAINS) or "(chưa cấu hình)"
        raise ValueError(f"Tên miền chưa được cho phép. Hiện hỗ trợ: {allowed}")

    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError("Cổng trong URL không hợp lệ") from error
    if port not in {None, 80, 443}:
        raise ValueError("URL chỉ được dùng cổng 80 hoặc 443")

    if not resolve_dns:
        return normalized_url

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(hostname, port or (443 if parsed.scheme == "https" else 80))
        }
    except socket.gaierror as error:
        raise ValueError(f"Không phân giải được tên miền {hostname}") from error

    if not addresses:
        raise ValueError(f"Không tìm thấy địa chỉ cho tên miền {hostname}")
    for address in addresses:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
        if not ip.is_global:
            raise ValueError("URL trỏ tới mạng nội bộ hoặc địa chỉ không an toàn")

    return normalized_url


def _download_html(url: str, timeout: int) -> str:
    current_url = url
    session = get_http_session()

    for redirect_count in range(MAX_REDIRECTS + 1):
        current_url = validate_url(current_url, resolve_dns=True)
        with session.get(
            current_url,
            timeout=(5, timeout),
            allow_redirects=False,
            stream=True,
        ) as response:
            if response.status_code in REDIRECT_STATUS_CODES:
                location = response.headers.get("Location")
                if not location:
                    raise requests.HTTPError("Redirect không có địa chỉ đích", response=response)
                if redirect_count >= MAX_REDIRECTS:
                    raise requests.TooManyRedirects(f"Vượt quá {MAX_REDIRECTS} lần chuyển hướng")
                current_url = urljoin(current_url, location)
                continue

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if content_type and "html" not in content_type and "text/" not in content_type:
                raise ValueError(f"Nội dung trả về không phải HTML ({content_type.split(';', 1)[0]})")

            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    declared_size = int(content_length)
                except ValueError:
                    declared_size = None
                if declared_size is not None and declared_size > MAX_RESPONSE_BYTES:
                    raise ValueError("Trang truyện vượt quá giới hạn dung lượng cho phép")

            chunks = []
            downloaded = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                downloaded += len(chunk)
                if downloaded > MAX_RESPONSE_BYTES:
                    raise ValueError("Trang truyện vượt quá giới hạn dung lượng cho phép")
                chunks.append(chunk)

            payload = b"".join(chunks)
            response._content = payload
            response._content_consumed = True
            encoding = response.encoding
            if not encoding or encoding.lower() == "iso-8859-1":
                encoding = response.apparent_encoding or "utf-8"
            return payload.decode(encoding, errors="replace")

    raise requests.TooManyRedirects(f"Vượt quá {MAX_REDIRECTS} lần chuyển hướng")


def fetch_html(url: str, timeout: int = REQUEST_TIMEOUT) -> str:
    """Fetch HTML from URL with caching (disk + memory)."""
    url = validate_url(url)

    cached = memory_cache.get(url)
    if cached is not None:
        return cached

    # Serialize only identical lock stripes. This prevents several preload
    # workers from downloading and writing the same chapter simultaneously.
    fetch_lock = _FETCH_LOCKS[hash(url) % len(_FETCH_LOCKS)]
    with fetch_lock:
        cached = memory_cache.get(url)
        if cached is not None:
            return cached

        cached = disk_cache.get(url)
        if cached is not None:
            memory_cache.set(url, cached)
            return cached

        html = _download_html(url, timeout)

        disk_cache.set(url, html)
        memory_cache.set(url, html)
        return html
