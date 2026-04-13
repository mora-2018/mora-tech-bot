import time
import xmlrpc.client
import requests
from config import Config


def check_n8n_health() -> dict:
    try:
        start = time.time()
        r = requests.get(f"{Config.N8N_URL}/healthz", timeout=8)
        elapsed = round((time.time() - start) * 1000)
        if r.status_code == 200:
            return {"status": "up", "response_ms": elapsed}
        return {"status": "degraded", "http_status": r.status_code, "response_ms": elapsed}
    except requests.exceptions.ConnectionError:
        return {"status": "down", "error": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"status": "down", "error": "Timeout after 8s"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def check_website(url: str) -> dict:
    # Normalise
    if not url.startswith("http"):
        url = f"https://{url}"
    try:
        start = time.time()
        r = requests.get(url, timeout=10, allow_redirects=True)
        elapsed = round((time.time() - start) * 1000)
        return {
            "status": "up" if r.status_code < 400 else "error",
            "http_status": r.status_code,
            "response_ms": elapsed,
            "url": url,
        }
    except requests.exceptions.ConnectionError:
        return {"status": "down", "url": url, "error": "Connection refused"}
    except requests.exceptions.Timeout:
        return {"status": "down", "url": url, "error": "Timeout after 10s"}
    except Exception as e:
        return {"status": "error", "url": url, "error": str(e)}


def check_odoo_health() -> dict:
    try:
        common = xmlrpc.client.ServerProxy(f"{Config.ODOO_URL}/xmlrpc/2/common")
        version = common.version()
        return {
            "status": "up",
            "server_version": version.get("server_version"),
            "db": Config.ODOO_DB,
        }
    except Exception as e:
        return {"status": "down", "error": str(e)}
