# ----------------------------------------------------------------------------
#  File:        core.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Core functionality for Obsidian integration
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Core functionality for Obsidian integration."""

import os
import logging
import traceback
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import markdown
from bs4 import BeautifulSoup

from .api import ObsidianAPI
from .filesystem import ObsidianFileSystem
from .utils import (
    sanitize_filename, extract_concepts, auto_link_concepts,
    get_formatted_date, get_formatted_time, format_conversation_as_markdown
)

# Configure logging
logger = logging.getLogger(__name__)


class ObsidianMemory:
    """
    A class to handle storing, viewing, and altering memories in Obsidian.
    """
    def __init__(self, 
                obsidian_path: str = "/Users/chriscelaya/ObsidianVaults",
                api_url: str = "127.0.0.1",
                api_port: int = 27124,
                api_token: str = "35d80b834a12ecea5e21f4838722b8af8575ce7186d56176a9ba7835a0334951"):
        """
        Initialize the Obsidian memory handler.
        
        Args:
            obsidian_path: Path to the Obsidian vault
            api_url: URL for the Obsidian API
            api_port: Port for the Obsidian API
            api_token: Authorization token for the Obsidian API
        """
        # Initialize API and file system handlers
        self.api = ObsidianAPI(api_url, api_port, api_token)
        self.fs = ObsidianFileSystem(obsidian_path)
        
        # Store paths
        self.obsidian_path = obsidian_path
        self.memory_dir = self.fs.memory_dir
        self.daily_notes_dir = self.fs.daily_notes_dir
        
        # Initialize concept cache for auto-linking
        self.concept_cache = set()
        self._load_concept_cache()
        
    def _load_concept_cache(self) -> None:
        """Load existing note titles for auto-linking."""
        try:
            # Get all markdown files in the vault to extract concepts
            self.concept_cache = set()
            
            # Walk through the Obsidian vault to find all markdown files
            for root, _, files in os.walk(self.obsidian_path):
                for file in files:
                    if file.endswith('.md'):
                        # Add the filename without extension as a concept
                        concept = os.path.splitext(file)[0]
                        self.concept_cache.add(concept)
                        
            logger.info(f"Loaded {len(self.concept_cache)} concepts for auto-linking")
        except Exception as e:
            logger.error(f"Error loading concept cache: {e}")
            logger.debug(traceback.format_exc())
            
    def _auto_link_concepts(self, text: str) -> str:
        """
        Auto-link concepts in text with Obsidian wiki links.
        
        Args:
            text: Text to add wiki links to
            
        Returns:
            Text with wiki links added
        """
        return auto_link_concepts(text, self.concept_cache)
        
    def create_daily_note(self) -> Optional[str]:
        """
        Create or update a daily note in Obsidian.
        
        Returns:
            Path to the daily note or None if failed
        """
        try:
            # Get the date
            date = get_formatted_date()
            
            # Get the daily note path
            daily_note_path = self.fs.get_daily_note_path(date)
            
            # Check if the daily note exists
            if os.path.exists(daily_note_path):
                # Read the existing content
                with open(daily_note_path, 'r') as f:
                    content = f.read()
            else:
                # Create a new daily note
                content = f"# Daily Note: {date}\n\n"
                content += f"Created: {get_formatted_time()}\n\n"
                content += "## Conversations\n\n"
                
            # Write the daily note
            if self.api.api_available:
                # Try to use the API
                rel_path = os.path.relpath(daily_note_path, self.obsidian_path)
                success = self.api.update_note(rel_path, content)
                
                if not success:
                    # Fall back to file system
                    success = self.fs.update_file(daily_note_path, content)
            else:
                # Use the file system
                success = self.fs.update_file(daily_note_path, content)
                
            if success:
                logger.info(f"Created/updated daily note: {daily_note_path}")
                return daily_note_path
            else:
                logger.error("Failed to create/update daily note")
                return None
        except Exception as e:
            logger.error(f"Error creating daily note: {e}")
            logger.debug(traceback.format_exc())
            return None
            
    def update_daily_note(self, filepath: str, conversation_link: str, summary: str = None) -> bool:
        """
        Update a daily note with a link to a conversation.
        
        Args:
            filepath: Path to the daily note
            conversation_link: Link to the conversation
            summary: Optional summary of the conversation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the existing content
            content = self.fs.read_file(filepath)
            
            if not content:
                logger.error(f"Failed to read daily note: {filepath}")
                return False
                
            # Add the conversation link
            time_str = get_formatted_time()
            
            if summary:
                link_entry = f"- {time_str}: {conversation_link} - {summary}\n"
            else:
                link_entry = f"- {time_str}: {conversation_link}\n"
                
            # Find the Conversations section
            if "## Conversations" in content:
                # Add the link after the Conversations section
                parts = content.split("## Conversations")
                content = parts[0] + "## Conversations\n\n" + link_entry + parts[1].split("\n", 1)[1]
            else:
                # Add a Conversations section
                content += "\n## Conversations\n\n" + link_entry
                
            # Write the updated content
            if self.api.api_available:
                # Try to use the API
                rel_path = os.path.relpath(filepath, self.obsidian_path)
                success = self.api.update_note(rel_path, content)
                
                if not success:
                    # Fall back to file system
                    success = self.fs.update_file(filepath, content)
            else:
                # Use the file system
                success = self.fs.update_file(filepath, content)
                
            if success:
                logger.info(f"Updated daily note with conversation link: {filepath}")
                return True
            else:
                logger.error("Failed to update daily note with conversation link")
                return False
        except Exception as e:
            logger.error(f"Error updating daily note: {e}")
            logger.debug(traceback.format_exc())
            return False
            
    def create_memory_note(self, 
                          conversation: List[Dict[str, Any]], 
                          custom_filename: Optional[str] = None,
                          retrieved_memories: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        """
        Create a memory note in Obsidian.
        
        Args:
            conversation: List of conversation messages
            custom_filename: Optional custom filename
            retrieved_memories: Optional list of retrieved memories
            
        Returns:
            Path to the memory note or None if failed
        """
        try:
            # Generate a filename if not provided
            if custom_filename is None:
                # Try to extract a title from the conversation
                title = None
                
                # Look for the first user message
                for message in conversation:
                    if message.get("role") == "user":
                        # Use the first 50 characters of the message as the title
                        title = message.get("content", "")[:50]
                        break
                        
                if title:
                    filename = sanitize_filename(title)
                else:
                    # Use the current timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"Conversation_{timestamp}"
            else:
                filename = custom_filename
                
            # Create the file path
            filepath = os.path.join(self.memory_dir, f"{filename}.md")
            
            # Generate the content
            content = f"# {filename}\n\n"
            content += f"Created: {get_formatted_date()} {get_formatted_time()}\n\n"
            
            # Add retrieved memories if provided
            if retrieved_memories:
                content += "## Retrieved Memories\n\n"
                
                for i, memory in enumerate(retrieved_memories):
                    memory_text = memory.get("text", "")
                    memory_source = memory.get("source", "Unknown")
                    
                    # Auto-link concepts
                    memory_text = self._auto_link_concepts(memory_text)
                    
                    content += f"### Memory {i+1}\n\n"
                    content += f"Source: {memory_source}\n\n"
                    content += f"{memory_text}\n\n"
                    
                content += "---\n\n"
                
            # Add the conversation
            content += "## Conversation\n\n"
            content += format_conversation_as_markdown(conversation)
            
            # Auto-link concepts in the content
            content = self._auto_link_concepts(content)
            
            # Write the file
            if self.api.api_available:
                # Try to use the API
                rel_path = os.path.relpath(filepath, self.obsidian_path)
                success = self.api.create_note(rel_path, content)
                
                if not success:
                    # Fall back to file system
                    success = self.fs.create_file(filepath, content)
            else:
                # Use the file system
                success = self.fs.create_file(filepath, content)
                
            if success:
                logger.info(f"Created memory note: {filepath}")
                
                # Update the daily note
                daily_note_path = self.create_daily_note()
                if daily_note_path:
                    # Create a link to the conversation
                    rel_path = os.path.relpath(filepath, self.obsidian_path)
                    conversation_link = f"[[{os.path.splitext(rel_path)[0]}]]"
                    
                    # Update the daily note
                    self.update_daily_note(daily_note_path, conversation_link)
                
                return filepath
            else:
                logger.error("Failed to create memory note")
                return None
        except Exception as e:
            logger.error(f"Error creating memory note: {e}")
            logger.debug(traceback.format_exc())
            return None
            
    def update_memory_note(self, filepath: str, messages: List[Dict[str, Any]], retrieved_memories: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Update a memory note in Obsidian.
        
        Args:
            filepath: Path to the memory note
            messages: List of conversation messages
            retrieved_memories: Optional list of retrieved memories
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the existing content
            content = self.fs.read_file(filepath)
            
            if not content:
                logger.error(f"Failed to read memory note: {filepath}")
                return False
                
            # Parse the content to find the conversation section
            if "## Conversation" in content:
                # Replace the conversation section
                parts = content.split("## Conversation")
                header = parts[0]
                
                # Format the new conversation
                new_conversation = "## Conversation\n\n"
                new_conversation += format_conversation_as_markdown(messages)
                
                # Auto-link concepts
                new_conversation = self._auto_link_concepts(new_conversation)
                
                # Update the content
                content = header + new_conversation
            else:
                # Add a conversation section
                content += "\n## Conversation\n\n"
                content += format_conversation_as_markdown(messages)
                
                # Auto-link concepts
                content = self._auto_link_concepts(content)
                
            # Write the updated content
            if self.api.api_available:
                # Try to use the API
                rel_path = os.path.relpath(filepath, self.obsidian_path)
                success = self.api.update_note(rel_path, content)
                
                if not success:
                    # Fall back to file system
                    success = self.fs.update_file(filepath, content)
            else:
                # Use the file system
                success = self.fs.update_file(filepath, content)
                
            if success:
                logger.info(f"Updated memory note: {filepath}")
                return True
            else:
                logger.error("Failed to update memory note")
                return False
        except Exception as e:
            logger.error(f"Error updating memory note: {e}")
            logger.debug(traceback.format_exc())
            return False
            
    def get_all_notes(self) -> List[Dict[str, Any]]:
        """
        Get all notes from the Obsidian vault.
        
        Returns:
            List of notes
        """
        # Try to use the API first
        api_notes = self.api.get_all_notes()
        
        if api_notes is not None:
            return api_notes
            
        # Fall back to file system
        return self.fs.get_all_notes()
        
    def get_note_content(self, note_path: str) -> Optional[str]:
        """
        Get the content of a note from the Obsidian vault.
        
        Args:
            note_path: Path to the note
            
        Returns:
            Note content or None if the note doesn't exist
        """
        # Try to use the API first
        api_content = self.api.get_note_content(note_path)
        
        if api_content is not None:
            return api_content
            
        # Fall back to file system
        return self.fs.read_file(os.path.join(self.obsidian_path, note_path))
        
    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for notes in the Obsidian vault.
        
        Args:
            query: Search query
            
        Returns:
            List of matching notes
        """
        # Try to use the API first
        api_results = self.api.search_notes(query)
        
        if api_results is not None:
            return api_results
            
        # Fall back to file system
        return self.fs.search_notes(query)
        
    def get_recent_conversations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversations from the Obsidian vault.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of recent conversations
        """
        try:
            # Get all notes
            all_notes = self.get_all_notes()
            
            # Sort by modified time (descending)
            sorted_notes = sorted(all_notes, key=lambda x: x.get("modified", 0), reverse=True)
            
            # Return the most recent notes
            return sorted_notes[:limit]
        except Exception as e:
            logger.error(f"Error getting recent conversations: {e}")
            logger.debug(traceback.format_exc())
            return []
            
    def extract_conversation_from_note(self, note_content: str) -> List[Dict[str, str]]:
        """
        Extract a conversation from a note.
        
        Args:
            note_content: Content of the note
            
        Returns:
            List of conversation messages
        """
        conversation = []
        
        try:
            # Convert Markdown to HTML
            html = markdown.markdown(note_content)
            
            # Parse the HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all h2 elements
            h2_elements = soup.find_all('h2')
            
            # Process each h2 element
            for h2 in h2_elements:
                # Check if this is a conversation message
                text = h2.get_text()
                
                if "User" in text or "Assistant" in text or "System" in text:
                    # Extract the role
                    if "User" in text:
                        role = "user"
                    elif "Assistant" in text:
                        role = "assistant"
                    else:
                        role = "system"
                        
                    # Extract the timestamp
                    timestamp_match = re.search(r'\((.*?)\)', text)
                    timestamp = timestamp_match.group(1) if timestamp_match else None
                    
                    # Get the content
                    content = ""
                    current = h2.next_sibling
                    
                    while current and current.name != 'h2':
                        if hasattr(current, 'get_text'):
                            content += current.get_text() + "\n"
                        current = current.next_sibling
                        
                    # Add the message to the conversation
                    conversation.append({
                        "role": role,
                        "content": content.strip(),
                        "timestamp": timestamp
                    })
        except Exception as e:
            logger.error(f"Error extracting conversation from note: {e}")
            logger.debug(traceback.format_exc())
            
        return conversation 