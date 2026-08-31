"""Bookmark management backed by SQLite."""

from datetime import datetime

from data.database import Database, database


class BookmarkManager:
    """Manage reading bookmarks with stable, autoincrementing IDs."""

    def __init__(self, db: Database = database):
        self.db = db

    def add(self, url: str, title: str = "", chapter: str = "", note: str = "") -> bool:
        now = datetime.now().astimezone().isoformat()
        self.db.execute(
            """
            INSERT INTO bookmarks (url, title, chapter, note, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = CASE WHEN excluded.title <> '' THEN excluded.title ELSE bookmarks.title END,
                chapter = CASE WHEN excluded.chapter <> '' THEN excluded.chapter ELSE bookmarks.chapter END,
                note = CASE WHEN excluded.note <> '' THEN excluded.note ELSE bookmarks.note END,
                updated_at = excluded.updated_at
            """,
            (url, title, chapter, note, now, now),
        )
        return True

    def remove(self, url: str) -> bool:
        return self.db.execute("DELETE FROM bookmarks WHERE url = ?", (url,)) > 0

    def get_all(self) -> list[dict]:
        return self.db.fetch_all(
            """
            SELECT id, url, title, chapter, note, created_at, updated_at
            FROM bookmarks
            ORDER BY updated_at DESC
            """
        )

    def get_by_url(self, url: str) -> dict | None:
        return self.db.fetch_one(
            """
            SELECT id, url, title, chapter, note, created_at, updated_at
            FROM bookmarks WHERE url = ?
            """,
            (url,),
        )

    def is_bookmarked(self, url: str) -> bool:
        return self.get_by_url(url) is not None

    def clear_all(self) -> None:
        self.db.execute("DELETE FROM bookmarks")


bookmark_manager = BookmarkManager()
