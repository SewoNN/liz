"""Utility functions for the base agent."""

from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI


def load_chat_model(model_name: str, temperature: float = 0.0) -> ChatAnthropic | ChatOpenAI:
    """Load a chat model based on the model name.
    
    Args:
        model_name: The name of the model to load, in the format "provider/model-name".
        temperature: The temperature to use for the model.
        
    Returns:
        The loaded chat model.
        
    Raises:
        ValueError: If the model provider is not supported.
    """
    provider, model = model_name.split("/", 1)
    
    if provider.lower() == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature)
    elif provider.lower() == "openai":
        return ChatOpenAI(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unsupported model provider: {provider}") 