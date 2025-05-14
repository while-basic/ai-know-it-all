# ----------------------------------------------------------------------------
#  File:        api.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: API interactions for Obsidian integration
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""API interactions for Obsidian integration."""

import logging
import requests
import traceback
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)


class ObsidianAPI:
    """
    A class to handle API interactions with Obsidian.
    """
    def __init__(self, api_url: str = "127.0.0.1", api_port: int = 27124, 
                 api_token: str = "35d80b834a12ecea5e21f4838722b8af8575ce7186d56176a9ba7835a0334951"):
        """
        Initialize the Obsidian API handler.
        
        Args:
            api_url: URL for the Obsidian API
            api_port: Port for the Obsidian API
            api_token: Authorization token for the Obsidian API
        """
        self.api_url = api_url
        self.api_port = api_port
        self.api_token = api_token
        self.base_url = f"http://{api_url}:{api_port}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Check if API is available
        self.api_available = self._check_api_available()
        if not self.api_available:
            logger.warning("Obsidian API not available. Falling back to file system operations.")
    
    def _check_api_available(self) -> bool:
        """
        Check if the Obsidian API is available.
        
        Returns:
            True if the API is available, False otherwise
        """
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
    
    def get_all_notes(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all notes from the Obsidian vault using the API.
        
        Returns:
            List of notes or None if API is not available
        """
        if not self.api_available:
            return None
            
        try:
            response = requests.get(
                f"{self.base_url}/vault/notes",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get notes from API: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting notes from API: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    def get_note_content(self, note_path: str) -> Optional[str]:
        """
        Get the content of a note from the Obsidian vault using the API.
        
        Args:
            note_path: Path to the note
            
        Returns:
            Note content or None if API is not available
        """
        if not self.api_available:
            return None
            
        try:
            response = requests.get(
                f"{self.base_url}/vault/note",
                headers=self.headers,
                params={"path": note_path}
            )
            
            if response.status_code == 200:
                return response.json().get("content")
            else:
                logger.error(f"Failed to get note content from API: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting note content from API: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    def create_note(self, path: str, content: str) -> bool:
        """
        Create a note in the Obsidian vault using the API.
        
        Args:
            path: Path to the note
            content: Content of the note
            
        Returns:
            True if successful, False otherwise
        """
        if not self.api_available:
            return False
            
        try:
            response = requests.post(
                f"{self.base_url}/vault/create",
                headers=self.headers,
                json={"path": path, "content": content}
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Failed to create note via API: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error creating note via API: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def update_note(self, path: str, content: str) -> bool:
        """
        Update a note in the Obsidian vault using the API.
        
        Args:
            path: Path to the note
            content: New content of the note
            
        Returns:
            True if successful, False otherwise
        """
        if not self.api_available:
            return False
            
        try:
            response = requests.post(
                f"{self.base_url}/vault/update",
                headers=self.headers,
                json={"path": path, "content": content}
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Failed to update note via API: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error updating note via API: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def search_notes(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Search for notes in the Obsidian vault using the API.
        
        Args:
            query: Search query
            
        Returns:
            List of matching notes or None if API is not available
        """
        if not self.api_available:
            return None
            
        try:
            response = requests.get(
                f"{self.base_url}/vault/search",
                headers=self.headers,
                params={"query": query}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to search notes via API: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error searching notes via API: {e}")
            logger.debug(traceback.format_exc())
            return None 