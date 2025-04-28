import pytest
import json
import sys
import os
from unittest.mock import patch
from langchain_core.messages import HumanMessage

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Define evaluation criteria
EVALUATION_CRITERIA = """
Rate the card set on:
1. Relevance to requested categories (1-10)
2. Question variety and diversity (1-10) 
3. Progression from light to deep questions (1-10)
4. Overall quality and engagement potential (1-10)

For each criterion, provide a numerical score and brief justification.
"""

# Define test requests covering different scenarios
@pytest.fixture
def sample_requests():
    return [
        {"message": "Create card set about childhood and future dreams", "id": "test-childhood-future"},
        {"message": "I want cards about relationships for newlyweds", "id": "test-newlyweds"},
        {"message": "Make me intimate questions for date night", "id": "test-intimate"},
        {"message": "Questions about personal values and beliefs", "id": "test-values"},
        {"message": "Fun questions for first date", "id": "test-fun-first-date"}
    ]

def evaluate_card_set(judge_llm, card_set, request_message, criteria):
    """Use LLM as judge to evaluate card set quality"""
    evaluation_prompt = f"""
    Evaluate this card set based on the following criteria:
    {criteria}
    
    USER REQUEST: {request_message}
    
    CARD SET:
    Name: {card_set.get('card_set_name')}
    Description: {card_set.get('card_set_description')}
    Categories: {', '.join([cat.get('name') for cat in card_set.get('categories', [])])}
    
    QUESTIONS:
    {chr(10).join([f"- {q}" for q in card_set.get('questions', [])])}
    
    Provide your evaluation as a JSON object with these fields:
    {{
        "relevance_score": <score 1-10>,
        "relevance_justification": "<brief explanation>",
        "variety_score": <score 1-10>,
        "variety_justification": "<brief explanation>",
        "progression_score": <score 1-10>,
        "progression_justification": "<brief explanation>",
        "overall_quality": <score 1-10>,
        "overall_justification": "<brief explanation>"
    }}
    """
    
    evaluation_result = judge_llm.invoke(evaluation_prompt)
    return evaluation_result

def test_card_creator_quality(langfuse_client, sample_requests, test_run_id):
    """Test the quality of card creator outputs using LLM-as-judge via LangFuse"""
    # Import here to avoid errors if not installed
    try:
        from src.workflow.graph import card_creator, llm
        from src.workflow.states import State
    except ImportError:
        pytest.skip("Required modules not available")
    
    for req in sample_requests:
        # Create trace in LangFuse
        trace = langfuse_client.trace(
            name="card_creator_evaluation",
            id=f"{req['id']}-{test_run_id}"  # Unique ID for the trace
        )
        
        # Create state with user request
        state = State(messages=[HumanMessage(content=req["message"])])
        
        # Log the input
        input_gen = trace.generation(
            name="user-request",
            input=req["message"]
        )
        
        # Run the card creator agent
        with patch('src.workflow.graph.retrieve_questions') as mock_retrieve:
            # Mock the retrieve_questions function to return some sample questions
            mock_retrieve.return_value = """
            What was your favorite childhood toy?
            What's your earliest memory?
            What do you hope to achieve in the next 5 years?
            """
            
            response = card_creator.invoke(state)
        
        card_set = response.get("structured_output", {})
        
        # Log the card creator output
        output_gen = trace.generation(
            name="card-creator-output",
            input=req["message"],
            output=str(card_set),
            model="card_creator_agent",
            metadata={
                "card_set_name": card_set.get("card_set_name"),
                "question_count": card_set.get("question_count"),
                "categories": [cat.get("name") for cat in card_set.get("categories", [])]
            }
        )
        
        # Run LLM-as-judge evaluation
        judge_result = evaluate_card_set(llm, card_set, req["message"], EVALUATION_CRITERIA)
        
        # Log the evaluation result
        eval_gen = trace.generation(
            name="card-set-evaluation",
            input=f"Evaluate card set for: {req['message']}",
            output=str(judge_result),
            model="judge_llm"
        )
        
        # Parse scores from judge result
        try:
            scores = json.loads(judge_result) if isinstance(judge_result, str) else judge_result
            
            # Log scores as observations
            trace.observation(name="relevance_score", value=scores.get("relevance_score"))
            trace.observation(name="variety_score", value=scores.get("variety_score"))
            trace.observation(name="progression_score", value=scores.get("progression_score"))
            trace.observation(name="overall_quality", value=scores.get("overall_quality"))
            
            # Evaluate based on threshold scores
            # We use soft assertions here to collect all results rather than stopping at first failure
            relevance_passed = scores.get("relevance_score", 0) >= 7.0
            variety_passed = scores.get("variety_score", 0) >= 7.0
            progression_passed = scores.get("progression_score", 0) >= 7.0
            quality_passed = scores.get("overall_quality", 0) >= 7.5
            
            # Log individual test results
            trace.observation(name="relevance_passed", value=relevance_passed)
            trace.observation(name="variety_passed", value=variety_passed)
            trace.observation(name="progression_passed", value=progression_passed)
            trace.observation(name="quality_passed", value=quality_passed)
            
            # Log overall test result
            overall_passed = all([relevance_passed, variety_passed, progression_passed, quality_passed])
            trace.observation(name="test_passed", value=overall_passed)
            
            # Final assertion for test pass/fail
            assert overall_passed, f"Card set quality below threshold for request: {req['message']}"
            
        except (json.JSONDecodeError, AttributeError) as e:
            # Log raw evaluation if JSON parsing fails
            trace.observation(name="evaluation_raw", value=str(judge_result))
            trace.observation(name="parsing_error", value=str(e))
            trace.observation(name="test_passed", value=False)
            # Test will fail if we can't parse scores
            assert False, f"Failed to parse evaluation scores from judge: {e}"

def test_card_creator_category_relevance(langfuse_client, test_run_id):
    """Test that card creator produces questions relevant to requested categories"""
    # Import here to avoid errors if not installed
    try:
        from src.workflow.graph import card_creator
        from src.workflow.states import State
    except ImportError:
        pytest.skip("Required modules not available")
    
    # Test specific category requests
    category_requests = [
        {"message": "Create questions about childhood only", "id": "test-childhood-only"},
        {"message": "I want only questions about future dreams", "id": "test-future-only"},
        {"message": "Give me questions about personal values", "id": "test-values-only"}
    ]
    
    for req in category_requests:
        trace = langfuse_client.trace(
            name="category_relevance_test",
            id=f"{req['id']}-{test_run_id}"
        )
        
        # Create state with category request
        state = State(messages=[HumanMessage(content=req["message"])])
        
        # Mock retrieve_questions to return relevant results
        with patch('src.workflow.graph.retrieve_questions') as mock_retrieve:
            mock_retrieve.return_value = "Sample question related to the category"
            
            # Get card creator response
            response = card_creator.invoke(state)
        
        card_set = response.get("structured_output", {})
        
        # Log the response
        trace.generation(
            name="category-specific-output",
            input=req["message"],
            output=str(card_set)
        )
        
        # Check that category is reflected in output
        category_request_words = req["message"].lower().split()
        category_words = set()
        
        # Extract categories from the output
        for cat in card_set.get("categories", []):
            category_words.update(cat.get("name", "").lower().split())
        
        # Check for overlap between request and output categories
        common_words = set(category_request_words) & category_words
        has_category_match = len(common_words) > 0
        
        trace.observation(name="has_category_match", value=has_category_match)
        trace.observation(name="request_category_words", value=str(category_request_words))
        trace.observation(name="response_category_words", value=str(category_words))
        trace.observation(name="common_words", value=str(common_words))
        
        assert has_category_match, f"Categories in output don't match request: {req['message']}" 