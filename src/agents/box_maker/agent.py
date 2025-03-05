"""Box maker agent implementation."""

import json
from datetime import datetime, timezone
from json import JSONDecodeError, dumps, loads
from typing import Dict, List, Literal, cast

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END

from src.agents.base.agent import BaseReActAgent
from src.agents.base.state import AgentState
from src.agents.base.utils import load_chat_model
from src.agents.box_maker.prompts import SYSTEM_PROMPT
from src.agents.box_maker.tools import TOOLS
from src.configuration import Configuration


class BoxMakerAgent(BaseReActAgent):
    """Box maker agent for generating box designs."""
    
    def __init__(self):
        """Initialize the box maker agent."""
        super().__init__(
            name="Box Maker Agent",
            description="An agent that generates box designs based on user input.",
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )
    
    async def call_model(self, state: AgentState, config: RunnableConfig) -> Dict[str, List[AIMessage]]:
        """Call the LLM powering the agent.
        
        Args:
            state: The current state of the agent.
            config: The runnable configuration.
            
        Returns:
            A dictionary containing the agent's response messages.
        """
        # Get the model from the configuration if available
        configuration = Configuration.from_runnable_config(config)
        model_name = configuration.model if hasattr(configuration, "model") else self.model
        
        model = load_chat_model(model_name).bind_tools(self.tools)
        system_message = self.system_prompt.format(
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
                "final_design": "Processing with tools..."
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
        try:
            parsed_response = loads(response.content)
            if not isinstance(parsed_response, dict) or "chain_of_thought" not in parsed_response or "final_design" not in parsed_response:
                parsed_response = {
                    "chain_of_thought": "Processing response",
                    "final_design": response.content
                }
        except JSONDecodeError:
            parsed_response = {
                "chain_of_thought": "Processing response",
                "final_design": response.content
            }

        return {
            "messages": [AIMessage(content=dumps(parsed_response))]
        }
    
    def route_model_output(self, state: AgentState) -> str:
        """Determine the next action based on the model's output.
        
        Args:
            state: The current state of the agent.
            
        Returns:
            A string indicating the next action to take.
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(
                f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
            )
        # If there is no tool call, then we finish
        if not last_message.tool_calls:
            return END
        # Otherwise we execute the requested actions
        return "tools" 