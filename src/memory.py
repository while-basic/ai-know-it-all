# ----------------------------------------------------------------------------
#  File:        memory.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Vector memory storage using FAISS for persistent chat history
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Tuple
import logging
import time
import uuid
from datetime import datetime
from dotenv import load_dotenv
import traceback

from .obsidian import ObsidianMemory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorMemory:
    """
    A class to handle vector storage and retrieval for chat memory using FAISS.
    """
    def __init__(self, memory_path: str = "./data/memory", use_obsidian: bool = True):
        """
        Initialize the vector memory.
        
        Args:
            memory_path: Path to store the vector database and metadata
            use_obsidian: Whether to use Obsidian for storing memories
        """
        self.memory_path = memory_path
        self.index_path = os.path.join(memory_path, "faiss_index.bin")
        self.metadata_path = os.path.join(memory_path, "metadata.json")
        self.use_obsidian = use_obsidian
        
        # Create model for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_size = self.model.get_sentence_embedding_dimension()
        
        # Create directory if it doesn't exist
        os.makedirs(memory_path, exist_ok=True)
        
        # Load or create index and metadata
        self.index, self.metadata = self._load_or_create_resources()
        
        # Initialize Obsidian if enabled
        if use_obsidian:
            obsidian_path = os.getenv("OBSIDIAN_PATH", "/Users/chriscelaya/ObsidianVaults")
            api_url = os.getenv("OBSIDIAN_API_URL", "127.0.0.1")
            api_port = int(os.getenv("OBSIDIAN_API_PORT", "27124"))
            api_token = os.getenv("OBSIDIAN_API_TOKEN", "35d80b834a12ecea5e21f4838722b8af8575ce7186d56176a9ba7835a0334951")
            
            self.obsidian = ObsidianMemory(
                obsidian_path=obsidian_path,
                api_url=api_url,
                api_port=api_port,
                api_token=api_token
            )
            
            # Track active conversation for Obsidian notes
            self.active_conversation = []
            self.active_note_path = None
            
            # Create a unique session ID for this conversation
            self.session_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
            
            # Create a new conversation note at startup
            self._create_new_conversation_note()
        
    def _load_or_create_resources(self) -> Tuple[faiss.IndexFlatL2, List[Dict[str, Any]]]:
        """
        Load existing index and metadata or create new ones.
        
        Returns:
            Tuple of (faiss index, metadata list)
        """
        # Create or load FAISS index
        if os.path.exists(self.index_path):
            logger.info(f"Loading existing index from {self.index_path}")
            index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            logger.info("Creating new FAISS index")
            index = faiss.IndexFlatL2(self.vector_size)
            metadata = []
            
        return index, metadata
        
    def _create_new_conversation_note(self) -> None:
        """Create a new conversation note in Obsidian."""
        if not self.use_obsidian:
            return
            
        try:
            # Create initial conversation note with timestamp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            initial_content = {
                "role": "system",
                "content": f"New conversation started at {timestamp}",
                "text": f"New conversation started at {timestamp}",
                "timestamp": time.time()
            }
            
            # Reset active conversation
            self.active_conversation = [initial_content]
            
            # Create the note with timestamp in filename for uniqueness
            timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
            note_title = f"Conversation_{timestamp_filename}"
            
            try:
                # Create the note
                self.active_note_path = self.obsidian.create_memory_note(
                    self.active_conversation, 
                    custom_filename=note_title
                )
                
                if self.active_note_path:
                    logger.info(f"Created new conversation note: {self.active_note_path}")
                else:
                    logger.error("Failed to create new conversation note in Obsidian")
            except Exception as inner_e:
                logger.error(f"Exception creating conversation note: {str(inner_e)}")
                logger.debug(traceback.format_exc())
                # Set active_note_path to None to indicate failure
                self.active_note_path = None
        except Exception as e:
            logger.error(f"Error creating conversation note: {e}")
            logger.debug(traceback.format_exc())
            # Set active_note_path to None to indicate failure
            self.active_note_path = None
    
    def add_memory(self, text: str, role: str, timestamp: Optional[float] = None) -> None:
        """
        Add a new memory entry to the vector store.
        
        Args:
            text: The text content to remember
            role: The role of the speaker (user or assistant)
            timestamp: Optional timestamp, defaults to current time
        """
        if not text.strip():
            return
            
        # Generate embedding
        embedding = self.model.encode([text])[0]
        embedding_normalized = embedding.reshape(1, -1).astype(np.float32)
        
        # Add to FAISS index
        self.index.add(embedding_normalized)
        
        # Add metadata
        if timestamp is None:
            timestamp = time.time()
            
        metadata_entry = {
            "text": text,
            "role": role,
            "timestamp": timestamp,
            "index": len(self.metadata),
            "session_id": getattr(self, "session_id", f"{int(timestamp)}")
        }
        self.metadata.append(metadata_entry)
        
        # Save to disk
        self._save_resources()
        
        # Add to Obsidian if enabled
        if self.use_obsidian:
            self._add_to_obsidian(metadata_entry)
        
    def _add_to_obsidian(self, entry: Dict[str, Any]) -> None:
        """
        Add a memory entry to Obsidian.
        
        Args:
            entry: The memory entry to add
        """
        try:
            # Make a copy of the entry to avoid modifying the original
            entry_copy = entry.copy()
            
            # Ensure the entry has a content field (Obsidian expects this)
            if "content" not in entry_copy and "text" in entry_copy:
                entry_copy["content"] = entry_copy["text"]
                
            # Add to active conversation
            self.active_conversation.append(entry_copy)
            
            # If this is the first message in a conversation, create a new note
            if len(self.active_conversation) <= 1 or self.active_note_path is None:
                timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
                note_title = f"Conversation_{timestamp_filename}"
                
                try:
                    self.active_note_path = self.obsidian.create_memory_note(
                        self.active_conversation,
                        custom_filename=note_title
                    )
                    
                    if self.active_note_path:
                        logger.info(f"Created new memory note: {self.active_note_path}")
                    else:
                        logger.error("Failed to create memory note in Obsidian")
                except Exception as e:
                    logger.error(f"Exception creating memory note: {str(e)}")
                    logger.debug(traceback.format_exc())
            else:
                # Otherwise update the existing note
                if self.active_note_path:
                    try:
                        # Pass the entire conversation to update the note completely
                        success = self.obsidian.update_memory_note(
                            self.active_note_path, 
                            self.active_conversation
                        )
                        
                        if success:
                            logger.debug(f"Updated memory note: {self.active_note_path}")
                        else:
                            logger.warning(f"Failed to update memory note: {self.active_note_path}")
                            # Try to create a new note as fallback
                            timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
                            note_title = f"Conversation_{timestamp_filename}"
                            
                            self.active_note_path = self.obsidian.create_memory_note(
                                self.active_conversation,
                                custom_filename=note_title
                            )
                            
                            if self.active_note_path:
                                logger.info(f"Created new fallback memory note: {self.active_note_path}")
                    except Exception as e:
                        logger.error(f"Exception updating memory note: {str(e)}")
                        logger.debug(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error adding to Obsidian: {e}")
            logger.debug(traceback.format_exc())
                
    def reset_active_conversation(self) -> None:
        """Reset the active conversation for a new session."""
        self.active_conversation = []
        self.active_note_path = None
        self.session_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        
        # Create a new conversation note
        if self.use_obsidian:
            self._create_new_conversation_note()
        
    def _save_resources(self) -> None:
        """Save the index and metadata to disk."""
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f)
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar memories.
        
        Args:
            query: The query text
            k: Number of results to return
            
        Returns:
            List of metadata entries for the most relevant memories
        """
        if self.index.ntotal == 0:
            return []
            
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        
        # Search the index
        k = min(k, self.index.ntotal)  # Don't request more than we have
        distances, indices = self.index.search(query_embedding, k)
        
        # Get metadata for results
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.metadata):
                results.append(self.metadata[idx])
                
        return results
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most recent memories.
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of the most recent memory entries
        """
        sorted_metadata = sorted(
            self.metadata, 
            key=lambda x: x.get("timestamp", 0),
            reverse=True
        )
        return sorted_metadata[:limit]
    
    def get_conversation_history(self, limit: int = 100) -> str:
        """
        Get formatted conversation history.
        
        Args:
            limit: Maximum number of messages to include
            
        Returns:
            Formatted conversation history string
        """
        recent = self.get_recent_memories(limit)
        recent.reverse()  # Chronological order
        
        history = []
        for entry in recent:
            prefix = "User: " if entry["role"] == "user" else "Assistant: "
            history.append(f"{prefix}{entry['text']}")
            
        return "\n".join(history)
    
    def get_obsidian_memories(self, query: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get memories from Obsidian.
        
        Args:
            query: Optional search query
            limit: Maximum number of results to return
            
        Returns:
            List of memories from Obsidian
        """
        if not self.use_obsidian:
            return []
            
        if query:
            # Search for specific memories
            return self.obsidian.search_notes(query)
        else:
            # Get recent conversations
            return self.obsidian.get_recent_conversations(limit)
            
    def import_from_obsidian(self, note_path: str) -> bool:
        """
        Import a conversation from an Obsidian note into the vector memory.
        
        Args:
            note_path: Path to the note
            
        Returns:
            True if successful, False otherwise
        """
        if not self.use_obsidian:
            return False
            
        # Get note content
        content = self.obsidian.get_note_content(note_path)
        if not content:
            return False
            
        # Extract conversation
        messages = self.obsidian.extract_conversation_from_note(content)
        
        # Add each message to vector memory
        for msg in messages:
            self.add_memory(msg["content"], msg["role"])
            
        return True
        
    def save_conversation_to_obsidian(self) -> bool:
        """
        Save the current conversation to Obsidian.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.use_obsidian or not self.active_conversation:
            return False
            
        try:
            # Generate a unique filename with timestamp
            timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
            note_title = f"Conversation_{timestamp_filename}"
            
            # Create a new note with the active conversation
            note_path = self.obsidian.create_memory_note(
                self.active_conversation,
                custom_filename=note_title
            )
            
            return note_path is not None
        except Exception as e:
            logger.error(f"Error saving conversation to Obsidian: {e}")
            return False 