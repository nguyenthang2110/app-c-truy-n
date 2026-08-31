"""Thread-safe SQLite storage with one-time migration from legacy JSON files."""

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Sequence

from config.settings import (
    BOOKMARKS_FILE,
    DATABASE_FILE,
    FAVORITES_FILE,
    HISTORY_FILE,
    SETTINGS_FILE,
)


logger = logging.getLogger(__name__)


SCHEMA = """
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL DEFAULT '',
    chapter TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS history (
    story_key TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    chapter TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    read_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    story_key TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    cover_url TEXT NOT NULL DEFAULT '',
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS migrations (
    key TEXT PRIMARY KEY,
    migrated_at TEXT NOT NULL
);
"""


class Database:
    """Open short-lived SQLite connections for safe multi-threaded access."""

    MIGRATION_KEY = "legacy_json_v1"

    def __init__(
        self,
        db_path: Path = DATABASE_FILE,
        *,
        bookmarks_file: Path = BOOKMARKS_FILE,
        history_file: Path = HISTORY_FILE,
        favorites_file: Path = FAVORITES_FILE,
        settings_file: Path = SETTINGS_FILE,
        migrate_legacy: bool = True,
    ):
        self.db_path = Path(db_path)
        self.bookmarks_file = Path(bookmarks_file)
        self.history_file = Path(history_file)
        self.favorites_file = Path(favorites_file)
        self.settings_file = Path(settings_file)
        self._initialize_lock = threading.RLock()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()
        if migrate_legacy:
            self._migrate_legacy_json()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._initialize_lock, self.connection() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
            connection.executescript(SCHEMA)

    def execute(self, sql: str, parameters: Sequence[object] = ()) -> int:
        with self.connection() as connection:
            cursor = connection.execute(sql, parameters)
            return cursor.rowcount

    def fetch_one(self, sql: str, parameters: Sequence[object] = ()) -> dict | None:
        with self.connection() as connection:
            row = connection.execute(sql, parameters).fetchone()
            return dict(row) if row is not None else None

    def fetch_all(self, sql: str, parameters: Sequence[object] = ()) -> list[dict]:
        with self.connection() as connection:
            rows = connection.execute(sql, parameters).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def _read_json(path: Path, default: object) -> object:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as source:
            return json.load(source)

    def _migrate_legacy_json(self) -> None:
        if self.fetch_one("SELECT key FROM migrations WHERE key = ?", (self.MIGRATION_KEY,)):
            return

        try:
            bookmarks = self._read_json(self.bookmarks_file, [])
            history = self._read_json(self.history_file, [])
            favorites = self._read_json(self.favorites_file, [])
            settings = self._read_json(self.settings_file, {})
            if not isinstance(bookmarks, list) or not isinstance(history, list):
                raise ValueError("Dữ liệu bookmark/history cũ không đúng định dạng")
            if not isinstance(favorites, list) or not isinstance(settings, dict):
                raise ValueError("Dữ liệu favorite/settings cũ không đúng định dạng")
        except (OSError, json.JSONDecodeError, ValueError):
            logger.exception("Không thể đọc dữ liệu JSON cũ; chưa đánh dấu migration")
            return

        now = datetime.now().astimezone().isoformat()
        with self.connection() as connection:
            for item in bookmarks:
                if not isinstance(item, dict) or not item.get("url"):
                    continue
                parameters = (
                    item.get("id"),
                    str(item["url"]),
                    str(item.get("title", "")),
                    str(item.get("chapter", "")),
                    str(item.get("note", "")),
                    str(item.get("created_at", now)),
                    str(item.get("updated_at", item.get("created_at", now))),
                )
                connection.execute(
                    """
                    INSERT OR IGNORE INTO bookmarks
                        (id, url, title, chapter, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    parameters,
                )

            for item in history:
                if not isinstance(item, dict) or not item.get("url"):
                    continue
                story_key = str(item.get("story_key") or item["url"])
                connection.execute(
                    """
                    INSERT OR IGNORE INTO history
                        (story_key, url, chapter, title, read_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        story_key,
                        str(item["url"]),
                        str(item.get("chapter", "")),
                        str(item.get("title", "")),
                        str(item.get("read_at", now)),
                    ),
                )

            for item in favorites:
                if not isinstance(item, dict) or not item.get("url"):
                    continue
                story_key = str(item.get("story_key") or item["url"])
                connection.execute(
                    """
                    INSERT OR IGNORE INTO favorites
                        (story_key, url, title, cover_url, added_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        story_key,
                        str(item["url"]),
                        str(item.get("title", "")),
                        str(item.get("cover_url", "")),
                        str(item.get("added_at", now)),
                    ),
                )

            for key, value in settings.items():
                connection.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (str(key), json.dumps(value, ensure_ascii=False)),
                )

            connection.execute(
                "INSERT INTO migrations (key, migrated_at) VALUES (?, ?)",
                (self.MIGRATION_KEY, now),
            )

        logger.info(
            "Đã migration JSON sang SQLite: %s bookmark, %s lịch sử, %s yêu thích",
            len(bookmarks),
            len(history),
            len(favorites),
        )

    def get_setting(self, key: str, default: object = None) -> object:
        row = self.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (TypeError, json.JSONDecodeError):
            logger.warning("Giá trị setting %s bị lỗi; dùng mặc định", key)
            return default

    def set_setting(self, key: str, value: object) -> None:
        self.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, json.dumps(value, ensure_ascii=False)),
        )


database = Database()
