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
        query_lower = query.lower()
        query_terms = [term.lower() for term in query.split() if len(term) > 2]
        
        # Patterns that indicate simulation or test files to filter out
        simulation_patterns = [
            "tick:", "type: simulation", "zombie_mode:", 
            "simulation_log", "test_data", "test file", 
            "example data", "sample data", "mock data"
        ]
        
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
                        
                        # Check if the filename matches the query
                        filename = os.path.splitext(file)[0].lower()
                        filename_match = query_lower in filename
                        
                        # Calculate a match score
                        match_score = 0
                        
                        # Filename match is a strong signal
                        if filename_match:
                            match_score += 10
                            
                        # Check for term matches in filename
                        for term in query_terms:
                            if term in filename:
                                match_score += 5
                                
                        # If we have a good filename match, check if it's not a simulation file
                        if match_score >= 10:
                            # Read the first few lines to check if it's a simulation file
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    header = f.read(500)  # Read just the header
                                    
                                # Check if this is a simulation or test file
                                is_simulation = any(pattern in header.lower() for pattern in simulation_patterns)
                                
                                if is_simulation:
                                    logger.info(f"Skipping simulation/test file: {filepath}")
                                    continue
                            except Exception:
                                pass  # If we can't read the file, assume it's not a simulation
                                
                            matching_notes.append({
                                "path": rel_path,
                                "name": os.path.splitext(file)[0],
                                "size": stats.st_size,
                                "created": stats.st_ctime,
                                "modified": stats.st_mtime,
                                "match_score": match_score,
                                "matched_by": "filename"
                            })
                            continue
                            
                        # Read the file content
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            # Check if this is a simulation or test file
                            is_simulation = any(pattern in content.lower() for pattern in simulation_patterns)
                            
                            if is_simulation:
                                logger.info(f"Skipping simulation/test file: {filepath}")
                                continue
                                
                            # Check for exact query match in content
                            content_match = query_lower in content.lower()
                            
                            # If no direct match, check for term matches
                            term_matches = 0
                            if not content_match and query_terms:
                                content_lower = content.lower()
                                for term in query_terms:
                                    if term in content_lower:
                                        term_matches += content_lower.count(term)
                                        
                            # Add match score based on content
                            if content_match:
                                match_score += 8
                            elif term_matches > 0:
                                # More matches = higher score, but cap at 7
                                match_score += min(7, term_matches)
                                
                            # If we have any kind of match, add the note
                            if match_score > 0:
                                matching_notes.append({
                                    "path": rel_path,
                                    "name": os.path.splitext(file)[0],
                                    "size": stats.st_size,
                                    "created": stats.st_ctime,
                                    "modified": stats.st_mtime,
                                    "content": content,
                                    "match_score": match_score,
                                    "matched_by": "content" if not filename_match else "filename+content"
                                })
                        except Exception as e:
                            logger.error(f"Error reading file content: {filepath}, {e}")
                            # Still add the note without content
                            if match_score > 0:
                                matching_notes.append({
                                    "path": rel_path,
                                    "name": os.path.splitext(file)[0],
                                    "size": stats.st_size,
                                    "created": stats.st_ctime,
                                    "modified": stats.st_mtime,
                                    "match_score": match_score,
                                    "matched_by": "filename",
                                    "error": str(e)
                                })
            
            # Sort by match score (highest first)
            matching_notes.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            # Log search results
            logger.info(f"Found {len(matching_notes)} notes matching query: {query}")
            
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