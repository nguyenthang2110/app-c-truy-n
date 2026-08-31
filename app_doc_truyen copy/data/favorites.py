"""Favorite-story management backed by SQLite."""

from datetime import datetime
from urllib.parse import urlparse

from data.database import Database, database


class FavoritesManager:
    """Manage favorite stories."""

    def __init__(self, db: Database = database):
        self.db = db

    @staticmethod
    def _get_story_key(url: str) -> str:
        parsed = urlparse(url)
        parts = parsed.path.rsplit("/", 1)
        base_path = parts[0] if len(parts) > 1 else parsed.path
        return f"{parsed.netloc}{base_path}"

    @staticmethod
    def _extract_title_from_url(url: str) -> str:
        parsed = urlparse(url)
        parts = parsed.path.strip("/").split("/")
        if parts and parts[0]:
            name = parts[0] if len(parts) == 1 else parts[-2]
            return name.replace("-", " ").replace("_", " ").title()
        return "Không rõ"

    def add(self, url: str, title: str = "", cover_url: str = "") -> bool:
        return self.db.execute(
            """
            INSERT OR IGNORE INTO favorites (story_key, url, title, cover_url, added_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                self._get_story_key(url),
                url,
                title or self._extract_title_from_url(url),
                cover_url,
                datetime.now().astimezone().isoformat(),
            ),
        ) > 0

    def remove(self, url: str) -> bool:
        return self.db.execute(
            "DELETE FROM favorites WHERE story_key = ?",
            (self._get_story_key(url),),
        ) > 0

    def get_all(self) -> list[dict]:
        return self.db.fetch_all(
            """
            SELECT url, title, cover_url, story_key, added_at
            FROM favorites ORDER BY added_at DESC
            """
        )

    def is_favorite(self, url: str) -> bool:
        return self.db.fetch_one(
            "SELECT story_key FROM favorites WHERE story_key = ?",
            (self._get_story_key(url),),
        ) is not None

    def toggle(self, url: str, title: str = "") -> bool:
        story_key = self._get_story_key(url)
        with self.db.connection() as connection:
            existing = connection.execute(
                "SELECT 1 FROM favorites WHERE story_key = ?", (story_key,)
            ).fetchone()
            if existing:
                connection.execute("DELETE FROM favorites WHERE story_key = ?", (story_key,))
                return False
            connection.execute(
                """
                INSERT INTO favorites (story_key, url, title, cover_url, added_at)
                VALUES (?, ?, ?, '', ?)
                """,
                (
                    story_key,
                    url,
                    title or self._extract_title_from_url(url),
                    datetime.now().astimezone().isoformat(),
                ),
            )
            return True

    def clear_all(self) -> None:
        self.db.execute("DELETE FROM favorites")


favorites_manager = FavoritesManager()
