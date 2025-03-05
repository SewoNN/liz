"""Supervisor agent implementation."""

from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional, Sequence, cast

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

from src.agents.base.utils import load_chat_model
from src.agents.box_maker import BoxMakerAgent
from src.agents.research import ResearchAgent
from src.agents.script_maker import ScriptMakerAgent
from src.configuration import Configuration
from src.supervisor.prompts import SYSTEM_PROMPT
from src.supervisor.state import InputState, SupervisorState


class SupervisorAgent:
    """Supervisor agent for coordinating multiple ReAct agents."""
    
    def __init__(self, model: str = "anthropic/claude-3-5-sonnet-20240620"):
        """Initialize the supervisor agent.
        
        Args:
            model: The model to use for the supervisor.
        """
        self.name = "Supervisor Agent"
        self.model = model
        self.system_prompt = SYSTEM_PROMPT
        
        # Initialize the specialized agents
        self.script_maker = ScriptMakerAgent()
        self.box_maker = BoxMakerAgent()
        self.research = ResearchAgent()
        
        # Build the graph
        self.graph = self._build_graph()
    
    async def call_supervisor(self, state: SupervisorState, config: RunnableConfig) -> Dict[str, List[AIMessage]]:
        """Call the LLM powering the supervisor.
        
        Args:
            state: The current state of the supervisor.
            config: The runnable configuration.
            
        Returns:
            A dictionary containing the supervisor's response messages.
        """
        # Get the model from the configuration if available
        configuration = Configuration.from_runnable_config(config)
        model_name = configuration.model if hasattr(configuration, "model") else self.model
        
        model = load_chat_model(model_name)
        system_message = self.system_prompt.format(
            system_time=datetime.now(tz=timezone.utc).isoformat()
        )

        response = cast(
            AIMessage,
            await model.ainvoke(
                [{"role": "system", "content": system_message}, *state.messages], config
            ),
        )

        return {"messages": [response]}
    
    def route_supervisor_output(self, state: SupervisorState) -> str:
        """Determine which agent to route to based on the supervisor's output.
        
        Args:
            state: The current state of the supervisor.
            
        Returns:
            A string indicating the next action to take.
        """
        last_message = state.messages[-1]
        if not isinstance(last_message, AIMessage):
            raise ValueError(
                f"Expected AIMessage in output edges, but got {type(last_message).__name__}"
            )
        
        content = last_message.content.lower()
        
        # Simple keyword-based routing
        if "script" in content or "story" in content or "creative" in content:
            return "script_maker"
        elif "box" in content or "container" in content or "package" in content:
            return "box_maker"
        elif "research" in content or "information" in content or "data" in content:
            return "research"
        else:
            # If no clear match, default to ending the conversation
            return END
    
    async def call_script_maker(self, state: SupervisorState, config: RunnableConfig) -> Dict[str, SupervisorState]:
        """Call the script maker agent.
        
        Args:
            state: The current state of the supervisor.
            config: The runnable configuration.
            
        Returns:
            A dictionary containing the updated supervisor state.
        """
        # Extract the last message from the supervisor to pass to the agent
        last_message = state.messages[-1]
        
        # Call the script maker agent
        agent_state = await self.script_maker.invoke([last_message], config)
        
        # Update the supervisor state with the agent's response
        new_state = SupervisorState(
            messages=list(state.messages) + list(agent_state.messages[-1:]),
            current_agent="script_maker",
            completed_agents=state.completed_agents + ["script_maker"],
        )
        
        return {"state": new_state}
    
    async def call_box_maker(self, state: SupervisorState, config: RunnableConfig) -> Dict[str, SupervisorState]:
        """Call the box maker agent.
        
        Args:
            state: The current state of the supervisor.
            config: The runnable configuration.
            
        Returns:
            A dictionary containing the updated supervisor state.
        """
        # Extract the last message from the supervisor to pass to the agent
        last_message = state.messages[-1]
        
        # Call the box maker agent
        agent_state = await self.box_maker.invoke([last_message], config)
        
        # Update the supervisor state with the agent's response
        new_state = SupervisorState(
            messages=list(state.messages) + list(agent_state.messages[-1:]),
            current_agent="box_maker",
            completed_agents=state.completed_agents + ["box_maker"],
        )
        
        return {"state": new_state}
    
    async def call_research(self, state: SupervisorState, config: RunnableConfig) -> Dict[str, SupervisorState]:
        """Call the research agent.
        
        Args:
            state: The current state of the supervisor.
            config: The runnable configuration.
            
        Returns:
            A dictionary containing the updated supervisor state.
        """
        # Extract the last message from the supervisor to pass to the agent
        last_message = state.messages[-1]
        
        # Call the research agent
        agent_state = await self.research.invoke([last_message], config)
        
        # Update the supervisor state with the agent's response
        new_state = SupervisorState(
            messages=list(state.messages) + list(agent_state.messages[-1:]),
            current_agent="research",
            completed_agents=state.completed_agents + ["research"],
        )
        
        return {"state": new_state}
    
    def _build_graph(self) -> StateGraph:
        """Build the supervisor's graph.
        
        Returns:
            The compiled state graph for the supervisor.
        """
        # Define the nodes
        def call_supervisor_node(state: SupervisorState, config: RunnableConfig) -> Dict[str, List[AIMessage]]:
            """Node for calling the supervisor."""
            return self.call_supervisor(state, config)
        
        def route_node(state: SupervisorState) -> str:
            """Node for routing the supervisor output."""
            return self.route_supervisor_output(state)
        
        def script_maker_node(state: SupervisorState, config: RunnableConfig) -> Dict[str, SupervisorState]:
            """Node for calling the script maker agent."""
            return self.call_script_maker(state, config)
        
        def box_maker_node(state: SupervisorState, config: RunnableConfig) -> Dict[str, SupervisorState]:
            """Node for calling the box maker agent."""
            return self.call_box_maker(state, config)
        
        def research_node(state: SupervisorState, config: RunnableConfig) -> Dict[str, SupervisorState]:
            """Node for calling the research agent."""
            return self.call_research(state, config)
        
        # Build the graph
        builder = StateGraph(SupervisorState, input=InputState)
        
        # Add nodes
        builder.add_node("call_supervisor", call_supervisor_node)
        builder.add_node("script_maker", script_maker_node)
        builder.add_node("box_maker", box_maker_node)
        builder.add_node("research", research_node)
        
        # Set the entrypoint
        builder.set_entry_point("call_supervisor")
        
        # Add conditional logic
        builder.add_conditional_edges("call_supervisor", route_node, {
            "script_maker": "script_maker",
            "box_maker": "box_maker",
            "research": "research",
            END: END
        })
        
        # Add edges from agents to end
        builder.add_edge("script_maker", END)
        builder.add_edge("box_maker", END)
        builder.add_edge("research", END)
        
        # Compile the graph
        graph = builder.compile()
        graph.name = self.name
        
        return graph
    
    async def invoke(self, messages: Sequence[AnyMessage], config: Optional[RunnableConfig] = None) -> SupervisorState:
        """Invoke the supervisor with the given messages.
        
        Args:
            messages: The input messages.
            config: The runnable configuration.
            
        Returns:
            The final state of the supervisor.
        """
        input_state = InputState(messages=messages)
        return await self.graph.ainvoke(input_state, config) 