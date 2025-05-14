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

import os
import json
import logging
import requests
import time
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import markdown
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        self.obsidian_path = obsidian_path
        self.api_url = api_url
        self.api_port = api_port
        self.api_token = api_token
        self.base_url = f"http://{api_url}:{api_port}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Create memory directory in Obsidian if it doesn't exist
        self.memory_dir = os.path.join(obsidian_path, "AI-Know-It-All")
        
        # Ensure the Obsidian vault path exists
        self._ensure_obsidian_path()
        
        # Check if API is available
        self.api_available = self._check_api_available()
        if not self.api_available:
            logger.warning("Obsidian API not available. Falling back to file system operations.")
        
        logger.info(f"Initialized Obsidian memory handler with path: {obsidian_path}")
        
    def _ensure_obsidian_path(self) -> None:
        """Ensure the Obsidian path exists and is properly set up."""
        try:
            # Check if the Obsidian vault path exists
            if not os.path.exists(self.obsidian_path):
                logger.warning(f"Obsidian vault path does not exist: {self.obsidian_path}")
                logger.info("Creating Obsidian vault path")
                os.makedirs(self.obsidian_path, exist_ok=True)
                
            # Create the AI-Know-It-All directory if it doesn't exist
            if not os.path.exists(self.memory_dir):
                logger.info(f"Creating AI-Know-It-All directory in Obsidian vault")
                os.makedirs(self.memory_dir, exist_ok=True)
                
            # Create a .obsidian directory if it doesn't exist
            obsidian_config_dir = os.path.join(self.obsidian_path, ".obsidian")
            if not os.path.exists(obsidian_config_dir):
                logger.info("Creating .obsidian directory")
                os.makedirs(obsidian_config_dir, exist_ok=True)
                
            # Create a basic config file if it doesn't exist
            config_file = os.path.join(obsidian_config_dir, "app.json")
            if not os.path.exists(config_file):
                with open(config_file, 'w') as f:
                    json.dump({"promptDelete": False}, f)
                    
            # Create a README file in the AI-Know-It-All directory
            readme_file = os.path.join(self.memory_dir, "README.md")
            if not os.path.exists(readme_file):
                with open(readme_file, 'w') as f:
                    f.write("# AI Know It All Memory\n\n")
                    f.write("This directory contains conversation memories from the AI Know It All chatbot.\n\n")
                    f.write("Each file represents a conversation session with timestamps and full message history.\n")
                    
            logger.info(f"Obsidian path setup completed: {self.obsidian_path}")
        except Exception as e:
            logger.error(f"Error ensuring Obsidian path: {e}")
            logger.debug(traceback.format_exc())
        
    def _check_api_available(self) -> bool:
        """Check if the Obsidian API is available."""
        try:
            response = requests.get(
                f"{self.base_url}/vault/",
                headers=self.headers,
                timeout=2  # Short timeout to avoid long waits
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Obsidian API not available: {e}")
            return False
        
    def _get_formatted_date(self) -> str:
        """Get current date formatted for filenames."""
        return datetime.now().strftime("%Y-%m-%d")
        
    def _get_formatted_time(self) -> str:
        """Get current time formatted for note content."""
        return datetime.now().strftime("%H:%M:%S")
        
    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filenames."""
        # Remove invalid filename characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            text = text.replace(char, '')
        # Limit length and replace spaces with dashes
        return text[:50].strip().replace(' ', '-')
        
    def create_memory_note(self, 
                          conversation: List[Dict[str, Any]], 
                          custom_filename: Optional[str] = None) -> Optional[str]:
        """
        Create a new note in Obsidian for the conversation.
        
        Args:
            conversation: List of conversation messages with role and content
            custom_filename: Optional custom filename (without extension)
            
        Returns:
            Path to the created note or None if failed
        """
        try:
            # Check if conversation is valid
            if not conversation or not isinstance(conversation, list):
                logger.error(f"Invalid conversation data: {type(conversation)}")
                return None
                
            # Generate filename based on date and first user message or custom filename
            date_str = self._get_formatted_date()
            time_str = self._get_formatted_time().replace(':', '-')
            
            if custom_filename:
                filename = f"{custom_filename}.md"
            else:
                # Find first user message for title
                title_content = "Conversation"
                for msg in conversation:
                    if msg["role"] == "user":
                        title_content = self._sanitize_filename(msg["content"] if "content" in msg else msg.get("text", ""))
                        break
                        
                filename = f"{date_str}-{time_str}-{title_content}.md"
                
            filepath = os.path.join(self.memory_dir, filename)
            logger.debug(f"Creating memory note at: {filepath}")
            
            # Generate note content
            content = [
                f"# Conversation: {os.path.splitext(filename)[0]}",
                f"Date: {date_str} {self._get_formatted_time()}",
                "Tags: #ai-conversation #memory",
                "",
                "## Conversation History",
                ""
            ]
            
            # Add conversation messages
            for i, msg in enumerate(conversation):
                try:
                    role = "User" if msg["role"] == "user" else ("AI" if msg["role"] == "assistant" else "System")
                    
                    # Handle the timestamp - ensure it exists and is a valid number
                    timestamp = time.time()  # Default to current time
                    if "timestamp" in msg and isinstance(msg["timestamp"], (int, float)):
                        timestamp = msg["timestamp"]
                        
                    # Format the timestamp
                    timestamp_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                    
                    # Handle the content - check both content and text fields
                    msg_content = ""
                    if "content" in msg and msg["content"] is not None:
                        msg_content = str(msg["content"])
                    elif "text" in msg and msg["text"] is not None:
                        msg_content = str(msg["text"])
                    else:
                        logger.warning(f"Message {i} has no content or text: {msg}")
                        
                    content.append(f"### {role} ({timestamp_str})")
                    content.append(msg_content)
                    content.append("")
                except Exception as msg_e:
                    logger.error(f"Error processing message {i}: {msg_e}")
                    logger.debug(f"Problematic message: {msg}")
                    # Continue with next message
                    continue
                
            # Write to file
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                content_str = '\n'.join(content)
                logger.debug(f"Writing {len(content_str)} bytes to {filepath}")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content_str)
                    
                logger.info(f"Created memory note: {filepath}")
                return filepath
            except Exception as e:
                logger.error(f"Error writing memory note file: {e}")
                logger.debug(traceback.format_exc())
                return None
        except Exception as e:
            logger.error(f"Error creating memory note: {e}")
            logger.debug(traceback.format_exc())
            return None
        
    def update_memory_note(self, filepath: str, messages: List[Dict[str, Any]]) -> bool:
        """
        Update an existing note with messages.
        
        Args:
            filepath: Path to the note file
            messages: All messages to include in the note (will replace existing content)
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(filepath):
            logger.error(f"Note not found: {filepath}")
            return False
            
        try:
            # Check if messages is valid
            if not messages or not isinstance(messages, list):
                logger.error(f"Invalid messages data: {type(messages)}")
                return False
                
            # Generate updated content
            date_str = self._get_formatted_date()
            time_str = self._get_formatted_time()
            filename = os.path.basename(filepath)
            
            content = [
                f"# Conversation: {os.path.splitext(filename)[0]}",
                f"Date: {date_str} {time_str} (Updated)",
                "Tags: #ai-conversation #memory",
                "",
                "## Conversation History",
                ""
            ]
            
            # Add all messages
            for i, msg in enumerate(messages):
                try:
                    role = "User" if msg["role"] == "user" else ("AI" if msg["role"] == "assistant" else "System")
                    
                    # Handle the timestamp - ensure it exists and is a valid number
                    timestamp = time.time()  # Default to current time
                    if "timestamp" in msg and isinstance(msg["timestamp"], (int, float)):
                        timestamp = msg["timestamp"]
                        
                    # Format the timestamp
                    timestamp_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                    
                    # Handle the content - check both content and text fields
                    msg_content = ""
                    if "content" in msg and msg["content"] is not None:
                        msg_content = str(msg["content"])
                    elif "text" in msg and msg["text"] is not None:
                        msg_content = str(msg["text"])
                    else:
                        logger.warning(f"Message {i} has no content or text: {msg}")
                        
                    content.append(f"### {role} ({timestamp_str})")
                    content.append(msg_content)
                    content.append("")
                except Exception as msg_e:
                    logger.error(f"Error processing message {i}: {msg_e}")
                    logger.debug(f"Problematic message: {msg}")
                    # Continue with next message
                    continue
                
            # Write updated content
            try:
                content_str = '\n'.join(content)
                logger.debug(f"Writing {len(content_str)} bytes to {filepath}")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content_str)
                    
                logger.info(f"Updated memory note: {filepath}")
                return True
            except Exception as file_e:
                logger.error(f"Error writing to file: {file_e}")
                logger.debug(traceback.format_exc())
                return False
        except Exception as e:
            logger.error(f"Error updating memory note: {e}")
            logger.debug(traceback.format_exc())
            return False
        
    def get_all_notes(self) -> List[Dict[str, Any]]:
        """
        Get all notes from the Obsidian vault.
        
        Returns:
            List of note metadata
        """
        if not self.api_available:
            return self._get_all_notes_from_filesystem()
            
        try:
            response = requests.get(
                f"{self.base_url}/vault/",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting notes from Obsidian API: {e}")
            return self._get_all_notes_from_filesystem()
            
    def _get_all_notes_from_filesystem(self) -> List[Dict[str, Any]]:
        """Get all notes from the file system."""
        notes = []
        
        if not os.path.exists(self.memory_dir):
            return notes
            
        for filename in os.listdir(self.memory_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(self.memory_dir, filename)
                notes.append({
                    'path': filepath,
                    'name': filename,
                    'modified': os.path.getmtime(filepath)
                })
                
        return notes
            
    def get_note_content(self, note_path: str) -> Optional[str]:
        """
        Get the content of a specific note.
        
        Args:
            note_path: Path to the note
            
        Returns:
            Note content or None if not found
        """
        # If path is a file path, read directly from file system
        if os.path.exists(note_path):
            try:
                with open(note_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading note from file system: {e}")
                return None
                
        # Otherwise try API if available
        if not self.api_available:
            return None
            
        try:
            response = requests.get(
                f"{self.base_url}/vault/{note_path}",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            
            return response.json().get("content")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting note content from Obsidian API: {e}")
            return None
            
    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """
        Search notes in Obsidian.
        
        Args:
            query: Search query
            
        Returns:
            List of matching notes
        """
        if not self.api_available:
            return self._search_notes_from_filesystem(query)
            
        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json={"query": query},
                timeout=5
            )
            response.raise_for_status()
            
            return response.json().get("results", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching notes in Obsidian API: {e}")
            return self._search_notes_from_filesystem(query)
            
    def _search_notes_from_filesystem(self, query: str) -> List[Dict[str, Any]]:
        """Search notes in the file system."""
        results = []
        query = query.lower()
        
        if not os.path.exists(self.memory_dir):
            return results
            
        for filename in os.listdir(self.memory_dir):
            if not filename.endswith('.md'):
                continue
                
            filepath = os.path.join(self.memory_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    
                if query in content:
                    results.append({
                        'path': filepath,
                        'name': filename,
                        'modified': os.path.getmtime(filepath),
                        'content': content[:300] + "..." if len(content) > 300 else content
                    })
            except Exception as e:
                logger.error(f"Error reading file during search: {e}")
                
        return results
            
    def get_recent_conversations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent conversation notes from Obsidian.
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation notes
        """
        # List all files in the memory directory
        memory_files = []
        
        if not os.path.exists(self.memory_dir):
            return memory_files
            
        for file in os.listdir(self.memory_dir):
            if file.endswith('.md') and file != "README.md":
                filepath = os.path.join(self.memory_dir, file)
                memory_files.append({
                    'path': filepath,
                    'modified': os.path.getmtime(filepath)
                })
                
        # Sort by modification time (newest first)
        memory_files.sort(key=lambda x: x['modified'], reverse=True)
        
        # Get the most recent files
        recent_files = memory_files[:limit]
        
        # Load content for each file
        conversations = []
        for file_info in recent_files:
            try:
                with open(file_info['path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                conversations.append({
                    'path': file_info['path'],
                    'modified': datetime.fromtimestamp(file_info['modified']).strftime("%Y-%m-%d %H:%M:%S"),
                    'content': content
                })
            except Exception as e:
                logger.error(f"Error reading recent conversation file: {e}")
            
        return conversations
        
    def extract_conversation_from_note(self, note_content: str) -> List[Dict[str, str]]:
        """
        Extract conversation messages from a note.
        
        Args:
            note_content: Content of the note
            
        Returns:
            List of messages with role and content
        """
        if not note_content:
            return []
            
        lines = note_content.split('\n')
        messages = []
        
        current_role = None
        current_content = []
        
        for line in lines:
            if line.startswith('### User'):
                # Save previous message if exists
                if current_role and current_content:
                    messages.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip()
                    })
                    current_content = []
                
                current_role = 'user'
            elif line.startswith('### AI'):
                # Save previous message if exists
                if current_role and current_content:
                    messages.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip()
                    })
                    current_content = []
                
                current_role = 'assistant'
            elif line.startswith('### System'):
                # Save previous message if exists
                if current_role and current_content:
                    messages.append({
                        'role': current_role,
                        'content': '\n'.join(current_content).strip()
                    })
                    current_content = []
                
                current_role = 'system'
            elif current_role:
                current_content.append(line)
                
        # Save the last message if exists
        if current_role and current_content:
            messages.append({
                'role': current_role,
                'content': '\n'.join(current_content).strip()
            })
            
        return messages 