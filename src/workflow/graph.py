"""Define a graph for all the agents"""


from typing import Literal
import logging
import json

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langgraph.types import Command


from workflow.prompts import SCRIPT_CREATOR_PROMPT, DATE_SCHEDULER_PROMPT, BOX_CREATOR_PROMPT, SUPERVISOR_PROMPT
from workflow.states import LizState, State

TOOLS = []

script_maker = create_react_agent(
    model=ChatOllama(model="mistral:7b"),
    tools=TOOLS,
    prompt=SCRIPT_CREATOR_PROMPT,
    name="script_maker_agent",
)

box_creator = create_react_agent(
    model=ChatOllama(model="mistral:7b"),
    tools=TOOLS,
    prompt=BOX_CREATOR_PROMPT,
    name="box_creator_agent",
)

date_scheduler = create_react_agent(
    model=ChatOllama(model="mistral:7b"),
    tools=TOOLS,
    prompt=DATE_SCHEDULER_PROMPT,
    name="date_scheduler_agent",
)


# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('liz_workflow.log'),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

llm = ChatOllama(model="mistral:7b")
logger = logging.getLogger('liz_workflow')

def supervisor_node(state: State) -> Command[Literal["script_maker_agent", "box_creator_agent", "date_scheduler_agent", "__end__"]]:
    logger.info("Supervisor node processing request")
    messages = [
        {"role": "system", "content": SUPERVISOR_PROMPT},
    ] + state["messages"]
    logger.info(f"Supervisor messages: {messages}")
    
    response = llm.invoke(messages)
    logger.info(f"Supervisor response: {response}")
    logger.info(f"Supervisor response type: {type(response)}")
    
    try:
        content_str = response.content
        parsed_content = json.loads(content_str)
        goto = parsed_content.get("next", "FINISH")
        if goto == "FINISH":
            goto = END
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Error parsing supervisor response: {e}")
        logger.error(f"Response content: {response.content if hasattr(response, 'content') else response}")
        goto = END
    
    logger.info(f"Supervisor routing to: {goto}")
    return Command(goto=goto, update={"next": goto})

def script_maker_node(state: State) -> Command[Literal["supervisor"]]:
    logger.info("Script maker node processing request")
    result = script_maker.invoke(state)
    logger.info("Script maker completed processing")
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="script_maker_agent")
            ]
        },
        goto="supervisor",
    )

def box_creator_node(state: State) -> Command[Literal["supervisor"]]:
    result = box_creator.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="box_creator_agent")
            ]
        },
        goto="supervisor",
    ) 

def date_scheduler_node(state: State) -> Command[Literal["supervisor"]]:
    result = date_scheduler.invoke(state)
    return Command(
        update={
            "messages": [ 
                HumanMessage(content=result["messages"][-1].content, name="date_scheduler_agent")
            ]
        },
        goto="supervisor",
    ) 

# You can also log when the graph is created
logger.info("Creating workflow graph")
graph = StateGraph(LizState)

graph.add_node("supervisor", supervisor_node)
graph.add_node("script_maker_agent", script_maker_node)
graph.add_node("box_creator_agent", box_creator_node)
graph.add_node("date_scheduler_agent", date_scheduler_node)

graph.add_edge("__start__", "supervisor")

# Compile the graph
liz = graph.compile()
logger.info("Workflow graph compiled successfully")


