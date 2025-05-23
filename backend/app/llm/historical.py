from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, AIMessage
from typing import List, Dict

#####Class for memory object
class InMemoryHistory(BaseChatMessageHistory):
    """Historial de mensajes en memoria."""
    messages: List[BaseMessage] = []

    def __init__(self):
        self.messages = []

    def add_messages(self, messages: List[BaseMessage]) -> None:
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages = []

# Almacén global (fuera del modelo)
_memory_store: Dict[str, InMemoryHistory] = {}

def get_by_session_id(session_id: str) -> InMemoryHistory:
    if session_id not in _memory_store:
        _memory_store[session_id] = InMemoryHistory()
    return _memory_store[session_id]