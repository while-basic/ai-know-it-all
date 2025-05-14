# ----------------------------------------------------------------------------
#  File:        memory_enhanced.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Enhanced vector memory storage with improved Obsidian integration
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

class EnhancedVectorMemory:
    """
    Enhanced version of VectorMemory with improved Obsidian integration.
    """
    def __init__(self, memory_path: str = "./data/memory", use_obsidian: bool = True):
        """
        Initialize the enhanced vector memory.
        
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
            
            # Sync existing metadata to Obsidian if needed
            self._sync_metadata_to_obsidian()
        
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
        
    def _sync_metadata_to_obsidian(self) -> None:
        """
        Sync existing metadata to Obsidian if it's not already there.
        This ensures that all vector memories are also stored in Obsidian.
        """
        if not self.use_obsidian or not self.obsidian:
            return
            
        try:
            logger.info("Checking if metadata needs to be synced to Obsidian...")
            
            # Get all notes in Obsidian
            obsidian_notes = self.obsidian.get_all_notes()
            
            # If there are no notes in Obsidian but we have metadata, sync it
            if not obsidian_notes and self.metadata:
                logger.info("No notes found in Obsidian but metadata exists. Syncing...")
                
                # Group entries by session ID
                sessions = {}
                for entry in self.metadata:
                    session_id = entry.get("session_id", "unknown")
                    if session_id not in sessions:
                        sessions[session_id] = []
                    sessions[session_id].append(entry)
                
                logger.info(f"Found {len(sessions)} unique sessions to sync")
                
                # Create a note for each session
                for session_id, entries in sessions.items():
                    # Sort entries by timestamp
                    sorted_entries = sorted(entries, key=lambda x: x.get("timestamp", 0))
                    
                    # Create a note for this session
                    note_path = self.obsidian.create_memory_note(
                        sorted_entries,
                        custom_filename=f"Session_{session_id}"
                    )
                    
                    if note_path:
                        logger.info(f"Created note for session {session_id}: {note_path}")
                    else:
                        logger.error(f"Failed to create note for session {session_id}")
                        
                logger.info("Metadata sync to Obsidian completed")
            else:
                logger.info("Obsidian already has notes or no metadata to sync")
        except Exception as e:
            logger.error(f"Error syncing metadata to Obsidian: {e}")
            logger.debug(traceback.format_exc())
        
    def _create_new_conversation_note(self, llm_client=None) -> None:
        """
        Create a new conversation note in Obsidian.
        
        Args:
            llm_client: Optional LLM client for generating a name (not used initially)
        """
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
            
            # Default note title with timestamp
            timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
            note_title = f"Conversation_{timestamp_filename}"
            
            # We'll rename the note later when we have enough context
            
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
            
            # Create a new note if we don't have one yet
            if not self.active_note_path:
                try:
                    # Generate a unique filename with timestamp
                    timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
                    note_title = f"Conversation_{timestamp_filename}"
                    
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
        if not self.use_obsidian or not hasattr(self, "obsidian") or not self.obsidian:
            return []
            
        try:
            if query:
                # Search for specific memories
                results = self.obsidian.search_notes(query)
                logger.info(f"Found {len(results)} Obsidian notes matching query: {query}")
                return results[:limit]
            else:
                # Get recent conversations
                results = self.obsidian.get_recent_conversations(limit)
                logger.info(f"Retrieved {len(results)} recent conversations from Obsidian")
                return results
        except Exception as e:
            logger.error(f"Error retrieving Obsidian memories: {e}")
            logger.debug(traceback.format_exc())
            return []
            
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
            
    def find_personal_details(self) -> Dict[str, str]:
        """
        Find personal details about the user in memory.
        
        Returns:
            Dictionary of personal details
        """
        details = {}
        
        # Patterns to look for
        name_patterns = ["my name is", "I'm", "I am", "call me"]
        
        # Search for name in metadata
        for memory in self.metadata:
            if memory["role"] != "user":
                continue
                
            text = memory.get("text", "").lower()
            
            # Look for name patterns
            for pattern in name_patterns:
                if pattern in text:
                    index = text.find(pattern) + len(pattern)
                    # Extract what might be the name (up to 20 chars after the pattern)
                    name_text = memory["text"][index:index + 20].strip()
                    if name_text and len(name_text) > 1:
                        # Clean up the name - remove punctuation at the end
                        if name_text[-1] in ['.', ',', '!', '?', ';', ':']:
                            name_text = name_text[:-1]
                        details["name"] = name_text
                        break
                        
            # If we found a name, stop searching
            if "name" in details:
                break
                
        # Also search in Obsidian if we didn't find a name
        if "name" not in details and self.use_obsidian:
            try:
                # Search for name patterns in Obsidian
                for pattern in name_patterns:
                    notes = self.obsidian.search_notes(pattern)
                    
                    for note in notes:
                        content = note.get("content", "")
                        if not content:
                            continue
                            
                        # Look for the pattern in the content
                        content_lower = content.lower()
                        pattern_index = content_lower.find(pattern)
                        
                        if pattern_index >= 0:
                            # Extract what might be the name
                            index = pattern_index + len(pattern)
                            name_text = content[index:index + 20].strip()
                            if name_text and len(name_text) > 1:
                                # Clean up the name - remove punctuation at the end
                                if name_text[-1] in ['.', ',', '!', '?', ';', ':']:
                                    name_text = name_text[:-1]
                                details["name"] = name_text
                                break
                                
                    # If we found a name, stop searching
                    if "name" in details:
                        break
            except Exception as e:
                logger.error(f"Error searching for personal details in Obsidian: {e}")
                
        return details

    def generate_conversation_name(self, messages: List[Dict[str, Any]], llm_client) -> str:
        """
        Generate a meaningful name for the conversation using the LLM.
        
        Args:
            messages: List of conversation messages
            llm_client: LLM client to use for generating the name
            
        Returns:
            Generated conversation name
        """
        try:
            # Filter out system messages and get the most recent messages
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            
            # If we don't have enough user messages, use a default name with timestamp
            if len(user_messages) < 1:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"Conversation_{timestamp}"
                
            # Create a prompt for the LLM to generate a name
            prompt = "Based on this conversation, generate a short, descriptive title (3-6 words) that captures the main topic:\n\n"
            
            # Add the most recent messages to the prompt (up to 3)
            for msg in user_messages[-3:]:
                prompt += f"User: {msg.get('text', msg.get('content', ''))}\n"
                
            # Generate a name using the LLM
            response = llm_client.generate_response(
                prompt=prompt,
                system_prompt="You are a helpful assistant that generates short, descriptive titles for conversations. Generate only the title, no quotes or explanations.",
                max_tokens=20
            )
            
            # Clean up the response
            name = response.strip().strip('"\'').strip()
            
            # If the name is empty or too long, use a default name
            if not name or len(name) > 50:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return f"Conversation_{timestamp}"
                
            # Replace spaces with underscores and remove invalid characters
            name = name.replace(' ', '_')
            invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            for char in invalid_chars:
                name = name.replace(char, '')
                
            # Add timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%Y%m%d")
            return f"{timestamp}_{name}"
            
        except Exception as e:
            logger.error(f"Error generating conversation name: {e}")
            logger.debug(traceback.format_exc())
            
            # Return a default name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"Conversation_{timestamp}"

    def rename_conversation_note(self, llm_client) -> bool:
        """
        Rename the conversation note with a more descriptive name using the LLM.
        
        Args:
            llm_client: LLM client to use for generating the name
            
        Returns:
            True if successful, False otherwise
        """
        if not self.use_obsidian or not self.active_note_path or not self.active_conversation:
            return False
            
        try:
            # Check if we have enough user messages
            user_messages = [msg for msg in self.active_conversation if msg.get("role") == "user"]
            if len(user_messages) < 2:
                return False  # Not enough context yet
                
            # Generate a name for the conversation
            new_name = self.generate_conversation_name(self.active_conversation, llm_client)
            
            # Get the current note path and directory
            current_path = self.active_note_path
            note_dir = os.path.dirname(current_path)
            
            # Create the new path
            new_path = os.path.join(note_dir, f"{new_name}.md")
            
            # Check if the new path already exists
            if os.path.exists(new_path):
                # Add a unique identifier to avoid conflicts
                timestamp = datetime.now().strftime("%H%M%S")
                new_path = os.path.join(note_dir, f"{new_name}_{timestamp}.md")
            
            try:
                # Rename the file
                os.rename(current_path, new_path)
                
                # Update the active note path
                self.active_note_path = new_path
                
                logger.info(f"Renamed conversation note to: {os.path.basename(new_path)}")
                return True
            except Exception as e:
                logger.error(f"Error renaming conversation note: {e}")
                logger.debug(traceback.format_exc())
                return False
        except Exception as e:
            logger.error(f"Error in rename_conversation_note: {e}")
            logger.debug(traceback.format_exc())
            return False 