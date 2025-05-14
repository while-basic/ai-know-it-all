# ----------------------------------------------------------------------------
#  File:        chat_enhanced.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Enhanced chat interface with improved memory integration
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from colorama import Fore, Style, init
from dotenv import load_dotenv
import random
from datetime import datetime

from .memory_enhanced import EnhancedVectorMemory
from .llm import LLMClient

# Load environment variables
load_dotenv()

# Initialize colorama
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rich console for pretty output
console = Console()

# Default system prompt for the chatbot
DEFAULT_SYSTEM_PROMPT = """You are AI Know It All, a helpful and knowledgeable assistant with long-term memory.
You can remember past conversations even after the program is restarted.
Be concise, friendly, and helpful. If you don't know something, say so.
Always remember personal details about the user, especially their name. If the user tells you their name, remember it and use it in your responses.
When the user asks about something they've told you before, check your memory and recall the information accurately.
Stick to factual information and avoid making up details or hallucinating about past conversations that didn't happen.
Only reference conversations and information that are explicitly mentioned in the context provided to you.
Be respectful and professional at all times.
"""

class EnhancedChatInterface:
    """
    Enhanced interactive chat interface for the AI Know It All CLI tool.
    """
    def __init__(self, 
                 memory_path: str = "./data/memory",
                 model: str = None,
                 use_obsidian: bool = False):
        """
        Initialize the enhanced chat interface.
        
        Args:
            memory_path: Path to the memory directory
            model: Model name to use
            use_obsidian: Whether to use Obsidian integration
        """
        self.memory = EnhancedVectorMemory(memory_path, use_obsidian=use_obsidian)
        self.llm = LLMClient(model=model)
        self.system_prompt = DEFAULT_SYSTEM_PROMPT
        self.conversation_history = []
        self.use_obsidian = use_obsidian
        
        # Initialize proactive features if Obsidian is enabled
        self.proactive_assistant = None
        if use_obsidian:
            from .proactive import ProactiveAssistant
            from .obsidian import ObsidianMemory
            
            # Get Obsidian path from environment or use default
            obsidian_path = os.getenv("OBSIDIAN_PATH", "/Users/chriscelaya/ObsidianVaults")
            obsidian = ObsidianMemory(obsidian_path=obsidian_path)
            
            # Initialize proactive assistant
            self.proactive_assistant = ProactiveAssistant(
                obsidian=obsidian,
                llm_client=self.llm
            )
            
        logger.info(f"Initialized Enhanced Chat Interface with model: {self.llm.model}")
        
    def _format_user_input(self, text: str) -> None:
        """Format and print user input."""
        console.print(f"{Fore.GREEN}User: {text}{Style.RESET_ALL}")
        
    def _format_assistant_response(self, text: str) -> None:
        """Format and print assistant response."""
        console.print(Panel(Markdown(text), title="AI Know It All", border_style="blue"))
        
    def _get_context_from_memory(self, query: str, k: int = 5) -> str:
        """
        Get relevant context from memory.
        
        Args:
            query: The user's query
            k: Number of relevant memories to retrieve
            
        Returns:
            Context string from memory
        """
        relevant_memories = self.memory.search(query, k=k)
        
        if not relevant_memories:
            return ""
            
        context_parts = []
        for memory in relevant_memories:
            role_prefix = "User" if memory["role"] == "user" else "Assistant"
            context_parts.append(f"{role_prefix}: {memory['text']}")
            
        return "\n".join(context_parts)
        
    def _verify_obsidian_content(self, content: str) -> bool:
        """
        Verify that Obsidian content is legitimate and not simulation or test data.
        
        Args:
            content: The content to verify
            
        Returns:
            True if content is legitimate, False otherwise
        """
        # Patterns that indicate simulation or test content
        simulation_patterns = [
            "tick:", "type: simulation", "zombie_mode:", 
            "simulation_log", "test_data", "test file", 
            "example data", "sample data", "mock data"
        ]
        
        # Check for simulation patterns
        if any(pattern in content.lower() for pattern in simulation_patterns):
            logger.warning("Detected simulation/test content in Obsidian data")
            return False
            
        # Check for metadata block patterns that might indicate test data
        metadata_block_pattern = "---\n" in content and "\n---\n" in content
        if metadata_block_pattern:
            metadata_section = content.split("---\n")[1] if "---\n" in content else ""
            suspicious_metadata = any(key in metadata_section.lower() for key in 
                                     ["tick:", "type:", "zombie_mode:", "simulation", "test"])
            if suspicious_metadata:
                logger.warning("Detected suspicious metadata block in Obsidian content")
                return False
        
        return True
        
    def _get_context_from_obsidian(self, query: str) -> str:
        """
        Get relevant context from Obsidian notes.
        
        Args:
            query: The user's query
            
        Returns:
            Context string from Obsidian
        """
        if not self.use_obsidian:
            return ""
            
        # Search Obsidian for relevant notes
        relevant_notes = self.memory.get_obsidian_memories(query, limit=15)
        
        # If no results, try different search strategies
        if not relevant_notes:
            logger.info("No relevant notes found in Obsidian with direct query")
            
            # Strategy 1: Try a broader search with more general terms
            simplified_query = ' '.join([word for word in query.split() if len(word) > 3])
            if simplified_query and simplified_query != query:
                logger.info(f"Trying broader search with: {simplified_query}")
                relevant_notes = self.memory.get_obsidian_memories(simplified_query, limit=10)
            
            # Strategy 2: Extract key nouns and search for those
            if not relevant_notes:
                # Simple extraction of potential nouns (words starting with capital letters)
                potential_nouns = [word for word in query.split() if word and word[0].isupper()]
                if potential_nouns:
                    noun_query = ' '.join(potential_nouns)
                    logger.info(f"Trying noun search with: {noun_query}")
                    relevant_notes = self.memory.get_obsidian_memories(noun_query, limit=10)
            
            # Strategy 3: Try with just the longest words (likely more meaningful)
            if not relevant_notes:
                words = query.split()
                words.sort(key=len, reverse=True)
                if len(words) > 2:
                    longest_words = ' '.join(words[:3])  # Use the 3 longest words
                    logger.info(f"Trying search with longest words: {longest_words}")
                    relevant_notes = self.memory.get_obsidian_memories(longest_words, limit=10)
            
            # Strategy 4: Fall back to getting recent notes if all searches fail
            if not relevant_notes:
                logger.info("Falling back to recent notes")
                relevant_notes = self.memory.get_obsidian_memories(limit=5)  # Get recent notes without a query
        
        if not relevant_notes:
            return ""
            
        context_parts = ["Here are some relevant memories from Obsidian:"]
        
        for note in relevant_notes:
            # Get the full content of the note
            note_path = note.get('path', '')
            if note_path:
                content = self.memory.obsidian.get_note_content(note_path)
            else:
                content = note.get('content', '')
                
            # Skip if content is empty or appears to be simulation/test data
            if not content or not self._verify_obsidian_content(content):
                continue
                
            # If content is too long, extract the most relevant parts
            if content and len(content) > 1000:
                # First, look for sections that might match the query
                query_terms = set(word.lower() for word in query.split() if len(word) > 3)
                
                # Split content into paragraphs
                paragraphs = content.split('\n\n')
                
                # Score paragraphs by relevance to query
                scored_paragraphs = []
                for para in paragraphs:
                    if len(para.strip()) < 10:  # Skip very short paragraphs
                        continue
                        
                    # Check if paragraph is simulation/test data
                    if not self._verify_obsidian_content(para):
                        continue
                        
                    # Count matching terms
                    para_lower = para.lower()
                    matches = sum(1 for term in query_terms if term in para_lower)
                    scored_paragraphs.append((para, matches))
                
                # Sort by relevance score (highest first)
                scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
                
                # Take the top 3 most relevant paragraphs
                relevant_content = '\n\n'.join(para for para, _ in scored_paragraphs[:3])
                
                # If we couldn't find relevant paragraphs, take the beginning and some from the middle
                if not relevant_content:
                    relevant_content = paragraphs[0] + '\n\n'  # Always include the first paragraph
                    if len(paragraphs) > 2:
                        relevant_content += '...\n\n' + paragraphs[len(paragraphs)//2] + '\n\n'  # Add a middle paragraph
                    if len(paragraphs) > 5:
                        relevant_content += '...\n\n' + paragraphs[-2]  # Add a paragraph near the end
                
                content = relevant_content
            
            # Add note information to context
            context_parts.append(f"Note: {os.path.basename(note_path) if note_path else 'Untitled'}")
            context_parts.append(content if content else "No content available")
            context_parts.append("")
            
        return "\n".join(context_parts)
        
    def _build_prompt_with_memory(self, query: str) -> List[Dict[str, str]]:
        """
        Build a prompt with memory context.
        
        Args:
            query: The user's query
            
        Returns:
            List of message dicts for the LLM
        """
        # Start with recent conversation history (increased from 10 to 20 messages)
        messages = self.conversation_history[-20:] if self.conversation_history else []
        
        # Always try to find personal details like names in memory
        personal_details = self._find_personal_details_in_memory()
        if personal_details:
            messages.insert(0, {
                "role": "system",
                "content": f"Important user details: {personal_details}"
            })
        
        # Add relevant important memories if available
        important_memories = self.memory.get_relevant_important_memories(query, limit=3)
        if important_memories:
            important_content = "Here are some important memories that are relevant to the current query:\n\n"
            for i, memory in enumerate(important_memories):
                category = memory.get("category", "other")
                similarity = memory.get("similarity", 0.0)
                text = memory.get("text", "")
                
                # Only include memories with reasonable similarity
                if similarity > 0.3:
                    important_content += f"{i+1}. [{category.upper()}] {text}\n\n"
                    
            if len(important_content) > 50:  # Only add if we have meaningful content
                messages.insert(0, {
                    "role": "system",
                    "content": important_content
                })
        
        # Add context from Obsidian if available - prioritize this over vector memory
        obsidian_context = ""
        if self.use_obsidian:
            obsidian_context = self._get_context_from_obsidian(query)
            if obsidian_context:
                messages.insert(0, {
                    "role": "system",
                    "content": f"IMPORTANT OBSIDIAN CONTEXT: The following information comes from the user's Obsidian vault and should be prioritized when answering their question:\n\n{obsidian_context}"
                })
                
                # Add a specific instruction to use Obsidian content
                messages.insert(0, {
                    "role": "system",
                    "content": "You MUST use the Obsidian content provided above to answer the user's question. This content is from the user's personal knowledge base and contains the most accurate information for their query. If the answer is in the Obsidian content, use it instead of your general knowledge."
                })
        
        # Add relevant context from long-term memory
        context = self._get_context_from_memory(query)
        if context:
            # If we have Obsidian context, make it clear that vector memory is secondary
            if obsidian_context:
                messages.insert(0, {
                    "role": "system",
                    "content": f"Additional context from vector memory (use only if Obsidian content doesn't answer the question):\n\n{context}"
                })
            else:
                messages.insert(0, {
                    "role": "system",
                    "content": f"Here are some relevant memories that might help with the current query:\n\n{context}"
                })
            
        # Add a reminder to use the context provided
        messages.insert(0, {
            "role": "system",
            "content": "IMPORTANT: When answering the user's question, use the context provided above. If the user asks about information they've shared before, you MUST use the context to answer accurately. Do not say you don't have access to personal information if it's provided in the context."
        })
                
        # Add the current query
        messages.append({"role": "user", "content": query})
        
        return messages
        
    def _find_personal_details_in_memory(self) -> str:
        """
        Search memory for personal details about the user.
        
        Returns:
            String with personal details found in memory
        """
        details = self.memory.find_personal_details()
        
        if not details:
            return ""
            
        result = []
        for key, value in details.items():
            result.append(f"The user's {key} is {value}")
            
        return "\n".join(result)
        
    def start_chat(self) -> None:
        """Start the chat session."""
        print(f"\n🤖 AI Know It All (Enhanced) - Using model: {self.llm.model}")
        print("=" * 50)
        print("Type '!exit' to quit, '!help' for commands")
        print("=" * 50)
        
        # Display welcome message if proactive assistant is enabled
        if self.proactive_assistant:
            welcome_message = self.proactive_assistant.generate_welcome_message()
            print(f"\n{welcome_message}\n")
            print("=" * 50)
        
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ")
                
                # Check for exit command
                if user_input.lower() in ["!exit", "!quit", "!q"]:
                    print("\n👋 Goodbye!")
                    break
                    
                # Check for help command
                if user_input.lower() == "!help":
                    self._show_help()
                    continue
                
                # Process query and get response
                response = self.process_query(user_input)
                
                # Display response
                print(f"\n🤖 AI: {response}")
                
                # Offer proactive suggestion occasionally (1 in 3 chance)
                if self.proactive_assistant and random.random() < 0.3:
                    suggestion = self.proactive_assistant.generate_proactive_suggestion()
                    if suggestion:
                        print(f"\n💡 Suggestion: {suggestion}")
                        
                # Offer reflective prompt occasionally (1 in 5 chance)
                if self.proactive_assistant and random.random() < 0.2:
                    reflective_prompt = self.proactive_assistant.generate_reflective_prompt()
                    if reflective_prompt:
                        print(f"\n💭 Reflection: {reflective_prompt}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat session terminated by user.")
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {e}", exc_info=True)
                print(f"\n❌ Error: {str(e)}")
                
    def process_query(self, query: str) -> str:
        """
        Process a user query and generate a response.
        
        Args:
            query: The user's query
            
        Returns:
            Assistant's response
        """
        # Check for special commands
        if query.lower().startswith("!obsidian"):
            return self._handle_obsidian_command(query)
            
        # Check if this query might be about Obsidian content
        is_obsidian_related = False
        if self.use_obsidian:
            # Simple heuristic to check if the query is likely about personal notes
            obsidian_indicators = ["notes", "vault", "obsidian", "wrote", "document", "file", 
                                  "remember", "mentioned", "said", "told", "shared",
                                  "my", "i", "we", "our", "us"]
            
            query_lower = query.lower()
            if any(indicator in query_lower for indicator in obsidian_indicators):
                is_obsidian_related = True
                logger.info(f"Query appears to be Obsidian-related: {query}")
        
        # Build prompt with memory context
        messages = self._build_prompt_with_memory(query)
        
        # For Obsidian-related queries, add an extra reminder
        if is_obsidian_related:
            messages.insert(0, {
                "role": "system",
                "content": "CRITICAL INSTRUCTION: This query appears to be asking about the user's personal notes or information. You MUST prioritize information from their Obsidian vault over your general knowledge. If relevant information is found in the Obsidian context, use it as your primary source. DO NOT say you don't have access to their notes - use the context provided."
            })
        
        # Generate response
        try:
            response = self.llm.chat_completion(
                messages=messages,
                system_prompt=self.system_prompt
            )
            
            # Check if response is valid
            if not response or not isinstance(response, str):
                logger.error(f"Invalid response from LLM: {response}")
                response = "I'm sorry, I couldn't generate a proper response. Please try again."
            
            # Check for potential hallucinations in the response
            hallucination_indicators = [
                "Note:", "Tick", "tick:", "date:", "type:", "zombie_mode:",
                "simulation_log", "agent:", "created:", "---"
            ]
            
            has_hallucination = any(indicator in response for indicator in hallucination_indicators)
            
            # For Obsidian-related queries, check if the response acknowledges the content
            if is_obsidian_related and ("I don't have access" in response or has_hallucination):
                # Try again with a more forceful instruction
                messages.insert(0, {
                    "role": "system",
                    "content": "CRITICAL ERROR: Your previous response was problematic. Either you incorrectly stated you don't have access to the user's notes, or you included metadata/formatting that doesn't belong in a response. DO NOT include any 'Note:', 'Tick', or metadata blocks in your response. Answer the question using ONLY the relevant information in the context. If you truly don't see relevant information in the context, simply state that you don't have that specific information, but DO NOT say you don't have access to their notes or include any metadata formatting."
                })
                
                # Generate a new response
                response = self.llm.chat_completion(
                    messages=messages,
                    system_prompt=self.system_prompt
                )
                
                # If we still have hallucination indicators, clean the response
                if any(indicator in response for indicator in hallucination_indicators):
                    # Remove any metadata blocks
                    if "---" in response:
                        parts = response.split("---")
                        if len(parts) >= 3:
                            # Remove the metadata block
                            response = "---".join([parts[0]] + parts[2:])
                    
                    # Remove lines with hallucination indicators
                    cleaned_lines = []
                    for line in response.split("\n"):
                        if not any(indicator in line for indicator in hallucination_indicators):
                            cleaned_lines.append(line)
                    
                    response = "\n".join(cleaned_lines)
                    
                    # Add a disclaimer
                    response = "I don't have specific information about that in your notes. " + response
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": response})
                
            # Save the interaction to memory
            self.memory.add_interaction(query, response)
            
            # Try to rename the conversation after collecting enough context (at least 2 user messages)
            if self.memory.active_conversation and len([m for m in self.memory.active_conversation if m.get("role") == "user"]) >= 2:
                try:
                    self.memory.rename_conversation_note(self.llm)
                except Exception as e:
                    logger.error(f"Error renaming conversation: {e}")
                    
            # Generate insight occasionally (1 in 4 chance)
            if self.proactive_assistant and random.random() < 0.25:
                try:
                    insight = self.proactive_assistant.generate_insight(self.memory.active_conversation)
                    # We don't display the insight immediately, it will be shown in the welcome message next time
                except Exception as e:
                    logger.error(f"Error generating insight: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "I'm sorry, an error occurred while generating a response. Please try again."
        
    def _handle_obsidian_command(self, command: str) -> str:
        """
        Handle Obsidian-related commands.
        
        Args:
            command: The command string
            
        Returns:
            Response message
        """
        # Parse the command
        parts = command.split()
        if len(parts) < 2:
            return "Available Obsidian commands: list, search, import, save, sync"
            
        subcommand = parts[1].lower()
        
        try:
            if subcommand == "list":
                # List recent notes
                notes = self.memory.obsidian.get_recent_notes(limit=10)
                if not notes:
                    return "No recent notes found."
                    
                result = "Recent notes:\n"
                for note in notes:
                    result += f"- {note['title']}\n"
                return result
                
            elif subcommand == "search" and len(parts) >= 3:
                # Search notes
                query = " ".join(parts[2:])
                notes = self.memory.obsidian.search_notes(query)
                if not notes:
                    return f"No notes found for query: {query}"
                    
                result = f"Search results for '{query}':\n"
                for note in notes:
                    result += f"- {note['title']}\n"
                return result
                
            elif subcommand == "import" and len(parts) >= 3:
                # Import a note
                path = " ".join(parts[2:])
                note = self.memory.obsidian.import_note(path)
                if not note:
                    return f"Note not found: {path}"
                    
                return f"Imported note: {note['title']}"
                
            elif subcommand == "save":
                # Save current conversation
                if not self.memory.active_note_path:
                    return "No active conversation to save."
                    
                self.memory.obsidian.update_memory_note(
                    self.memory.active_note_path,
                    self.memory.active_conversation
                )
                return "Conversation saved to Obsidian."
                
            elif subcommand == "sync":
                # Sync memory to Obsidian
                self.memory.sync_to_obsidian()
                return "Memory synced to Obsidian."
                
            else:
                return "Unknown Obsidian command. Available commands: list, search, import, save, sync"
                
        except Exception as e:
            logger.error(f"Error importing Obsidian note: {e}")
            return "Error importing Obsidian note. Please check the logs for details."
            
    def _show_help(self) -> None:
        """Display help information."""
        print("\n=== AI Know It All Help ===")
        print("Available commands:")
        print("  !exit, !quit, !q - Exit the chat")
        print("  !help - Show this help message")
        print("  !obsidian - Show Obsidian commands")
        print("  !obsidian list - List recent notes")
        print("  !obsidian search <query> - Search notes")
        print("  !obsidian import <path> - Import a note")
        print("  !obsidian save - Save current conversation")
        print("  !obsidian sync - Sync memory to Obsidian")
        print("=" * 30)