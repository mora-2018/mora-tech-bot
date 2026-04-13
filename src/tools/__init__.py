from tools.health_tools import check_n8n_health, check_website, check_odoo_health
from tools.n8n_tools import (
    list_n8n_workflows,
    get_n8n_workflow_errors,
    get_n8n_execution_detail,
    activate_n8n_workflow,
    deactivate_n8n_workflow,
)
from tools.coolify_tools import get_coolify_service_status, restart_coolify_n8n

# Registry: tool name -> function
_REGISTRY = {
    "check_n8n_health": check_n8n_health,
    "check_website": check_website,
    "check_odoo_health": check_odoo_health,
    "list_n8n_workflows": list_n8n_workflows,
    "get_n8n_workflow_errors": get_n8n_workflow_errors,
    "get_n8n_execution_detail": get_n8n_execution_detail,
    "activate_n8n_workflow": activate_n8n_workflow,
    "deactivate_n8n_workflow": deactivate_n8n_workflow,
    "get_coolify_service_status": get_coolify_service_status,
    "restart_coolify_n8n": restart_coolify_n8n,
}


def execute_tool(name: str, args: dict) -> object:
    fn = _REGISTRY.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    return fn(**args)


# Tool definitions sent to Claude API
TOOL_DEFINITIONS = [
    {
        "name": "check_n8n_health",
        "description": "Check if the n8n automation server is running and responsive.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "check_website",
        "description": "Check if a website is up. Use for mora.lk, squaloroma.com, or any URL.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to check, e.g. mora.lk or squaloroma.com"}
            },
            "required": ["url"],
        },
    },
    {
        "name": "check_odoo_health",
        "description": "Check if the Odoo ERP system is running and accessible.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_n8n_workflows",
        "description": "List all n8n workflows with their name, ID, and active/inactive status.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_n8n_workflow_errors",
        "description": "Get recent failed executions for a specific n8n workflow.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "The workflow ID from list_n8n_workflows"}
            },
            "required": ["workflow_id"],
        },
    },
    {
        "name": "get_n8n_execution_detail",
        "description": "Get full detail of a specific n8n execution including which node failed and why.",
        "input_schema": {
            "type": "object",
            "properties": {
                "execution_id": {"type": "string", "description": "Execution ID from get_n8n_workflow_errors"}
            },
            "required": ["execution_id"],
        },
    },
    {
        "name": "activate_n8n_workflow",
        "description": "Reactivate a stopped or deactivated n8n workflow. Use when a workflow is showing as inactive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "The workflow ID to reactivate"}
            },
            "required": ["workflow_id"],
        },
    },
    {
        "name": "deactivate_n8n_workflow",
        "description": "Deactivate an n8n workflow. Requires staff approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "The workflow ID to deactivate"}
            },
            "required": ["workflow_id"],
        },
    },
    {
        "name": "get_coolify_service_status",
        "description": "Check the status of the n8n service on the hosting server.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "restart_coolify_n8n",
        "description": "Restart the n8n container via Coolify. Use when n8n is completely unresponsive.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]
