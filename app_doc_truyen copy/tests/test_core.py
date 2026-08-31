import base64
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from config.settings import PRELOAD_CACHE_SIZE
from core.cache import DiskCache, MemoryTTLCache
from core.chapter import change_chapter_url, get_chapter_number_from_url
from core.scraper import clean_text, fetch_html, validate_url
from data.bookmarks import BookmarkManager
from data.database import Database
from data.favorites import FavoritesManager
from data.history import HistoryManager
from ui.components.tts_player import get_tts_html


class ChapterNavigationTests(unittest.TestCase):
    def test_change_chapter_preserves_padding_and_suffix(self):
        url = "https://example.com/truyen/chuong-009.html?source=app#doc"
        self.assertEqual(
            change_chapter_url(url, 1),
            "https://example.com/truyen/chuong-010.html?source=app#doc",
        )
        self.assertEqual(get_chapter_number_from_url(url), "009")

    def test_previous_chapter_never_drops_below_one(self):
        self.assertEqual(
            change_chapter_url("https://example.com/chuong-1.html", -1),
            "https://example.com/chuong-1.html",
        )


class CacheTests(unittest.TestCase):
    def test_memory_cache_expires_and_evicts(self):
        cache = MemoryTTLCache(ttl=0.02, max_items=2)
        cache.set("a", "A")
        cache.set("b", "B")
        cache.set("c", "C")
        self.assertIsNone(cache.get("a"))
        self.assertEqual(cache.get("c"), "C")
        time.sleep(0.03)
        self.assertIsNone(cache.get("c"))

    def test_disk_cache_concurrent_writes_remain_readable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = DiskCache(Path(temp_dir), ttl=60)
            values = [f"<html>{index}</html>" for index in range(20)]
            threads = [
                threading.Thread(target=cache.set, args=("https://example.com/1", value))
                for value in values
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertIn(cache.get("https://example.com/1"), values)

    def test_disk_cache_enforces_size_limit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = DiskCache(Path(temp_dir), ttl=60, max_bytes=350)
            for index in range(5):
                cache.set(f"https://example.com/{index}", f"chapter-{index}-" + ("x" * 1000))
            cache.maintain()
            total = sum(path.stat().st_size for path in Path(temp_dir).glob("*.json.gz"))
            self.assertLessEqual(total, 350)


class ScraperTests(unittest.TestCase):
    def test_clean_text_normalizes_spacing(self):
        self.assertEqual(clean_text("Xin\u00a0 chào.  Bạn khỏe?"), "Xin chào.\nBạn khỏe?")

    def test_fetch_rejects_non_http_url(self):
        with self.assertRaises(ValueError):
            fetch_html("file:///etc/passwd")

    def test_url_allowlist_rejects_unknown_domain(self):
        with self.assertRaisesRegex(ValueError, "chưa được cho phép"):
            validate_url("https://example.com/chuong-1.html")

    @patch("core.scraper.socket.getaddrinfo")
    def test_url_validation_rejects_private_dns_result(self, getaddrinfo):
        getaddrinfo.return_value = [(2, 1, 6, "", ("127.0.0.1", 443))]
        with self.assertRaisesRegex(ValueError, "mạng nội bộ"):
            validate_url(
                "https://truyenhoan.com/chuong-1.html",
                resolve_dns=True,
            )

    @patch("core.scraper.socket.getaddrinfo")
    def test_url_validation_accepts_public_allowed_domain(self, getaddrinfo):
        getaddrinfo.return_value = [(2, 1, 6, "", ("1.1.1.1", 443))]
        self.assertEqual(
            validate_url(
                "https://truyenhoan.com/chuong-1.html",
                resolve_dns=True,
            ),
            "https://truyenhoan.com/chuong-1.html",
        )


class DatabaseTests(unittest.TestCase):
    def make_database(self, directory: str) -> Database:
        root = Path(directory)
        (root / "bookmarks.json").write_text(
            json.dumps([
                {
                    "id": 7,
                    "url": "https://truyenhoan.com/a/chuong-1.html",
                    "title": "A",
                    "chapter": "1",
                    "created_at": "2026-01-01T00:00:00",
                    "updated_at": "2026-01-01T00:00:00",
                }
            ]),
            encoding="utf-8",
        )
        (root / "history.json").write_text("[]", encoding="utf-8")
        (root / "favorites.json").write_text("[]", encoding="utf-8")
        (root / "settings.json").write_text('{"theme":"dark"}', encoding="utf-8")
        return Database(
            root / "reader.db",
            bookmarks_file=root / "bookmarks.json",
            history_file=root / "history.json",
            favorites_file=root / "favorites.json",
            settings_file=root / "settings.json",
        )

    def test_json_migration_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db = self.make_database(temp_dir)
            self.assertEqual(db.fetch_one("SELECT COUNT(*) count FROM bookmarks")["count"], 1)
            db._migrate_legacy_json()
            self.assertEqual(db.fetch_one("SELECT COUNT(*) count FROM bookmarks")["count"], 1)
            self.assertTrue((Path(temp_dir) / "bookmarks.json").exists())

    def test_bookmark_ids_never_repeat_after_delete(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db = self.make_database(temp_dir)
            manager = BookmarkManager(db)
            manager.add("https://truyenhoan.com/b/chuong-1.html")
            manager.add("https://truyenhoan.com/c/chuong-1.html")
            manager.remove("https://truyenhoan.com/b/chuong-1.html")
            manager.add("https://truyenhoan.com/d/chuong-1.html")
            ids = [item["id"] for item in manager.get_all()]
            self.assertEqual(len(ids), len(set(ids)))

    def test_history_and_favorites_use_transactional_store(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db = self.make_database(temp_dir)
            history = HistoryManager(db)
            favorites = FavoritesManager(db)
            url = "https://truyenhoan.com/truyen-a/chuong-2.html"
            history.add(url, "2")
            self.assertEqual(history.get_recent(1)[0]["chapter"], "2")
            self.assertTrue(favorites.add(url))
            self.assertTrue(favorites.is_favorite(url))

    def test_concurrent_bookmark_writes_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db = self.make_database(temp_dir)
            manager = BookmarkManager(db)
            threads = [
                threading.Thread(
                    target=manager.add,
                    args=(f"https://truyenhoan.com/story/chuong-{index}.html",),
                )
                for index in range(20)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(len(manager.get_all()), 21)


class TTSComponentTests(unittest.TestCase):
    def test_payload_is_embedded_once_and_player_is_chunked(self):
        text = "Nội dung kiểm thử duy nhất 9f5306f2. " * 300
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        html = get_tts_html(encoded, auto_play=True)
        self.assertEqual(html.count(encoded), 1)
        self.assertIn("MAX_UTTERANCE_CHARS", html)
        self.assertIn("CSS.highlights", html)

    def test_preload_cache_is_bounded(self):
        import core.chapter as chapter

        with chapter._PRELOAD_LOCK:
            chapter._PRELOAD_CACHE.clear()

        with patch.object(chapter, "load_content", return_value=("nội dung", "")):
            chapter.preload_next_chapters(
                "https://example.com/truyen/chuong-1.html",
                look_ahead=PRELOAD_CACHE_SIZE + 5,
            )
            chapter._PRELOAD_FUTURE.result(timeout=5)

        with chapter._PRELOAD_LOCK:
            self.assertLessEqual(len(chapter._PRELOAD_CACHE), PRELOAD_CACHE_SIZE)


if __name__ == "__main__":
    unittest.main()
