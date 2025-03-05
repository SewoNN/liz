"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List, Optional, cast

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
from transformers import pipeline
from asyncio import get_running_loop

from script_maker.configuration import Configuration


# async def search(
#     query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
# ) -> Optional[list[dict[str, Any]]]:
#     """Search for general web results.

#     This function performs a search using the Tavily search engine, which is designed
#     to provide comprehensive, accurate, and trusted results. It's particularly useful
#     for answering questions about current events.
#     """
#     configuration = Configuration.from_runnable_config(config)
#     wrapped = TavilySearchResults(max_results=configuration.max_search_results)
#     result = await wrapped.ainvoke({"query": query})
#     return cast(list[dict[str, Any]], result)

async def sentiment_analysis(
        text: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[dict[str, Any]]:
    """Perform sentiment analysis on input text."""
    sa_pipeline = pipeline("sentiment-analysis")
    loop = get_running_loop()
    result = await loop.run_in_executor(None, sa_pipeline, text)
    return cast(list[dict[str, Any]], result)

TOOLS: List[Callable[..., Any]] = [sentiment_analysis]