"""Tools for the box maker agent."""

from typing import Any, Callable, Dict, List, Optional, cast

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated


async def calculate_material(
    length: float, width: float, height: float, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> Optional[Dict[str, Any]]:
    """Calculate the amount of material needed for a box with the given dimensions.
    
    This tool calculates the total surface area of a box, which can be used to estimate
    the amount of material needed for construction.
    
    Args:
        length: The length of the box in centimeters.
        width: The width of the box in centimeters.
        height: The height of the box in centimeters.
        
    Returns:
        A dictionary containing the calculated surface area and material estimates.
    """
    # Calculate the surface area of the box
    surface_area = 2 * (length * width + length * height + width * height)
    
    # Add 10% for tabs and folds
    total_material = surface_area * 1.1
    
    return {
        "surface_area_cm2": surface_area,
        "total_material_needed_cm2": total_material,
        "cardboard_sheets_needed": total_material / 2500,  # Assuming standard 50x50cm sheets
    }


TOOLS: List[Callable[..., Any]] = [calculate_material] 