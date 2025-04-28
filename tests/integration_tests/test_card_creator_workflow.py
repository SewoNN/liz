import pytest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from langchain_core.messages import HumanMessage

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.workflow.graph import card_creator
from src.workflow.states import State

@pytest.fixture
def mock_retrieve_questions():
    with patch('src.workflow.graph.retrieve_questions') as mock_retrieve:
        mock_retrieve.return_value = """
        What was your favorite childhood toy?
        What's your earliest memory?
        Who was your favorite teacher?
        """
        yield mock_retrieve

@pytest.fixture
def mock_llm():
    with patch('src.workflow.graph.ChatOllama') as mock_chat:
        llm_instance = MagicMock()
        mock_chat.return_value = llm_instance
        
        # Setup mock LLM response
        structured_output = {
            "chain_of_thought": "Creating cards focused on childhood...",
            "card_set_name": "Childhood Memories",
            "card_set_description": "Questions about growing up",
            "question_count": 3,
            "categories": [{"name": "Early Years", "description": "Questions about early childhood"}],
            "questions": [
                "What was your favorite childhood toy?",
                "What's your earliest memory?",
                "Who was your favorite teacher?"
            ]
        }
        
        llm_instance.invoke.return_value = structured_output
        yield mock_chat

def test_card_creator_workflow_integration(mock_retrieve_questions, mock_llm):
    """Test the full card creator workflow with mocked dependencies"""
    # Initialize test state with user message
    state = State(messages=[HumanMessage(content="Create cards about childhood memories")])
    
    # Invoke the card creator
    result = card_creator.invoke(state)
    
    # Verify that retrieve_questions was called
    mock_retrieve_questions.assert_called_once()
    
    # Check the output structure
    assert "messages" in result
    assert "structured_output" in result or "structured_response" in result
    
    # If structured_output is available, validate its content
    structured_content = result.get("structured_output") or result.get("structured_response", {})
    assert "card_set_name" in structured_content
    assert "questions" in structured_content
    assert len(structured_content["questions"]) > 0

def test_card_creator_handles_retrieve_questions_failure():
    """Test how card creator handles failures in the retrieve_questions tool"""
    with patch('src.workflow.graph.retrieve_questions', side_effect=Exception("Tool failure")):
        with patch('src.workflow.graph.ChatOllama') as mock_chat:
            # Mock the LLM to return a valid response even when tool fails
            llm_instance = MagicMock()
            mock_chat.return_value = llm_instance
            
            structured_output = {
                "chain_of_thought": "Creating cards even though tool failed...",
                "card_set_name": "Basic Questions",
                "card_set_description": "Fallback questions",
                "question_count": 2,
                "categories": [{"name": "General", "description": "General questions"}],
                "questions": [
                    "What do you enjoy doing in your free time?",
                    "What's something you're looking forward to?"
                ]
            }
            
            llm_instance.invoke.return_value = structured_output
            
            state = State(messages=[HumanMessage(content="Create cards about childhood memories")])
            
            # Should still work even if retrieve_questions fails
            result = card_creator.invoke(state)
            
            # Should still produce some output
            assert "messages" in result
</rewritten_file> 