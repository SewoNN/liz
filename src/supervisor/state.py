"""Define the state structures for the supervisor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from typing_extensions import Annotated


@dataclass
class InputState:
    """Defines the input state for the supervisor, representing a narrower interface to the outside world.

    This class is used to define the initial state and structure of incoming data.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )
    """
    Messages tracking the primary execution state of the supervisor.
    """


@dataclass
class SupervisorState(InputState):
    """Represents the complete state of the supervisor, extending InputState with additional attributes.

    This class can be used to store any information needed throughout the supervisor's lifecycle.
    """

    is_last_step: IsLastStep = field(default=False)
    """
    Indicates whether the current step is the last one before the graph raises an error.
    """

    metadata: Dict[str, Any] = field(default_factory=dict)
    """
    Additional metadata that can be used to store information about the supervisor's state.
    """

    artifacts: Dict[str, Any] = field(default_factory=dict)
    """
    Artifacts produced by the supervisor during execution.
    """
    
    agent_states: Dict[str, Any] = field(default_factory=dict)
    """
    States of the individual agents managed by the supervisor.
    """
    
    current_agent: Optional[str] = field(default=None)
    """
    The name of the currently active agent.
    """
    
    completed_agents: List[str] = field(default_factory=list)
    """
    List of agents that have completed their tasks.
    """ 