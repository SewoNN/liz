import pytest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.workflow.graph import retrieve_questions

def test_retrieve_questions_success(mock_qdrant_client, mock_embeddings):
    """Test successful question retrieval"""
    # Setup mock QdrantClient and OllamaEmbeddings from fixtures
    
    result = retrieve_questions({"category": "childhood"})
    
    # Check if the result contains the expected questions
    assert "What was your favorite childhood toy?" in result
    assert "What's your earliest memory?" in result

def test_retrieve_questions_empty_results(mock_qdrant_client, mock_embeddings):
    """Test behavior when no questions are found"""
    # Override the mock to return empty results
    mock_qdrant_client.search.return_value = []
    
    result = retrieve_questions({"category": "nonexistent"})
    assert "No relevant questions found" in result

def test_retrieve_questions_error_handling(mock_qdrant_client, mock_embeddings):
    """Test error handling in the retrieve_questions function"""
    # Override the mock to raise an exception
    mock_qdrant_client.search.side_effect = Exception("Connection error")
    
    result = retrieve_questions({"category": "childhood"})
    assert "encountered an error" in result 