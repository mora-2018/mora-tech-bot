import asyncio
import logging
import anthropic
from config import Config
from context import ConversationContext
from prompts import SYSTEM_PROMPT
from safety import check_tier, RequiresApprovalError
from tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

_client = anthropic.AsyncAnthropic(api_key=Config.ANTHROPIC_API_KEY)

MAX_ITERATIONS = 8


async def run_agent_loop(user_message: str, ctx: ConversationContext) -> str:
    # Store message for potential resume after approval
    if user_message != "__resume__":
        ctx.last_message = user_message

    # On resume after approval, re-use stored message
    effective_message = ctx.last_message if user_message == "__resume__" else user_message

    messages = [{"role": "user", "content": effective_message}]

    for iteration in range(MAX_ITERATIONS):
        response = await _client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return _extract_text(response)

        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_args = block.input

                logger.info(f"Tool call: {tool_name}({tool_args})")

                # Safety gate — raises RequiresApprovalError for Tier 2
                check_tier(tool_name, tool_args, ctx)

                # Execute tool in thread (all tools are sync)
                try:
                    result = await asyncio.to_thread(execute_tool, tool_name, tool_args)
                except Exception as e:
                    result = f"Tool error: {e}"
                    logger.error(f"Tool {tool_name} failed: {e}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            break

    # Exhausted iterations — escalate
    logger.warning(f"Max iterations reached for: {effective_message}")
    return (
        "I checked everything I can access and could not pinpoint the exact cause. "
        "I have notified Maleesha with my findings."
    )


def _extract_text(response) -> str:
    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return "Done."
