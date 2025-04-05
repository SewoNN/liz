"""Define a graph for all the agents"""


from typing import Literal
import logging
import json

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langgraph.types import Command
from langchain.tools.retriever import create_retriever_tool
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from typing import List, Dict, Any
from workflow.prompts import SCRIPT_CREATOR_PROMPT, DATE_SCHEDULER_PROMPT, BOX_CREATOR_PROMPT, SUPERVISOR_PROMPT, CARD_CREATOR_PROMPT
from workflow.states import LizState, State
from pydantic import BaseModel, Field


class CardCreatorStructuredOutput(BaseModel):
    chain_of_thought: str = Field(description="The chain of thought process used to create the card set")
    card_set_name: str = Field(description="The name of the card set")
    card_set_description: str = Field(description="A description of the card set")
    question_count: int = Field(description="The number of questions in the card set")
    categories: List[Dict[str, Any]] = Field(description="The categories of questions in the card set")
    questions: List[str] = Field(description="The questions in the card set")


class SupervisorResponse(BaseModel):
    chain_of_thought: str = Field(description="The chain of thought process used to determine the next agent to call")
    next: Literal["script_maker_agent", "box_creator_agent", "date_scheduler_agent", "card_creator_agent", "FINISH"] = Field(description="The next agent to call")


childhood_questions_retriever = QdrantVectorStore(client=QdrantClient(url="http://localhost:6333"),
                                collection_name="childhood", embedding=OllamaEmbeddings(model="nomic-embed-text")).as_retriever()

retriever_tool = create_retriever_tool(
    childhood_questions_retriever,
    "retrieve_childhood_questions",
    "Search and return questions on the topic of personal and childhood memories"
)

card_creator_tools = [retriever_tool]
TOOLS = []

model_version = "deepseek-r1:14b"
llm = ChatOllama(model=model_version)


script_maker = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SCRIPT_CREATOR_PROMPT,
    name="script_maker_agent",
)

box_creator = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=BOX_CREATOR_PROMPT,
    name="box_creator_agent",
)

date_scheduler = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=DATE_SCHEDULER_PROMPT,
    name="date_scheduler_agent",
)

card_creator = create_react_agent(
    model=llm,
    tools=card_creator_tools,
    prompt=CARD_CREATOR_PROMPT,
    name="card_game_creator_agent",
    response_format=CardCreatorStructuredOutput,
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

logger = logging.getLogger('liz_workflow')

def supervisor_node(state: State) -> Command[Literal["script_maker_agent", "box_creator_agent", "date_scheduler_agent", "card_creator_agent", "__end__"]]:
    logger.info("Supervisor node processing request")
    messages = [
        {"role": "system", "content": SUPERVISOR_PROMPT},
    ] + state["messages"]
    logger.info(f"Supervisor messages: {messages}")
    
    response = ChatOllama(model=model_version).with_structured_output(SupervisorResponse).invoke(messages)
    logger.info(f"Supervisor response: {response}")
    logger.info(f"Supervisor response type: {type(response)}")
    
    try:
        goto = response.next
        if goto == "FINISH":
            goto = END
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Error parsing supervisor response: {e}")
        logger.error(f"Response: {response}")
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

def card_creator_node(state: State) -> Command[Literal["supervisor"]]:
    result = card_creator.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="card_creator_agent")
            ],
            "structured_output": result.get("structured_response", {})
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
graph.add_node("card_creator_agent", card_creator_node)

graph.add_edge("__start__", "supervisor")

# Compile the graph
liz = graph.compile()
logger.info("Workflow graph compiled successfully")


