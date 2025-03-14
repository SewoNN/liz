"""Configuration for the script writer.

This module defines the configuration for the script writer.
"""

from config.configuration import Configuration
from config.prompts import SCRIPT_CREATOR_PROMPT
from config.prompts import BOX_CREATOR_PROMPT
from config.prompts import DATE_SCHEDULER_PROMPT


__all__ = ["Configuration", "SCRIPT_CREATOR_PROMPT", "BOX_CREATOR_PROMPT", "DATE_SCHEDULER_PROMPT"]
