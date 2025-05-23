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
import re

from .obsidian import ObsidianMemory

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Keywords that indicate important memories
IMPORTANT_KEYWORDS = [
    "remember", "don't forget", "important", "critical", "essential",
    "favorite", "love", "hate", "dislike", "preference", "prefer",
    "allergy", "allergic", "birthday", "anniversary", "name is", "call me",
    "address", "phone", "email", "contact", "emergency", "family", "child",
    "children", "spouse", "wife", "husband", "partner", "goal", "project",
    "deadline", "meeting", "appointment", "schedule", "reminder",
    "work", "job", "career", "school", "college", "university", "degree", "major",
    "minor", "certificate", "license", "skill", "expertise", "hobby", "interest",
    "activity", "sport", "game", "movie", "tv", "music", "book", "article",
    "website", "blog", "podcast", "youtube", "instagram", "facebook", "twitter",
    "linkedin", "github", "gitlab", "bitbucket", "docker", "kubernetes", "aws",
    "azure", "google", "apple", "microsoft", "amazon", "facebook", "twitter",
    "obsidian", "vault", "note", "document", "file", "folder", "directory", "path",
    "project", "task", "todo", "list", "item", "note", "document", "file", "folder",
    "directory", "path", "project", "task", "todo", "list", "item", "note", "document",
    "file", "folder", "directory", "path", "project", "task", "todo", "list", "item",
    "note", "document", "file", "folder", "directory", "path", "project", "task", "todo",
    "list", "item", "note", "document", "file", "folder", "directory", "path", "project",
    "financial", "money", "bank", "account", "credit", "debit", "card", "payment", "invoice", "expenses", "income", "budget", "investment", "stock", "due date"
]

# Regular expressions for detecting personal information
PERSONAL_INFO_PATTERNS = {
    "name": [r"(?:my name is|call me|i am) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)", r"([A-Z][a-z]+(?: [A-Z][a-z]+)*) is my name"],
    "birthday": [r"my birthday is (\w+ \d{1,2}(?:st|nd|rd|th)?(?:,? \d{4})?)", r"born on (\w+ \d{1,2}(?:st|nd|rd|th)?(?:,? \d{4})?)"],
    "email": [r"my email is ([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"],
    "phone": [r"my (?:phone|number) is ((?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4})"],
    "location": [r"(?:i live in|i'm from|i am from) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)"],
    "job": [r"(?:i work as|i am a|i'm a) ([a-z]+(?: [a-z]+)*)"],
    "preference": [r"i (?:like|love|enjoy|prefer) ([a-z]+(?: [a-z]+)*)", r"i (?:dislike|hate|don't like) ([a-z]+(?: [a-z]+)*)"],
}

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
        self.important_memories_path = os.path.join(memory_path, "important_memories.json")
        self.use_obsidian = use_obsidian
        
        # Create model for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_size = self.model.get_sentence_embedding_dimension()
        
        # Create directory if it doesn't exist
        os.makedirs(memory_path, exist_ok=True)
        
        # Load or create index and metadata
        self.index, self.metadata = self._load_or_create_resources()
        
        # Load or create important memories
        self.important_memories = self._load_or_create_important_memories()
        
        # Initialize conversation tracking (regardless of Obsidian usage)
        self.active_conversation = []
        self.active_note_path = None
        self.session_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
        
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
        
    def _load_or_create_important_memories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load existing important memories or create new ones.
        
        Returns:
            Dictionary of important memories by category
        """
        if os.path.exists(self.important_memories_path):
            logger.info(f"Loading existing important memories from {self.important_memories_path}")
            try:
                with open(self.important_memories_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading important memories: {e}")
                return {"personal": [], "preferences": [], "events": [], "other": []}
        else:
            logger.info("Creating new important memories file")
            important_memories = {"personal": [], "preferences": [], "events": [], "other": []}
            self._save_important_memories(important_memories)
            return important_memories
            
    def _save_important_memories(self, important_memories: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Save important memories to disk.
        
        Args:
            important_memories: Dictionary of important memories by category
        """
        try:
            with open(self.important_memories_path, 'w') as f:
                json.dump(important_memories, f, indent=2)
            logger.info(f"Saved important memories to {self.important_memories_path}")
        except Exception as e:
            logger.error(f"Error saving important memories: {e}")
            
    def identify_important_memory(self, text: str, role: str = "user") -> Optional[Dict[str, Any]]:
        """
        Identify if a memory is important based on content analysis.
        
        Args:
            text: The memory text
            role: The role (user or assistant)
            
        Returns:
            Dictionary with importance info or None if not important
        """
        # Only process user messages for importance
        if role != "user":
            return None
            
        # Check for important keywords
        has_important_keyword = any(keyword in text.lower() for keyword in IMPORTANT_KEYWORDS)
        
        # Check for personal information patterns
        personal_info = {}
        for info_type, patterns in PERSONAL_INFO_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    personal_info[info_type] = matches[0]
                    break
                    
        # Determine the category
        category = "other"
        if personal_info:
            category = "personal"
        elif any(pref in text.lower() for pref in ["like", "love", "enjoy", "prefer", "dislike", "hate", "financial", "money", "bank", "account", "credit", "debit", "card", "payment", "invoice", "expenses", "income", "budget", "investment", "stock", "due date"]):
            category = "preferences"
        elif any(event in text.lower() for event in ["meeting", "appointment", "schedule", "event", "birthday", "anniversary", "due date", "bill due", "expense", "payday", "overtime", "schedule", "time off"]):
            category = "events"
            
        # If we found something important, return the info
        if has_important_keyword or personal_info:
            importance_info = {
                "text": text,
                "timestamp": time.time(),
                "category": category,
                "personal_info": personal_info,
                "has_important_keyword": has_important_keyword
            }
            
            # Add to important memories
            if category in self.important_memories:
                self.important_memories[category].append(importance_info)
            else:
                self.important_memories["other"].append(importance_info)
                
            # Save important memories
            self._save_important_memories(self.important_memories)
            
            return importance_info
            
        return None
        
    def get_relevant_important_memories(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get important memories relevant to the current query.
        
        Args:
            query: The user's query
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant important memories
        """
        # Flatten all important memories into a single list
        all_memories = []
        for category, memories in self.important_memories.items():
            for memory in memories:
                all_memories.append(memory)
                
        if not all_memories:
            return []
            
        # Get embeddings for the query and all important memories
        memory_texts = [memory["text"] for memory in all_memories]
        
        try:
            # Get embeddings
            query_embedding = self.model.encode([query])[0]
            memory_embeddings = self.model.encode(memory_texts)
            
            # Calculate similarities
            similarities = []
            for i, memory_embedding in enumerate(memory_embeddings):
                similarity = np.dot(query_embedding, memory_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(memory_embedding))
                similarities.append((similarity, i))
                
            # Sort by similarity (highest first)
            similarities.sort(reverse=True)
            
            # Return the top memories
            result = []
            for similarity, idx in similarities[:limit]:
                memory = all_memories[idx].copy()
                memory["similarity"] = float(similarity)
                result.append(memory)
                
            return result
        except Exception as e:
            logger.error(f"Error getting relevant important memories: {e}")
            return []
        
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
            
            # Create a daily note for this session
            daily_note_path = self.obsidian.create_daily_note()
            if daily_note_path:
                logger.info(f"Created/updated daily note: {daily_note_path}")
            
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
    
    def add_memory(self, text: str, role: str = "user", session_id: Optional[str] = None) -> bool:
        """
        Add a memory entry to the vector store.
        
        Args:
            text: The text to add
            role: The role (user or assistant)
            session_id: Optional session ID
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not isinstance(text, str):
            logger.warning("Invalid memory text")
            return False
            
        try:
            # Create a memory entry
            entry = self._create_memory_entry(text, role, session_id)
            
            # Check if this is an important memory
            importance_info = self.identify_important_memory(text, role)
            if importance_info:
                entry["important"] = True
                entry["importance_info"] = importance_info
                logger.info(f"Identified important memory: {importance_info['category']}")
            else:
                entry["important"] = False
            
            # Generate embedding
            embedding = self.model.encode([text])[0]
            embedding_normalized = embedding.reshape(1, -1).astype(np.float32)
            
            # Add to FAISS index
            self.index.add(embedding_normalized)
            
            # Add metadata
            entry["index"] = len(self.metadata)
            self.metadata.append(entry)
            
            # Save to disk
            self._save_resources()
            
            # Add to Obsidian if enabled
            if self.use_obsidian:
                self._add_to_obsidian(entry)
                
            return True
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            logger.debug(traceback.format_exc())
            return False
        
    def add_interaction(self, user_query: str, assistant_response: str, session_id: Optional[str] = None) -> bool:
        """
        Add a user-assistant interaction to memory.
        
        Args:
            user_query: The user's query
            assistant_response: The assistant's response
            session_id: Optional session ID
            
        Returns:
            True if successful, False otherwise
        """
        # Add user message
        user_success = self.add_memory(user_query, "user", session_id)
        
        # Add assistant message
        assistant_success = self.add_memory(assistant_response, "assistant", session_id)
        
        return user_success and assistant_success
    
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
                    
                    # Get any relevant memories for this entry
                    retrieved_memories = None
                    if entry_copy["role"] == "user":
                        # Search for relevant memories for user queries
                        retrieved_memories = self.search(entry_copy["content"], k=3)
                    
                    self.active_note_path = self.obsidian.create_memory_note(
                        self.active_conversation, 
                        custom_filename=note_title,
                        retrieved_memories=retrieved_memories
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
                        # Get any relevant memories for this entry
                        retrieved_memories = None
                        if entry_copy["role"] == "user":
                            # Search for relevant memories for user queries
                            retrieved_memories = self.search(entry_copy["content"], k=3)
                            
                        # Pass the entire conversation to update the note completely
                        success = self.obsidian.update_memory_note(
                            self.active_note_path, 
                            self.active_conversation,
                            retrieved_memories=retrieved_memories
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
                                custom_filename=note_title,
                                retrieved_memories=retrieved_memories
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
            results = []
            
            if query:
                # First, try direct search with the full query
                results = self.obsidian.search_notes(query)
                logger.info(f"Found {len(results)} Obsidian notes matching query: {query}")
                
                # If we got too few results, try additional search strategies
                if len(results) < 3:
                    # Try searching for each significant word separately and combine results
                    significant_words = [word for word in query.split() if len(word) > 3]
                    
                    for word in significant_words[:3]:  # Limit to first 3 significant words to avoid too many searches
                        word_results = self.obsidian.search_notes(word)
                        
                        # Add new results that aren't already in our list
                        for result in word_results:
                            if result not in results:
                                results.append(result)
                                
                                # Stop if we have enough results
                                if len(results) >= limit * 2:  # Get more than we need, we'll filter later
                                    break
                                    
                    logger.info(f"After word-by-word search, found {len(results)} total Obsidian notes")
                
                # If we still have few results, try a broader approach - get recent notes
                if len(results) < 3:
                    recent_notes = self.obsidian.get_recent_conversations(limit * 2)
                    
                    # Add new results that aren't already in our list
                    for note in recent_notes:
                        if note not in results:
                            results.append(note)
                            
                    logger.info(f"After adding recent notes, found {len(results)} total Obsidian notes")
                    
                # For each result, try to get the full content and score it for relevance
                scored_results = []
                query_terms = set(word.lower() for word in query.split() if len(word) > 3)
                
                for result in results:
                    # Get the content if not already present
                    if not result.get('content') and result.get('path'):
                        result['content'] = self.obsidian.get_note_content(result['path'])
                        
                    # Score the result based on content relevance to query
                    score = 0
                    content = result.get('content', '').lower()
                    
                    # Score based on query term matches
                    for term in query_terms:
                        if term in content:
                            score += content.count(term)
                            
                    # Bonus points for title matches
                    title = result.get('name', '').lower()
                    for term in query_terms:
                        if term in title:
                            score += 5  # Title matches are more important
                            
                    # Recency bonus (if we have modified time)
                    if result.get('modified'):
                        # Add a small bonus for recent notes (up to 2 points)
                        time_diff = time.time() - result.get('modified', 0)
                        if time_diff < 86400:  # Less than a day old
                            score += 2
                        elif time_diff < 604800:  # Less than a week old
                            score += 1
                            
                    scored_results.append((result, score))
                
                # Sort by relevance score (highest first)
                scored_results.sort(key=lambda x: x[1], reverse=True)
                
                # Return the top results
                return [result for result, _ in scored_results[:limit]]
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

    def _create_memory_entry(self, text: str, role: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a memory entry.
        
        Args:
            text: The text content
            role: The role (user or assistant)
            session_id: Optional session ID
            
        Returns:
            Memory entry dictionary
        """
        timestamp = time.time()
        
        if not session_id:
            session_id = getattr(self, "session_id", f"{int(timestamp)}-{self._generate_session_id()}")
            
        return {
            "text": text,
            "role": role,
            "timestamp": timestamp,
            "session_id": session_id
        }
        
    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID.
        
        Returns:
            Session ID string
        """
        import uuid
        return str(uuid.uuid4())[:8] 