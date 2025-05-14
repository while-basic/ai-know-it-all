# ----------------------------------------------------------------------------
#  File:        filesystem.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: File system operations for Obsidian integration
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""File system operations for Obsidian integration."""

import os
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import shutil

from .utils import get_formatted_date, get_formatted_time

# Configure logging
logger = logging.getLogger(__name__)


class ObsidianFileSystem:
    """
    A class to handle file system operations for Obsidian integration.
    """
    def __init__(self, obsidian_path: str = "/Users/chriscelaya/ObsidianVaults"):
        """
        Initialize the Obsidian file system handler.
        
        Args:
            obsidian_path: Path to the Obsidian vault
        """
        self.obsidian_path = obsidian_path
        
        # Create memory directory in Obsidian if it doesn't exist
        self.memory_dir = os.path.join(obsidian_path, "ai-know-it-all")
        self.daily_notes_dir = os.path.join(self.memory_dir, "Daily Notes")
        
        # Ensure the Obsidian vault path exists
        self._ensure_obsidian_path()
        
    def _ensure_obsidian_path(self) -> None:
        """
        Ensure the Obsidian path exists and is properly set up.
        """
        try:
            # Check if the Obsidian vault path exists
            if not os.path.exists(self.obsidian_path):
                logger.warning(f"Obsidian vault path does not exist: {self.obsidian_path}")
                logger.info("Creating Obsidian vault path")
                os.makedirs(self.obsidian_path, exist_ok=True)
                
            # Create the ai-know-it-all directory if it doesn't exist
            if not os.path.exists(self.memory_dir):
                logger.info(f"Creating ai-know-it-all directory in Obsidian vault")
                os.makedirs(self.memory_dir, exist_ok=True)
                
            # Create Daily Notes directory if it doesn't exist
            if not os.path.exists(self.daily_notes_dir):
                logger.info(f"Creating Daily Notes directory in ai-know-it-all")
                os.makedirs(self.daily_notes_dir, exist_ok=True)
                
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
                    
            # Create a README file in the ai-know-it-all directory
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
            
    def create_file(self, filepath: str, content: str) -> bool:
        """
        Create a file in the Obsidian vault.
        
        Args:
            filepath: Path to the file
            content: Content of the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write the file
            with open(filepath, 'w') as f:
                f.write(content)
                
            logger.info(f"Created file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            logger.debug(traceback.format_exc())
            return False
            
    def update_file(self, filepath: str, content: str) -> bool:
        """
        Update a file in the Obsidian vault.
        
        Args:
            filepath: Path to the file
            content: New content of the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the file exists
            if not os.path.exists(filepath):
                logger.warning(f"File does not exist: {filepath}")
                return self.create_file(filepath, content)
                
            # Write the file
            with open(filepath, 'w') as f:
                f.write(content)
                
            logger.info(f"Updated file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error updating file: {e}")
            logger.debug(traceback.format_exc())
            return False
            
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read a file from the Obsidian vault.
        
        Args:
            filepath: Path to the file
            
        Returns:
            File content or None if the file doesn't exist
        """
        try:
            # Check if the file exists
            if not os.path.exists(filepath):
                logger.warning(f"File does not exist: {filepath}")
                return None
                
            # Read the file
            with open(filepath, 'r') as f:
                content = f.read()
                
            return content
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            logger.debug(traceback.format_exc())
            return None
            
    def get_all_notes(self) -> List[Dict[str, Any]]:
        """
        Get all notes from the Obsidian vault.
        
        Returns:
            List of notes
        """
        notes = []
        
        try:
            # Walk through the entire Obsidian vault
            for root, _, files in os.walk(self.obsidian_path):
                # Skip .obsidian directory and other hidden directories
                if os.path.basename(root).startswith('.'):
                    continue
                    
                for file in files:
                    if file.endswith('.md'):
                        # Skip hidden files
                        if os.path.basename(file).startswith('.'):
                            continue
                            
                        # Get the file path
                        filepath = os.path.join(root, file)
                        
                        # Get the relative path
                        rel_path = os.path.relpath(filepath, self.obsidian_path)
                        
                        # Get the file stats
                        stats = os.stat(filepath)
                        
                        # Add the note to the list
                        notes.append({
                            "path": rel_path,
                            "name": os.path.splitext(file)[0],
                            "size": stats.st_size,
                            "created": stats.st_ctime,
                            "modified": stats.st_mtime
                        })
        except Exception as e:
            logger.error(f"Error getting all notes: {e}")
            logger.debug(traceback.format_exc())
            
        return notes
        
    def search_notes(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for notes in the Obsidian vault.
        
        Args:
            query: Search query
            
        Returns:
            List of matching notes
        """
        matching_notes = []
        query = query.lower()
        
        try:
            # Walk through the entire Obsidian vault
            for root, _, files in os.walk(self.obsidian_path):
                # Skip .obsidian directory and other hidden directories
                if os.path.basename(root).startswith('.'):
                    continue
                    
                for file in files:
                    if file.endswith('.md'):
                        # Skip hidden files
                        if os.path.basename(file).startswith('.'):
                            continue
                            
                        # Get the file path
                        filepath = os.path.join(root, file)
                        
                        # Get the relative path
                        rel_path = os.path.relpath(filepath, self.obsidian_path)
                        
                        # Check if the query is in the note name
                        if query in file.lower():
                            # Get the file stats
                            stats = os.stat(filepath)
                            
                            # Read the content for the preview
                            content = self.read_file(filepath)
                            
                            # Add the note to the list
                            matching_notes.append({
                                "path": rel_path,
                                "name": os.path.splitext(file)[0],
                                "size": stats.st_size,
                                "created": stats.st_ctime,
                                "modified": stats.st_mtime,
                                "content": content
                            })
                            continue
                            
                        # Check if the query is in the note content
                        content = self.read_file(filepath)
                        
                        if content and query in content.lower():
                            # Get the file stats
                            stats = os.stat(filepath)
                            
                            # Add the note to the list
                            matching_notes.append({
                                "path": rel_path,
                                "name": os.path.splitext(file)[0],
                                "size": stats.st_size,
                                "created": stats.st_ctime,
                                "modified": stats.st_mtime,
                                "content": content
                            })
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            logger.debug(traceback.format_exc())
            
        return matching_notes
        
    def get_daily_note_path(self, date: str = None) -> str:
        """
        Get the path to a daily note.
        
        Args:
            date: Date for the note (default: today)
            
        Returns:
            Path to the daily note
        """
        if date is None:
            date = get_formatted_date()
            
        return os.path.join(self.daily_notes_dir, f"{date}.md") 