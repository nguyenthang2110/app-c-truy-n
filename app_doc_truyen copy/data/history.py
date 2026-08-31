"""Reading history management backed by SQLite."""

from datetime import datetime
from urllib.parse import urlparse

from data.database import Database, database


class HistoryManager:
    """Manage the latest reading position for each story."""

    MAX_HISTORY_ITEMS = 100

    def __init__(self, db: Database = database):
        self.db = db

    @staticmethod
    def _get_story_key(url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path
        parts = path.rsplit("/", 1)
        base_path = parts[0] if len(parts) > 1 else path
        return f"{parsed.netloc}{base_path}"

    @staticmethod
    def _extract_title_from_url(url: str) -> str:
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        if parts and parts[0]:
            name = parts[0] if len(parts) == 1 else parts[-2]
            return name.replace("-", " ").replace("_", " ").title()
        return "Không rõ"

    def add(self, url: str, chapter: str = "", title: str = "") -> None:
        story_key = self._get_story_key(url)
        read_at = datetime.now().astimezone().isoformat()
        with self.db.connection() as connection:
            connection.execute(
                """
                INSERT INTO history (story_key, url, chapter, title, read_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(story_key) DO UPDATE SET
                    url = excluded.url,
                    chapter = excluded.chapter,
                    title = excluded.title,
                    read_at = excluded.read_at
                """,
                (story_key, url, chapter, title or self._extract_title_from_url(url), read_at),
            )
            connection.execute(
                """
                DELETE FROM history
                WHERE story_key IN (
                    SELECT story_key FROM history
                    ORDER BY read_at DESC
                    LIMIT -1 OFFSET ?
                )
                """,
                (self.MAX_HISTORY_ITEMS,),
            )

    def get_all(self) -> list[dict]:
        return self.db.fetch_all(
            """
            SELECT url, chapter, title, story_key, read_at
            FROM history ORDER BY read_at DESC
            """
        )

    def get_recent(self, limit: int = 10) -> list[dict]:
        return self.db.fetch_all(
            """
            SELECT url, chapter, title, story_key, read_at
            FROM history ORDER BY read_at DESC LIMIT ?
            """,
            (max(0, limit),),
        )

    def get_last_read(self, url: str) -> dict | None:
        return self.db.fetch_one(
            """
            SELECT url, chapter, title, story_key, read_at
            FROM history WHERE story_key = ?
            """,
            (self._get_story_key(url),),
        )

    def remove(self, url: str) -> bool:
        return self.db.execute(
            "DELETE FROM history WHERE story_key = ?",
            (self._get_story_key(url),),
        ) > 0

    def clear_all(self) -> None:
        self.db.execute("DELETE FROM history")


history_manager = HistoryManager()
