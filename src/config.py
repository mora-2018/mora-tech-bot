import os


def _require(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f"Missing required env var: {key}")
    return val


class Config:
    TELEGRAM_BOT_TOKEN: str = _require("TELEGRAM_BOT_TOKEN")
    MALEESHA_CHAT_ID: int = int(_require("MALEESHA_CHAT_ID"))
    STAFF_GROUP_CHAT_IDS: list[int] = [
        int(x.strip()) for x in _require("STAFF_GROUP_CHAT_IDS").split(",")
    ]
    ALLOWED_CHAT_IDS: set[int] = set()  # populated after class definition

    ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")

    N8N_URL: str = _require("N8N_URL")
    N8N_API_KEY: str = _require("N8N_API_KEY")

    COOLIFY_URL: str = _require("COOLIFY_URL")
    COOLIFY_TOKEN: str = _require("COOLIFY_TOKEN")
    N8N_SERVICE_UUID: str = _require("N8N_SERVICE_UUID")

    ODOO_URL: str = _require("ODOO_URL")
    ODOO_DB: str = _require("ODOO_DB")
    ODOO_UID: int = int(_require("ODOO_UID"))
    ODOO_PASSWORD: str = _require("ODOO_PASSWORD")


Config.ALLOWED_CHAT_IDS = set(Config.STAFF_GROUP_CHAT_IDS) | {Config.MALEESHA_CHAT_ID}
