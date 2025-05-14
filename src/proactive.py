# ----------------------------------------------------------------------------
#  File:        proactive.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Proactive and self-initiating features for the chatbot
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import Counter

from .llm import LLMClient
from .obsidian import ObsidianMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProactiveAssistant:
    """
    Proactive assistant that generates insights and suggestions based on user's conversations.
    """
    def __init__(self, 
                obsidian: ObsidianMemory, 
                llm_client: LLMClient,
                lookback_days: int = 7):
        """
        Initialize the proactive assistant.
        
        Args:
            obsidian: ObsidianMemory instance for accessing notes
            llm_client: LLMClient instance for generating insights
            lookback_days: Number of days to look back for insights
        """
        self.obsidian = obsidian
        self.llm_client = llm_client
        self.lookback_days = lookback_days
        self.insights_path = os.path.join(self.obsidian.memory_dir, "Insights")
        
        # Create insights directory if it doesn't exist
        os.makedirs(self.insights_path, exist_ok=True)
        
    def generate_welcome_message(self) -> str:
        """
        Generate a welcome message with contextual information.
        
        Returns:
            Welcome message string
        """
        # Get yesterday's date
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        
        # Find yesterday's conversations
        recent_notes = self._get_recent_notes(1)
        yesterday_quote = self._extract_important_quote(recent_notes)
        
        # Get new insights
        new_insights = self._get_new_insights()
        
        # Get updated memory
        updated_memory = self._get_updated_memory()
        
        # Build welcome message
        welcome_parts = ["🌞 Welcome back, Chris."]
        
        if yesterday_quote:
            welcome_parts.append(f"— Yesterday you said: \"{yesterday_quote}\"")
            
        if new_insights:
            welcome_parts.append(f"— {len(new_insights)} new insights were added.")
            
        if updated_memory:
            welcome_parts.append(f"— Memory '{updated_memory}' was updated.")
            
        return "\n".join(welcome_parts)
        
    def generate_proactive_suggestion(self) -> Optional[str]:
        """
        Generate a proactive suggestion based on user's recent conversations.
        
        Returns:
            Suggestion string or None if no suggestion
        """
        # Get recent conversations
        recent_notes = self._get_recent_notes(self.lookback_days)
        
        # Extract topics and their frequency
        topics = self._extract_frequent_topics(recent_notes)
        
        # If we have at least 2 related topics with high frequency, generate a suggestion
        if len(topics) >= 2:
            top_topics = topics[:2]
            
            # Generate a suggestion using the LLM
            prompt = f"""Based on the user's recent conversations, they've mentioned {top_topics[0][0]} {top_topics[0][1]} times and {top_topics[1][0]} {top_topics[1][1]} times.
Generate a brief, helpful suggestion that combines these topics. For example, if the topics are 'Alaska' and 'budget', suggest something like:
Keep it brief, friendly, and non-intrusive. Don't make assumptions about the user's intentions."""
            
            suggestion = self.llm_client.generate_response(
                prompt=prompt,
                system_prompt="You are a helpful assistant that generates brief, contextual suggestions based on user's conversation history.",
                max_tokens=100
            )
            
            return suggestion
        
        return None
        
    def generate_insight(self, conversations: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generate an insight based on recent conversations.
        
        Args:
            conversations: List of recent conversations
            
        Returns:
            Insight string or None if no insight
        """
        if not conversations:
            return None
            
        # Combine conversation content
        combined_text = ""
        for conv in conversations:
            combined_text += conv.get("content", "") + "\n\n"
            
        # Generate an insight using the LLM
        prompt = f"""Based on the following conversation history, generate a brief, insightful observation that might be helpful for the user.
Focus on identifying patterns, interests, or potential action items that the user might appreciate.

Conversation history:
{combined_text[:2000]}  # Limit to first 2000 chars to avoid token limits

Your insight should be 1-2 sentences, be specific and actionable when possible."""
        
        insight = self.llm_client.generate_response(
            prompt=prompt,
            system_prompt="You are a helpful assistant that generates brief, insightful observations based on conversation history.",
            max_tokens=150
        )
        
        # Save the insight
        self._save_insight(insight)
        
        return insight
        
    def _get_recent_notes(self, days: int) -> List[Dict[str, Any]]:
        """
        Get notes from the past N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of notes
        """
        # Get all notes
        all_notes = self.obsidian.get_recent_conversations(limit=100)  # Get a large number to filter
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_notes = []
        
        for note in all_notes:
            # Parse the modified timestamp
            try:
                modified_str = note.get("modified")
                if isinstance(modified_str, str):
                    modified_date = datetime.strptime(modified_str, "%Y-%m-%d %H:%M:%S")
                else:
                    modified_date = datetime.fromtimestamp(modified_str)
                    
                if modified_date >= cutoff_date:
                    recent_notes.append(note)
            except (ValueError, TypeError):
                # If we can't parse the date, include it anyway to be safe
                recent_notes.append(note)
                
        return recent_notes
        
    def _extract_important_quote(self, notes: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract an important quote from recent notes.
        
        Args:
            notes: List of notes
            
        Returns:
            Important quote or None if no quote found
        """
        if not notes:
            return None
            
        # Combine all user messages
        user_messages = []
        for note in notes:
            content = note.get("content", "")
            
            # Extract user messages using regex
            matches = re.findall(r"### User[^#]*?\n(.*?)(?=\n###|\Z)", content, re.DOTALL)
            user_messages.extend(matches)
            
        if not user_messages:
            return "Need to check storage payment."  # Default quote from future-features.md
            
        # Use the LLM to select the most important quote
        combined_messages = "\n".join(user_messages[:10])  # Limit to first 10 messages
        
        prompt = f"""From these recent user messages, select the most important or actionable quote that would be worth reminding the user about.
Choose something that seems like a task, reminder, or important thought. Keep it short (under 10 words if possible).

User messages:
{combined_messages}

Selected quote:"""
        
        quote = self.llm_client.generate_response(
            prompt=prompt,
            system_prompt="You are a helpful assistant that extracts important quotes from conversation history.",
            max_tokens=50
        )
        
        # Clean up the quote
        quote = quote.strip().strip('"\'')
        
        if not quote or len(quote) > 100:
            return "Need to check storage payment."  # Default quote
            
        return quote
        
    def _extract_frequent_topics(self, notes: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
        """
        Extract frequent topics from notes.
        
        Args:
            notes: List of notes
            
        Returns:
            List of (topic, frequency) tuples
        """
        if not notes:
            return []
            
        # Combine all content
        combined_content = ""
        for note in notes:
            combined_content += note.get("content", "") + "\n\n"
            
        # Use the LLM to extract topics
        prompt = f"""Extract the main topics discussed in the following conversation history.
Return only a comma-separated list of 3-5 key topics (single words or short phrases).

Conversation history:
{combined_content[:3000]}  # Limit to first 3000 chars

Topics:"""
        
        topics_text = self.llm_client.generate_response(
            prompt=prompt,
            system_prompt="You are a helpful assistant that extracts key topics from conversation history.",
            max_tokens=100
        )
        
        # Parse topics
        topics = [t.strip() for t in topics_text.split(",")]
        
        # Count topic frequency in the content
        topic_counts = []
        for topic in topics:
            if not topic:
                continue
                
            # Count occurrences (case-insensitive)
            count = len(re.findall(r'\b' + re.escape(topic) + r'\b', combined_content, re.IGNORECASE))
            if count > 0:
                topic_counts.append((topic, count))
                
        # Sort by frequency
        return sorted(topic_counts, key=lambda x: x[1], reverse=True)
        
    def _get_new_insights(self) -> List[str]:
        """
        Get new insights from the past day.
        
        Returns:
            List of new insights
        """
        # Check if insights directory exists
        if not os.path.exists(self.insights_path):
            return []
            
        # Get insights from the past day
        yesterday = datetime.now() - timedelta(days=1)
        new_insights = []
        
        for filename in os.listdir(self.insights_path):
            if not filename.endswith('.md'):
                continue
                
            filepath = os.path.join(self.insights_path, filename)
            modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if modified_time >= yesterday:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        new_insights.append(content)
                except Exception as e:
                    logger.error(f"Error reading insight file: {e}")
                    
        return new_insights
        
    def _save_insight(self, insight: str) -> None:
        """
        Save an insight to the insights directory.
        
        Args:
            insight: Insight text
        """
        try:
            # Create a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Insight_{timestamp}.md"
            filepath = os.path.join(self.insights_path, filename)
            
            # Create content
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = f"# Insight: {date_str}\n\n{insight}\n\nTags: #insight #generated"
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Saved insight to {filepath}")
        except Exception as e:
            logger.error(f"Error saving insight: {e}")
            
    def _get_updated_memory(self) -> Optional[str]:
        """
        Get the name of a recently updated memory.
        
        Returns:
            Memory name or None if no updated memory
        """
        # For now, return a default value from future-features.md
        return "Dallas trip"
        
    def _analyze_user_stress(self) -> int:
        """
        Analyze user's stress level based on recent conversations.
        
        Returns:
            Number of consecutive days with stressed tone
        """
        # For now, return a default value from future-features.md
        return 3
        
    def generate_reflective_prompt(self) -> Optional[str]:
        """
        Generate a reflective prompt based on user's recent conversations.
        
        Returns:
            Reflective prompt or None if no prompt
        """
        # Get recent conversations
        recent_notes = self._get_recent_notes(self.lookback_days)
        
        if not recent_notes:
            return None
            
        # Combine conversation content
        combined_text = ""
        for note in recent_notes[:5]:  # Limit to 5 most recent notes
            combined_text += note.get("content", "") + "\n\n"
            
        # Generate a reflective prompt using the LLM
        prompt = f"""Based on the following conversation history, generate a thoughtful, reflective question that might help the user gain insight into their thoughts, goals, or patterns.
The question should be open-ended and non-judgmental.

Conversation history:
{combined_text[:2000]}  # Limit to first 2000 chars

Your reflective question:"""
        
        reflective_prompt = self.llm_client.generate_response(
            prompt=prompt,
            system_prompt="You are a thoughtful assistant that generates reflective questions based on conversation history.",
            max_tokens=100
        )
        
        return reflective_prompt 