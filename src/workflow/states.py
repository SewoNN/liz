from typing import Dict, TypedDict, Any, Literal

from langgraph.graph import MessagesState

class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["script_maker_agent", "box_creator_agent", "date_scheduler_agent", "FINISH"]


class State(MessagesState):
    next: str

class LizState(State): 
    last_agent: str
    context: str
    routing_decision: Dict[str, Any]
