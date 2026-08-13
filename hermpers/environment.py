import os


BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8642/v1").rstrip("/")
_base_uri_from_url = BASE_URL[:-3] if BASE_URL.endswith("/v1") else BASE_URL
BASE_URI = os.environ.get("BASE_URI", _base_uri_from_url).rstrip("/")

API_KEY = os.environ.get("API_KEY", "your_api_key_here")
API_SERVER_KEY = os.environ.get("API_SERVER_KEY", API_KEY)
MASTER_KEY_TOKEN = os.environ.get("MASTER_KEY_TOKEN", "")
MODEL = os.environ.get("MODEL", "deepseek-v4-flash")
HERMES_HTTP_TIMEOUT = float(os.environ.get("HERMES_HTTP_TIMEOUT", "60"))

ROOM_BASE_URL = os.environ.get("ROOM_BASE_URL", "https://chat.nvgtrs.io").rstrip("/")
PORT = os.environ.get("PORT", "80")
RELOAD = os.environ.get("RELOAD", "False")

MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
MAX_TEXT_ATTACHMENT_CHARS = int(os.environ.get("MAX_TEXT_ATTACHMENT_CHARS", "12000"))
MAX_REPLY_FILE_UPLOADS = int(os.environ.get("MAX_REPLY_FILE_UPLOADS", "5"))
MAX_REPLY_FILE_UPLOAD_BYTES = int(os.environ.get("MAX_REPLY_FILE_UPLOAD_BYTES", str(20 * 1024 * 1024)))


def _default_sqlite_path() -> str:
    # In Docker use a volume-friendly location; local runs stay in the project directory.
    if os.path.exists("/.dockerenv"):
        return "/data/w-bridge/w_bridge.db"
    return "./w_bridge.db"


def _build_database_url() -> str:
    explicit_database_url = os.environ.get("DATABASE_URL")
    if explicit_database_url:
        return explicit_database_url

    sqlite_path = os.environ.get("SQLITE_DB_PATH", _default_sqlite_path())
    if sqlite_path.startswith("/"):
        return f"sqlite:////{sqlite_path.lstrip('/')}"
    return f"sqlite:///{sqlite_path}"


DATABASE_URL = _build_database_url()
