import pytest
import os
from unittest.mock import MagicMock, patch
import logging
from datetime import datetime

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_card_creator')

# Create a fixture for LangFuse instance
@pytest.fixture(scope="session")
def langfuse_client():
    try:
        # Import only if available
        from langfuse import Langfuse
        
        # Use environment variables or test keys
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "test-api-key")
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "test-public-key")
        host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
        
        # For testing, we can either:
        # 1. Use a real LangFuse instance with test credentials
        # 2. Mock the LangFuse client
        
        # Option 1: Real client with test project
        if os.environ.get("USE_REAL_LANGFUSE") == "true":
            return Langfuse(secret_key=secret_key, public_key=public_key, host=host)
        
        # Option 2: Mock client
        else:
            mock_client = MagicMock()
            mock_trace = MagicMock()
            mock_generation = MagicMock()
            mock_observation = MagicMock()
            
            mock_client.trace.return_value = mock_trace
            mock_trace.generation.return_value = mock_generation
            mock_trace.observation.return_value = mock_observation
            
            return mock_client
    except ImportError:
        # If LangFuse isn't installed, return mock
        mock_client = MagicMock()
        mock_client.trace.return_value.generation.return_value = MagicMock()
        mock_client.trace.return_value.observation.return_value = MagicMock()
        return mock_client

# Create a fixture for test run ID to group related test runs
@pytest.fixture(scope="session")
def test_run_id():
    return f"test-run-{datetime.now().strftime('%Y%m%d%H%M%S')}"

# Create fixtures for common test data
@pytest.fixture
def sample_card_set():
    return {
        "card_set_name": "Test Card Set",
        "card_set_description": "A test card set for unit testing",
        "question_count": 3,
        "categories": [
            {"name": "Test Category", "description": "Test category description"}
        ],
        "questions": [
            "Test question 1?",
            "Test question 2?",
            "Test question 3?"
        ]
    }

# Mock for QdrantClient
@pytest.fixture
def mock_qdrant_client():
    with patch('workflow.graph.QdrantClient') as mock_client:
        client_instance = MagicMock()
        mock_client.return_value = client_instance
        
        # Setup mock search results
        mock_result = [
            MagicMock(payload={"question": "What was your favorite childhood toy?"}),
            MagicMock(payload={"question": "What's your earliest memory?"})
        ]
        client_instance.search.return_value = mock_result
        yield client_instance

# Mock for OllamaEmbeddings
@pytest.fixture
def mock_embeddings():
    with patch('workflow.graph.OllamaEmbeddings') as mock_embed:
        embed_instance = MagicMock()
        mock_embed.return_value = embed_instance
        embed_instance.embed_query.return_value = [0.1, 0.2, 0.3]  # Mock embedding vector
        yield embed_instance 