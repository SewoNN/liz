"""Main graph module for the LangGraph CLI.

This module exposes the supervisor graph for the LangGraph CLI.
"""

from typing import Dict, List, Literal, Optional, Sequence, cast

from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph

from src.configuration import Configuration
from src.supervisor import SupervisorAgent, SupervisorState, InputState

# Create the supervisor agent
supervisor = SupervisorAgent()

# Update the graph to use the configuration
graph = supervisor.graph.with_config(config_schema=Configuration) 