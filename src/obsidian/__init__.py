# ----------------------------------------------------------------------------
#  File:        __init__.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Obsidian integration module initialization
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Obsidian integration for AI Know It All."""

from .core import ObsidianMemory
from .utils import sanitize_filename, extract_concepts, auto_link_concepts

__all__ = ['ObsidianMemory', 'sanitize_filename', 'extract_concepts', 'auto_link_concepts'] 