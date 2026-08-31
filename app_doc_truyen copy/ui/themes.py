"""Theme preference management backed by SQLite."""

from typing import Literal

from data.database import Database, database


ThemeType = Literal["dark", "light", "auto"]


class ThemeManager:
    def __init__(self, db: Database = database):
        self.db = db

    def get_theme(self) -> ThemeType:
        theme = self.db.get_setting("theme", "dark")
        return theme if theme in {"dark", "light", "auto"} else "dark"

    def set_theme(self, theme: ThemeType) -> None:
        if theme not in {"dark", "light", "auto"}:
            raise ValueError(f"Theme không hợp lệ: {theme}")
        self.db.set_setting("theme", theme)

    def toggle_theme(self) -> ThemeType:
        new_theme: ThemeType = "light" if self.get_theme() == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme

    def is_dark(self) -> bool:
        return self.get_theme() in {"dark", "auto"}


theme_manager = ThemeManager()
