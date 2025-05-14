# ----------------------------------------------------------------------------
#  File:        utils.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Utility functions for Obsidian integration
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Utility functions for Obsidian integration."""

import re
from typing import Set, Dict, Any, List
from datetime import datetime


def sanitize_filename(text: str) -> str:
    """
    Sanitize text for use in filenames.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text suitable for filenames
    """
    # Remove invalid filename characters
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        text = text.replace(char, '')
    # Limit length and replace spaces with dashes
    return text[:50].strip().replace(' ', '-')


def extract_concepts(text: str, concept_cache: Set[str]) -> Set[str]:
    """
    Extract potential concepts from text for auto-linking.
    
    Args:
        text: Text to extract concepts from
        concept_cache: Set of known concepts to match against
        
    Returns:
        Set of concepts found in the text
    """
    # Simple extraction of capitalized words and phrases
    concepts = set()
    
    # Find capitalized words (potential proper nouns)
    # This regex looks for words starting with a capital letter followed by lowercase letters
    capitalized_words = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
    concepts.update(capitalized_words)
    
    # Find potential multi-word concepts (e.g., "New York", "Machine Learning")
    # This regex looks for 2-3 consecutive capitalized words
    multi_word = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b', text)
    concepts.update(multi_word)
    
    # Filter concepts that exist in our concept cache
    return {concept for concept in concepts if concept in concept_cache}


def auto_link_concepts(text: str, concept_cache: Set[str]) -> str:
    """
    Auto-link concepts in text with Obsidian wiki links.
    
    Args:
        text: Text to add wiki links to
        concept_cache: Set of known concepts to link
        
    Returns:
        Text with wiki links added
    """
    # Extract concepts from the text
    concepts = extract_concepts(text, concept_cache)
    
    # Sort concepts by length (descending) to handle overlapping concepts
    sorted_concepts = sorted(concepts, key=len, reverse=True)
    
    # Replace concepts with wiki links
    for concept in sorted_concepts:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(concept) + r'\b'
        replacement = f"[[{concept}]]"
        text = re.sub(pattern, replacement, text)
        
    return text


def get_formatted_date() -> str:
    """Get current date formatted for filenames."""
    return datetime.now().strftime("%Y-%m-%d")


def get_formatted_time() -> str:
    """Get current time formatted for note content."""
    return datetime.now().strftime("%H:%M:%S")


def format_conversation_as_markdown(conversation: List[Dict[str, Any]]) -> str:
    """
    Format a conversation as Markdown.
    
    Args:
        conversation: List of conversation messages
        
    Returns:
        Markdown formatted conversation
    """
    markdown_content = ""
    
    for message in conversation:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        timestamp = message.get("timestamp", None)
        
        if timestamp:
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        else:
            time_str = get_formatted_time()
            
        if role == "user":
            markdown_content += f"## 👤 User ({time_str})\n\n{content}\n\n"
        elif role == "assistant":
            markdown_content += f"## 🤖 Assistant ({time_str})\n\n{content}\n\n"
        elif role == "system":
            markdown_content += f"## 🔧 System ({time_str})\n\n{content}\n\n"
        else:
            markdown_content += f"## {role.capitalize()} ({time_str})\n\n{content}\n\n"
            
    return markdown_content 