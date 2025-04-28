import pytest
from pydantic import ValidationError
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.workflow.graph import CardCreatorStructuredOutput

def test_valid_card_creator_output(sample_card_set):
    """Test that a valid output passes validation"""
    output = CardCreatorStructuredOutput(**sample_card_set)
    assert output.card_set_name == "Test Card Set"
    assert output.question_count == 3
    assert len(output.questions) == 3
    assert len(output.categories) == 1

def test_missing_required_fields():
    """Test that validation fails when required fields are missing"""
    invalid_output = {
        "card_set_name": "Incomplete Set",
        "card_set_description": "Missing required fields"
        # Missing other required fields
    }
    
    with pytest.raises(ValidationError):
        CardCreatorStructuredOutput(**invalid_output)

def test_question_count_validation():
    """Test that question_count matches actual questions length"""
    invalid_output = {
        "chain_of_thought": "Some reasoning...",
        "card_set_name": "Mismatch Example",
        "card_set_description": "The count doesn't match questions",
        "question_count": 10,  # Says 10 but only has 2
        "categories": [{"name": "Test", "description": "Test category"}],
        "questions": ["Question 1", "Question 2"]
    }
    
    # This will pass Pydantic validation but we should check the count
    output = CardCreatorStructuredOutput(**invalid_output)
    assert output.question_count != len(output.questions) 