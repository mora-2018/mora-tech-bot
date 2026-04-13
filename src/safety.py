from context import ConversationContext

# Tier 1: auto-execute, no confirmation needed
TIER_1 = {
    "check_n8n_health",
    "check_website",
    "check_odoo_health",
    "list_n8n_workflows",
    "get_n8n_workflow_errors",
    "get_n8n_execution_detail",
    "get_coolify_service_status",
    "activate_n8n_workflow",   # reactivate a stopped workflow
    "restart_coolify_n8n",     # restart the n8n container
}

# Tier 2: requires staff confirmation via inline button
TIER_2 = {
    "deactivate_n8n_workflow",
    "update_shopify_product_status",
    "update_odoo_product_active",
    "retry_failed_queue_lines",
}

# Tier 3+: never execute — escalate to Maleesha only
TIER_3 = set()  # No tools. If it's Tier 3, don't put it in TOOL_REGISTRY at all.


class RequiresApprovalError(Exception):
    def __init__(self, tool_name: str, tool_args: dict, token: str, description: str):
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.token = token
        self.description = description
        super().__init__(f"Approval required for {tool_name}")

    def approve_key(self) -> str:
        return f"approve:{self.token}"

    def cancel_key(self) -> str:
        return f"cancel:{self.token}"

    def approval_message(self) -> str:
        return (
            f"This action needs your approval:\n\n"
            f"<b>{self.description}</b>\n\n"
            f"This cannot be easily undone. Confirm?"
        )


def check_tier(tool_name: str, tool_args: dict, ctx: ConversationContext) -> None:
    if tool_name in TIER_2:
        if not ctx.has_approval(tool_name, tool_args):
            token = ctx.request_approval(tool_name, tool_args, _describe(tool_name, tool_args))
            raise RequiresApprovalError(
                tool_name=tool_name,
                tool_args=tool_args,
                token=token,
                description=_describe(tool_name, tool_args),
            )
        # Approval granted — clear it after use
        ctx.clear_approval()


def _describe(tool_name: str, tool_args: dict) -> str:
    descriptions = {
        "deactivate_n8n_workflow": f"Deactivate n8n workflow: {tool_args.get('workflow_id', '')}",
        "update_shopify_product_status": (
            f"Set Shopify product {tool_args.get('product_id', '')} "
            f"to <b>{tool_args.get('status', '')}</b> on {tool_args.get('store', 'mora')}"
        ),
        "update_odoo_product_active": (
            f"Set Odoo product ID {tool_args.get('product_id', '')} "
            f"active={tool_args.get('active', '')}"
        ),
        "retry_failed_queue_lines": "Retry all failed sync queue lines in Odoo",
    }
    return descriptions.get(tool_name, f"Execute: {tool_name}")
