# Configuration settings for Story Reader App

import os
from pathlib import Path

# ===================== App Settings =====================
APP_TITLE = "📖 Đọc truyện"
APP_ICON = "📖"
LAYOUT = "wide"

# ===================== HTTP Settings =====================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15"
}
REQUEST_TIMEOUT = 25
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.3
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
POOL_CONNECTIONS = 10
POOL_MAX_SIZE = 20
MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 5 * 1024 * 1024
ALLOWED_DOMAINS = tuple(
    domain.strip().lower().rstrip(".")
    for domain in os.getenv("DOC_TRUYEN_ALLOWED_DOMAINS", "truyenhoan.com").split(",")
    if domain.strip()
)

# ===================== Cache Settings =====================
CACHE_DIR = Path.home() / ".cache" / "doc_truyen"
CACHE_TTL = 3600  # 1 hour in seconds
MEMORY_CACHE_TTL = 3600
DISK_CACHE_MAX_BYTES = 100 * 1024 * 1024

# ===================== Preload Settings =====================
PRELOAD_LOOK_AHEAD = 3  # Number of chapters to preload
PRELOAD_CACHE_SIZE = 12 # Prevent long reading sessions from growing forever
MAX_CHAPTER_LOAD = 10   # Max chapters to load at once
THREAD_POOL_SIZE = 4    # Bounded parallel loading avoids network/resource spikes

# ===================== Data Storage =====================
DATA_DIR = Path.home() / ".config" / "doc_truyen"
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
HISTORY_FILE = DATA_DIR / "history.json"
FAVORITES_FILE = DATA_DIR / "favorites.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
DATABASE_FILE = DATA_DIR / "reader.db"
LOG_FILE = DATA_DIR / "app.log"

# ===================== TTS Settings =====================
DEFAULT_RATE = 1.0
DEFAULT_PITCH = 1.0
MIN_RATE = 0.5
MAX_RATE = 2.0
MIN_PITCH = 0.0
MAX_PITCH = 2.0
RATE_STEP = 0.1
PITCH_STEP = 0.1
BASE_CPS = 14.0  # Characters per second

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
