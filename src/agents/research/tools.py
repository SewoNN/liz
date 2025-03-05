"""Tools for the research agent."""

from typing import Any, Callable, Dict, List, Optional, cast

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated


async def search(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[List[Dict[str, Any]]]:
    """Search for general web results.

    This function performs a search using the Tavily search engine, which is designed
    to provide comprehensive, accurate, and trusted results. It's particularly useful
    for answering questions about current events, facts, and general information.
    
    Args:
        query: The search query.
        
    Returns:
        A list of dictionaries containing the search results.
    """
    wrapped = TavilySearchResults(max_results=5)
    result = await wrapped.ainvoke({"query": query})
    return cast(List[Dict[str, Any]], result)


async def summarize(
    text: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[Dict[str, Any]]:
    """Summarize a long piece of text.
    
    This tool takes a long piece of text and generates a concise summary that captures
    the main points and key information.
    
    Args:
        text: The text to summarize.
        
    Returns:
        A dictionary containing the summary.
    """
    # In a real implementation, this would use a model to generate a summary
    # For now, we'll just return a placeholder
    words = text.split()
    if len(words) <= 100:
        return {"summary": text}
    
    # Simple extractive summary (first 100 words)
    summary = " ".join(words[:100]) + "..."
    return {"summary": summary}


TOOLS: List[Callable[..., Any]] = [search, summarize] 