"""Base ReAct agent implementation.

This module provides a base class for ReAct agents that can be extended
for different specialized purposes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, Type, TypeVar, cast

from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph


from src.agents.base.state import AgentState, InputState
from src.configuration import Configuration


class BaseReActAgent(ABC):
    """Base class for ReAct agents.
    
    This class provides the common structure and functionality for all ReAct agents.
    Specialized agents should extend this class and implement the abstract methods.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        tools: List[Callable[..., Any]],
        system_prompt: str,
        model: str = "anthropic/claude-3-5-sonnet-20240620",
    ):
        """Initialize the ReAct agent.
        
        Args:
            name: The name of the agent.
            description: A description of the agent's purpose.
            tools: A list of tools available to the agent.
            system_prompt: The system prompt for the agent.
            model: The model to use for the agent.
        """
        self.name = name
        self.description = description
        self.tools = tools
        self.system_prompt = system_prompt
        self.model = model
        self.graph = self._build_graph()
    
    @abstractmethod
    async def call_model(self, state: AgentState, config: RunnableConfig) -> Dict[str, List[AIMessage]]:
        """Call the LLM powering the agent.
        
        Args:
            state: The current state of the agent.
            config: The runnable configuration.
            
        Returns:
            A dictionary containing the agent's response messages.
        """
        pass
    
    @abstractmethod
    def route_model_output(self, state: AgentState) -> str:
        """Determine the next action based on the model's output.
        
        Args:
            state: The current state of the agent.
            
        Returns:
            A string indicating the next action to take.
        """
        pass
    
    def _build_graph(self) -> StateGraph:
        """Build the agent's graph.
        
        Returns:
            The compiled state graph for the agent.
        """
        # Define the nodes
        def call_model_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
            """Node for calling the model."""
            return self.call_model(state, config)
        
        def route_node(state: AgentState) -> str:
            """Node for routing the model output."""
            return self.route_model_output(state)
        
        def tools_node(state: AgentState, config: RunnableConfig) -> Dict[str, List[AIMessage]]:
            """Execute the tool calls in the last message."""
            last_message = state.messages[-1]
            if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
                return {"messages": state.messages}
            
            # Process each tool call
            new_messages = list(state.messages)
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.name
                tool_args = tool_call.args
                
                # Find the matching tool
                for tool in self.tools:
                    if tool.__name__ == tool_name:
                        try:
                            # Execute the tool
                            tool_result = tool(**tool_args)
                            # Add the tool result as a new message
                            new_messages.append(
                                AIMessage(
                                    content=f"Tool {tool_name} returned: {tool_result}",
                                    tool_call_id=tool_call.id
                                )
                            )
                        except Exception as e:
                            # Handle tool execution errors
                            new_messages.append(
                                AIMessage(
                                    content=f"Error executing tool {tool_name}: {str(e)}",
                                    tool_call_id=tool_call.id
                                )
                            )
                        break
            
            return {"messages": new_messages}
        
        # Build the graph
        builder = StateGraph(AgentState, input=InputState, config_schema=Configuration)
        
        # Add nodes
        builder.add_node("call_model", call_model_node)
        builder.add_node("tools", tools_node)
        
        # Set the entrypoint
        builder.set_entry_point("call_model")
        
        # Add conditional logic
        builder.add_conditional_edges("call_model", route_node, {
            "tools": "tools",
            END: END
        })
        
        # Add edge from tools back to call_model
        builder.add_edge("tools", "call_model")
        
        # Compile the graph
        graph = builder.compile()
        graph.name = self.name
        
        return graph
    
    async def invoke(self, messages: Sequence[AnyMessage], config: Optional[RunnableConfig] = None) -> AgentState:
        """Invoke the agent with the given messages.
        
        Args:
            messages: The input messages.
            config: The runnable configuration.
            
        Returns:
            The final state of the agent.
        """
        input_state = InputState(messages=messages)
        return await self.graph.ainvoke(input_state, config) 