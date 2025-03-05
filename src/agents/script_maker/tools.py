"""Tools for the script maker agent."""

from typing import Any, Callable, List, Optional, cast

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
from transformers import pipeline
from asyncio import get_running_loop


async def sentiment_analysis(
        text: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[List[dict[str, Any]]]:
    """Perform sentiment analysis on input text.
    
    This tool analyzes the sentiment of the provided text, determining if it's positive,
    negative, or neutral. It's useful for understanding the emotional tone of content.
    
    Args:
        text: The text to analyze.
        
    Returns:
        A list of dictionaries containing the sentiment analysis results.
    """
    sa_pipeline = pipeline("sentiment-analysis")
    loop = get_running_loop()
    result = await loop.run_in_executor(None, sa_pipeline, text)
    return cast(List[dict[str, Any]], result)


TOOLS: List[Callable[..., Any]] = [sentiment_analysis] 