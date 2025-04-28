import pytest
from workflow.prompts import CARD_CREATOR_PROMPT

def test_prompt_contains_required_sections():
    """Test that the card creator prompt contains all required sections"""
    assert "retrieve_questions tool" in CARD_CREATOR_PROMPT
    assert "categories" in CARD_CREATOR_PROMPT
    assert "chain-of-thought" in CARD_CREATOR_PROMPT

def test_prompt_formatting():
    """Test that the prompt is correctly formatted with required placeholders"""
    assert "{system_time}" in CARD_CREATOR_PROMPT

def test_prompt_instruction_clarity():
    """Test that the prompt instructions are clear and comprehensive"""
    required_instructions = [
        "analyze the couple's preferences",
        "retrieve_questions tool",
        "thematic categories",
        "progression from lighter to deeper"
    ]
    for instruction in required_instructions:
        assert instruction in CARD_CREATOR_PROMPT.lower() 