import secrets
import time
from dataclasses import dataclass, field
from typing import Optional

_contexts: dict[int, "ConversationContext"] = {}

# Safety constants
RATE_LIMIT_MAX = 5          # max messages per chat per hour
RATE_LIMIT_WINDOW = 3600    # 1 hour in seconds
CIRCUIT_BREAKER_MAX = 3     # crashes before circuit opens
CIRCUIT_BREAKER_WINDOW = 600  # 10 minutes in seconds


@dataclass
class PendingApproval:
    token: str
    tool_name: str
    tool_args: dict
    description: str
    resume_message: str


@dataclass
class ConversationContext:
    chat_id: int
    pending_approval: Optional[PendingApproval] = None
    approved_tokens: set[str] = field(default_factory=set)
    last_message: str = ""

    # Rate limiting
    _message_timestamps: list[float] = field(default_factory=list)

    # Circuit breaker
    _crash_timestamps: list[float] = field(default_factory=list)
    _circuit_open: bool = False

    # --- Approval ---

    def request_approval(self, tool_name: str, tool_args: dict, description: str) -> str:
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

    # --- Rate limiting ---

    def check_rate_limit(self) -> tuple[bool, int]:
        """Returns (allowed, seconds_until_reset)."""
        now = time.time()
        cutoff = now - RATE_LIMIT_WINDOW
        self._message_timestamps = [t for t in self._message_timestamps if t > cutoff]
        if len(self._message_timestamps) >= RATE_LIMIT_MAX:
            reset_in = int(self._message_timestamps[0] + RATE_LIMIT_WINDOW - now)
            return False, max(reset_in, 1)
        self._message_timestamps.append(now)
        return True, 0

    # --- Circuit breaker ---

    def record_crash(self) -> bool:
        """Records a crash. Returns True if circuit just opened."""
        now = time.time()
        cutoff = now - CIRCUIT_BREAKER_WINDOW
        self._crash_timestamps = [t for t in self._crash_timestamps if t > cutoff]
        self._crash_timestamps.append(now)
        if len(self._crash_timestamps) >= CIRCUIT_BREAKER_MAX:
            self._circuit_open = True
            return True
        return False

    def is_circuit_open(self) -> bool:
        if not self._circuit_open:
            return False
        # Auto-reset after window passes
        now = time.time()
        cutoff = now - CIRCUIT_BREAKER_WINDOW
        recent = [t for t in self._crash_timestamps if t > cutoff]
        if len(recent) < CIRCUIT_BREAKER_MAX:
            self._circuit_open = False
            self._crash_timestamps = recent
            return False
        return True


def get_context(chat_id: int) -> ConversationContext:
    if chat_id not in _contexts:
        _contexts[chat_id] = ConversationContext(chat_id=chat_id)
    return _contexts[chat_id]


def clear_context(chat_id: int) -> None:
    _contexts.pop(chat_id, None)
