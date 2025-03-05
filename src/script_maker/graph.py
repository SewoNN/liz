"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from json import JSONDecodeError, loads, dumps
from datetime import datetime, timezone
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from script_maker.configuration import Configuration
from script_maker.state import InputState, State
from script_maker.tools import TOOLS
from script_maker.utils import load_chat_model

# Define the function that calls the model


async def call_model(
    state: State, config: RunnableConfig
) -> Dict[str, List[AIMessage]]:
    """Call the LLM powering our "agent"."""
    configuration = Configuration.from_runnable_config(config)
    model = load_chat_model(configuration.model).bind_tools(TOOLS)
    system_message = configuration.system_prompt.format(
        system_time=datetime.now(tz=timezone.utc).isoformat()
    )

    response = cast(
        AIMessage,
        await model.ainvoke(
            [{"role": "system", "content": system_message}, *state.messages], config
        ),
    )

    # If there are tool calls, wrap the response in our expected JSON structure
    if response.tool_calls:
        structured_response = {
            "chain_of_thought": "Using tool to gather information",
            "final_script": "Processing with tools..."
        }
        # Create a new AIMessage that includes both the tool calls and our structured content
        return {
            "messages": [
                AIMessage(
                    content=dumps(structured_response),
                    tool_calls=response.tool_calls
                )
            ]
        }

    # For regular responses, ensure they're properly structured
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print("--------------------------------")
    print(response.content)
    print(response)
    try:
        parsed_response = loads(response.content)
        if not isinstance(parsed_response, dict) or "chain_of_thought" not in parsed_response or "final_script" not in parsed_response:
            parsed_response = {
                "chain_of_thought": "Processing response",
                "final_script": response.content
            }
    except JSONDecodeError:
        parsed_response = {
            "chain_of_thought": "Processing response",
            "final_script": response.content
        }

    return {
        "messages": [AIMessage(content=dumps(parsed_response))]
    }



def get_user_details(state: State) -> Dict[str, List[AIMessage]]:
    """Validate if the user provided required details in their input.
    
    Returns:
        Dict with either an error message or the original input state.
    """
    required_details = ["environment", "tone", "setting", "theme", "unique preferences", "names"]
    last_message = state.messages[-1].content.lower()
    
    missing = [detail for detail in required_details if detail not in last_message]

    # Only send message if ALL details are missing
    if len(missing) == len(required_details):
        error_response = {
            "chain_of_thought": "User has not provided any required details. Requesting more information.",
            "final_script": f"Before proceeding, I need more details about: {', '.join(missing)}. Please provide this information."
        }
        return {
            "messages": [AIMessage(content=dumps(error_response))]
        }
    
    # If at least one detail is provided, pass through to the model
    return {"messages": state.messages}

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the nodes we will cycle between
builder.add_node("validate_input", get_user_details)
builder.add_node("call_model", call_model)
builder.add_node("tools", ToolNode(TOOLS))

# Set the entrypoint as validate_input
builder.add_edge("__start__", "validate_input")

def route_validation(state: State) -> Literal["__end__", "call_model"]:
    """Route based on validation results"""
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        return "call_model"
    
    # If the last message is from the validation node (contains error message)
    if "Before proceeding, I need more details about:" in last_message.content:
        return "__end__"
    
    return "call_model"

# Add conditional edges for the validation node
builder.add_conditional_edges(
    "validate_input",
    route_validation
)

def route_model_output(state: State) -> Literal["__end__", "tools"]:
    """Determine the next node based on the model's output.

    This function checks if the model's last message contains tool calls.

    Args:
        state (State): The current state of the conversation.

    Returns:
        str: The name of the next node to call ("__end__" or "tools").
    """
    last_message = state.messages[-1]
    if not isinstance(last_message, AIMessage):
        raise ValueError(
            f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
        )
    # If there is no tool call, then we finish
    if not last_message.tool_calls:
        return "__end__"
    # Otherwise we execute the requested actions
    return "tools"

# Add a conditional edge to determine the next step after `call_model`
builder.add_conditional_edges(
    "call_model",
    route_model_output,
)

# Add a normal edge from `tools` to `call_model`
builder.add_edge("tools", "call_model")

# Compile the builder into an executable graph
# You can customize this by adding interrupt points for state updates
graph = builder.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
)
graph.name = "ReAct Agent"  # This customizes the name in LangSmith
