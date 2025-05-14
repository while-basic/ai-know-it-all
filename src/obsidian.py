# ----------------------------------------------------------------------------
#  File:        obsidian.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Obsidian integration for storing, viewing, and altering memories
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Obsidian integration for AI Know It All."""

# This file is maintained for backward compatibility
# New code should use the obsidian package directly

from .obsidian.core import ObsidianMemory
from .obsidian.utils import (
    sanitize_filename, extract_concepts, auto_link_concepts,
    get_formatted_date, get_formatted_time, format_conversation_as_markdown
)
from .obsidian.api import ObsidianAPI
from .obsidian.filesystem import ObsidianFileSystem

# Re-export the main class for backward compatibility
__all__ = ['ObsidianMemory']
