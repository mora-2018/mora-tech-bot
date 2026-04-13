import secrets
from dataclasses import dataclass, field
from typing import Optional

_contexts: dict[int, "ConversationContext"] = {}


@dataclass
class PendingApproval:
    token: str
    tool_name: str
    tool_args: dict
    description: str
    resume_message: str  # the original user message to resume with


@dataclass
class ConversationContext:
    chat_id: int
    pending_approval: Optional[PendingApproval] = None
    approved_tokens: set[str] = field(default_factory=set)
    # Stores the last user message for resume after approval
    last_message: str = ""

    def request_approval(
        self,
        tool_name: str,
        tool_args: dict,
        description: str,
    ) -> str:
        token = secrets.token_urlsafe(12)
        self.pending_approval = PendingApproval(
            token=token,
            tool_name=tool_name,
            tool_args=tool_args,
            description=description,
            resume_message=self.last_message,
        )
        return token

    def grant_approval(self, token: str) -> bool:
        if self.pending_approval and self.pending_approval.token == token:
            self.approved_tokens.add(token)
            return True
        return False

    def has_approval(self, tool_name: str, tool_args: dict) -> bool:
        if not self.pending_approval:
            return False
        if self.pending_approval.tool_name != tool_name:
            return False
        if self.pending_approval.token not in self.approved_tokens:
            return False
        return True

    def clear_approval(self) -> None:
        self.pending_approval = None
        self.approved_tokens.clear()


def get_context(chat_id: int) -> ConversationContext:
    if chat_id not in _contexts:
        _contexts[chat_id] = ConversationContext(chat_id=chat_id)
    return _contexts[chat_id]


def clear_context(chat_id: int) -> None:
    _contexts.pop(chat_id, None)
