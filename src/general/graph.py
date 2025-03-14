"""Define a graph for all the agents"""

from datetime import datetime, timezone
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, create_react_agent
from langgraph.types import Command
from langchain_ollama import ChatOllama
from langgraph_supervisor import create_supervisor

from src.config.configuration import Configuration
from src.general.state import InputState, State
from src.tools.tools import TOOLS

from src.config.prompts import SCRIPT_CREATOR_PROMPT,BOX_CREATOR_PROMPT,DATE_SCHEDULER_PROMPT,SUPERVISOR_PROMPT

configuration = Configuration.from_runnable_config()

script_maker = create_react_agent(
    model=ChatOllama(model="mistral:7b"),
    tools=TOOLS,
    prompt=SCRIPT_CREATOR_PROMPT,
)

box_creator = create_react_agent(
    model=ChatOllama(model="mistral:7b"),
    tools=TOOLS,
    prompt=BOX_CREATOR_PROMPT,
)

date_scheduler = create_react_agent(
    model=ChatOllama(model="mistral:7b"),
    tools=TOOLS,
    prompt=DATE_SCHEDULER_PROMPT,
)

workflow = create_supervisor(
    model=ChatOllama(model="mistral:7b"),
    members=[script_maker, box_creator, date_scheduler],
    prompt=SUPERVISOR_PROMPT,
)

liz = workflow.compile()
