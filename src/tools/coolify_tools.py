import requests
from config import Config

_HEADERS = {
    "Authorization": f"Bearer {Config.COOLIFY_TOKEN}",
    "Content-Type": "application/json",
}
_BASE = Config.COOLIFY_URL.rstrip("/") + "/api/v1"


def get_coolify_service_status() -> dict:
    try:
        r = requests.get(
            f"{_BASE}/services/{Config.N8N_SERVICE_UUID}",
            headers=_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        return {
            "name": data.get("name"),
            "status": data.get("status"),
            "fqdn": data.get("fqdn"),
        }
    except Exception as e:
        return {"error": str(e)}


def restart_coolify_n8n() -> dict:
    try:
        r = requests.post(
            f"{_BASE}/services/{Config.N8N_SERVICE_UUID}/restart",
            headers=_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
        return {"restarted": True, "service_uuid": Config.N8N_SERVICE_UUID}
    except Exception as e:
        return {"restarted": False, "error": str(e)}
