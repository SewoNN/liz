from typing import Dict, TypedDict, Any, Literal, Optional

from langgraph.graph import MessagesState

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["script_maker_agent", "box_creator_agent", "date_scheduler_agent", "card_creator_agent", "FINISH"]


class State(MessagesState):
    next: str

class LizState(State): 
    last_agent: str
    routing_decision: Dict[str, Any]
    structured_output: Optional[Dict[str, Any]] = None
