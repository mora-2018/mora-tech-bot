import requests
from config import Config

_HEADERS = {"X-N8N-API-KEY": Config.N8N_API_KEY, "Content-Type": "application/json"}
_BASE = Config.N8N_URL.rstrip("/") + "/api/v1"


def _get(path: str, params: dict = None) -> dict | list:
    r = requests.get(f"{_BASE}{path}", headers=_HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def _patch(path: str, body: dict) -> dict:
    r = requests.patch(f"{_BASE}{path}", headers=_HEADERS, json=body, timeout=10)
    r.raise_for_status()
    return r.json()


def list_n8n_workflows() -> list:
    data = _get("/workflows")
    workflows = data.get("data", data) if isinstance(data, dict) else data
    return [
        {
            "id": w["id"],
            "name": w["name"],
            "active": w.get("active", False),
            "updated": w.get("updatedAt", ""),
        }
        for w in workflows
    ]


def get_n8n_workflow_errors(workflow_id: str) -> list:
    executions = _get("/executions", params={"workflowId": workflow_id, "status": "error", "limit": 5})
    items = executions.get("data", []) if isinstance(executions, dict) else executions
    results = []
    for ex in items:
        results.append({
            "execution_id": ex.get("id"),
            "status": ex.get("status"),
            "started": ex.get("startedAt"),
            "stopped": ex.get("stoppedAt"),
        })
    return results


def get_n8n_execution_detail(execution_id: str) -> dict:
    data = _get(f"/executions/{execution_id}")
    # Extract the failed node and error message from runData
    run_data = data.get("data", {}).get("resultData", {}).get("runData", {})
    error_nodes = {}
    for node_name, node_runs in run_data.items():
        for run in node_runs:
            error = run.get("error")
            if error:
                error_nodes[node_name] = {
                    "message": error.get("message", ""),
                    "type": error.get("name", ""),
                }
    return {
        "execution_id": execution_id,
        "status": data.get("status"),
        "started": data.get("startedAt"),
        "stopped": data.get("stoppedAt"),
        "failed_nodes": error_nodes,
    }


def activate_n8n_workflow(workflow_id: str) -> dict:
    result = _patch(f"/workflows/{workflow_id}", {"active": True})
    return {"workflow_id": workflow_id, "active": result.get("active"), "name": result.get("name")}


def deactivate_n8n_workflow(workflow_id: str) -> dict:
    result = _patch(f"/workflows/{workflow_id}", {"active": False})
    return {"workflow_id": workflow_id, "active": result.get("active"), "name": result.get("name")}
