"""Bounded memory and compressed disk caches."""

import gzip
import hashlib
import json
import logging
import os
import tempfile
import threading
import time
from collections import OrderedDict
from pathlib import Path

from config.settings import (
    CACHE_DIR,
    CACHE_TTL,
    DISK_CACHE_MAX_BYTES,
    MEMORY_CACHE_TTL,
)


logger = logging.getLogger(__name__)


def get_cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


class DiskCache:
    """Persistent compressed cache with atomic writes and size eviction."""

    def __init__(
        self,
        cache_dir: Path = CACHE_DIR,
        ttl: int = CACHE_TTL,
        max_bytes: int = DISK_CACHE_MAX_BYTES,
    ):
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        self.max_bytes = max_bytes
        self._lock = threading.RLock()
        self._writes_since_maintenance = 0
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._remove_legacy_pickle_cache()
        self.maintain()

    def _path_for(self, url: str) -> Path:
        return self.cache_dir / f"{get_cache_key(url)}.json.gz"

    @staticmethod
    def _decode(path: Path) -> dict:
        raw = gzip.decompress(path.read_bytes())
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Cache payload không phải object")
        return payload

    def _remove_legacy_pickle_cache(self) -> None:
        removed = 0
        for path in self.cache_dir.glob("*.pkl"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                logger.warning("Không xóa được cache pickle cũ: %s", path, exc_info=True)
        if removed:
            logger.info("Đã xóa %s file cache pickle cũ", removed)

    def get(self, url: str) -> str | None:
        path = self._path_for(url)
        with self._lock:
            if not path.exists():
                return None
            try:
                payload = self._decode(path)
                timestamp = float(payload["timestamp"])
                html = payload["html"]
                if not isinstance(html, str):
                    raise TypeError("Cache HTML không phải chuỗi")
                if time.time() - timestamp >= self.ttl:
                    path.unlink(missing_ok=True)
                    return None
                path.touch(exist_ok=True)
                return html
            except (OSError, gzip.BadGzipFile, json.JSONDecodeError, KeyError, TypeError, ValueError):
                logger.warning("Cache hỏng, sẽ tải lại: %s", path, exc_info=True)
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("Không xóa được cache hỏng: %s", path, exc_info=True)
                return None

    def set(self, url: str, html: str) -> None:
        path = self._path_for(url)
        temp_name: str | None = None
        try:
            payload = json.dumps(
                {"html": html, "timestamp": time.time()},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            compressed = gzip.compress(payload, compresslevel=6)
            with self._lock:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=self.cache_dir,
                    prefix=f".{path.stem}-",
                    suffix=".tmp",
                    delete=False,
                ) as temp_file:
                    temp_name = temp_file.name
                    temp_file.write(compressed)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())
                os.replace(temp_name, path)
                temp_name = None
                self._writes_since_maintenance += 1
                if self._writes_since_maintenance >= 25:
                    self._writes_since_maintenance = 0
                    self.maintain()
        except OSError:
            logger.warning("Không ghi được disk cache cho %s", url, exc_info=True)
        finally:
            if temp_name:
                try:
                    Path(temp_name).unlink(missing_ok=True)
                except OSError:
                    logger.warning("Không dọn được cache tạm: %s", temp_name, exc_info=True)

    def clear(self) -> None:
        with self._lock:
            for pattern in ("*.json.gz", "*.pkl", ".*.tmp"):
                for path in self.cache_dir.glob(pattern):
                    try:
                        path.unlink()
                    except OSError:
                        logger.warning("Không xóa được cache: %s", path, exc_info=True)

    def clear_expired(self) -> int:
        cleared = 0
        now = time.time()
        with self._lock:
            for path in self.cache_dir.glob("*.json.gz"):
                try:
                    payload = self._decode(path)
                    if now - float(payload["timestamp"]) >= self.ttl:
                        path.unlink()
                        cleared += 1
                except (OSError, gzip.BadGzipFile, json.JSONDecodeError, KeyError, TypeError, ValueError):
                    try:
                        path.unlink(missing_ok=True)
                        cleared += 1
                    except OSError:
                        logger.warning("Không xóa được cache lỗi: %s", path, exc_info=True)
        return cleared

    def maintain(self) -> int:
        """Remove expired/corrupt entries and evict least-recently-used files."""
        with self._lock:
            removed = self.clear_expired()
            entries = []
            total_bytes = 0
            for path in self.cache_dir.glob("*.json.gz"):
                try:
                    stat = path.stat()
                except OSError:
                    continue
                entries.append((stat.st_mtime, stat.st_size, path))
                total_bytes += stat.st_size

            for _, size, path in sorted(entries):
                if total_bytes <= self.max_bytes:
                    break
                try:
                    path.unlink()
                    total_bytes -= size
                    removed += 1
                except OSError:
                    logger.warning("Không xóa được cache khi giới hạn dung lượng: %s", path)
            return removed


class MemoryTTLCache:
    """Small, thread-safe in-memory cache with LRU eviction."""

    def __init__(self, ttl: int, max_items: int = 128):
        self.ttl = ttl
        self.max_items = max_items
        self._items: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> str | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            created_at, value = item
            if time.monotonic() - created_at >= self.ttl:
                del self._items[key]
                return None
            self._items.move_to_end(key)
            return value

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._items[key] = (time.monotonic(), value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_items:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


disk_cache = DiskCache()
memory_cache = MemoryTTLCache(ttl=MEMORY_CACHE_TTL)
