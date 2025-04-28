import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from langchain_core.messages import HumanMessage

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.workflow.graph import supervisor_node, SupervisorResponse
from src.workflow.states import State

@pytest.fixture
def mock_supervisor_llm():
    with patch('src.workflow.graph.ChatOllama') as mock_chat:
        llm_instance = MagicMock()
        mock_chat.return_value.with_structured_output.return_value = llm_instance
        
        # Create a mock response that routes to card_creator_agent
        structured_response = SupervisorResponse(
            chain_of_thought="User is asking for questions, so card creator is best",
            next="card_creator_agent"
        )
        
        llm_instance.invoke.return_value = structured_response
        yield mock_chat

def test_supervisor_routes_to_card_creator(mock_supervisor_llm):
    """Test that supervisor correctly routes to card creator for relevant requests"""
    # Initialize test state with user message about cards
    state = State(messages=[HumanMessage(content="I need questions about childhood")])
    
    # Run the supervisor node
    result = supervisor_node(state)
    
    # Verify routing to card_creator_agent
    assert result.goto == "card_creator_agent"
    assert result.update["next"] == "card_creator_agent"

def test_supervisor_doesnt_route_to_card_creator_for_unrelated_requests(mock_supervisor_llm):
    """Test that supervisor doesn't route to card creator for unrelated requests"""
    # Override the mock to route elsewhere
    mock_supervisor_llm.return_value.with_structured_output.return_value.invoke.return_value = \
        SupervisorResponse(
            chain_of_thought="User is asking for a script, not questions",
            next="script_maker_agent"
        )
    
    # Initialize test state with user message about scripts
    state = State(messages=[HumanMessage(content="Create a romantic script for us")])
    
    # Run the supervisor node
    result = supervisor_node(state)
    
    # Verify not routing to card_creator_agent
    assert result.goto != "card_creator_agent"
    assert result.update["next"] != "card_creator_agent" 