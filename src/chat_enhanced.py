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

class EnhancedChatInterface:
    """
    Enhanced interactive chat interface for the AI Know It All CLI tool.
    """
    def __init__(self, 
                memory_path: Optional[str] = None, 
                base_url: Optional[str] = None,
                model: Optional[str] = None,
                use_obsidian: bool = True):
        """
        Initialize the enhanced chat interface.
        
        Args:
            memory_path: Path to store memory, defaults to env var or ./data/memory
            base_url: Ollama API base URL
            model: Model name to use
            use_obsidian: Whether to use Obsidian for storing memories
        """
        memory_path = memory_path or os.getenv("MEMORY_PATH", "./data/memory")
        
        self.memory = EnhancedVectorMemory(memory_path, use_obsidian=use_obsidian)
        self.llm = LLMClient(base_url, model)
        self.conversation_history: List[Dict[str, str]] = []
        self.use_obsidian = use_obsidian
        
        # System prompt for the chatbot with enhanced memory instructions
        self.system_prompt = """You are AI Know It All, a helpful and knowledgeable assistant with long-term memory.
You can remember past conversations even after the program is restarted.
Be concise, friendly, and helpful. If you don't know something, say so.
Always remember personal details about the user, especially their name. If the user tells you their name, remember it and use it in your responses.
When the user asks about something they've told you before, check your memory and recall the information accurately.
Stick to factual information and avoid making up details or hallucinating about past conversations that didn't happen.
Only reference conversations and information that are explicitly mentioned in the context provided to you. Do not create new information or create new scenes.
Be respectful and professional at all times.
"""

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
        relevant_notes = self.memory.get_obsidian_memories(query, limit=3)
        
        if not relevant_notes:
            return ""
            
        context_parts = ["Here are some relevant memories from Obsidian:"]
        
        for note in relevant_notes:
            # Extract a snippet from the note content
            content = note.get('content', '')
            if len(content) > 500:
                content = content[:500] + "..."
                
            context_parts.append(f"Note: {os.path.basename(note.get('path', 'Unknown'))}")
            context_parts.append(content)
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
        
        # Add relevant context from long-term memory
        context = self._get_context_from_memory(query)
        if context:
            messages.insert(0, {
                "role": "system",
                "content": f"Here are some relevant memories that might help with the current query:\n\n{context}"
            })
            
        # Add context from Obsidian if available
        if self.use_obsidian:
            obsidian_context = self._get_context_from_obsidian(query)
            if obsidian_context:
                messages.insert(0, {
                    "role": "system",
                    "content": obsidian_context
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
            
        # Build prompt with memory context
        messages = self._build_prompt_with_memory(query)
        
        # Generate response
        try:
            response = self.llm.chat_completion(
                messages=messages,
                system_prompt=self.system_prompt
            )
            
            # Check if response is valid
            if not response or not isinstance(response, str):
                logger.error(f"Invalid response from LLM: {response}")
                response = "I'm sorry, I encountered an issue generating a response. Please try again."
                
            # If response starts with "Assistant:", remove it
            if response.startswith("Assistant:"):
                response = response[len("Assistant:"):].strip()
                
            # Update conversation history and memory
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Store in long-term memory
            self.memory.add_memory(query, "user")
            self.memory.add_memory(response, "assistant")
            
            # Try to rename the conversation if we have enough context
            # We need at least 2 user messages (4 total messages including system and responses)
            user_messages = [msg for msg in self.conversation_history if msg["role"] == "user"]
            if len(user_messages) >= 2:
                logger.info("Attempting to rename conversation with descriptive title...")
                renamed = self.memory.rename_conversation_note(self.llm)
                if renamed:
                    logger.info(f"Successfully renamed conversation to: {os.path.basename(self.memory.active_note_path)}")
            
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, I encountered an issue generating a response. Please try again."
        
    def _handle_obsidian_command(self, command: str) -> str:
        """
        Handle special Obsidian commands.
        
        Args:
            command: The command string
            
        Returns:
            Response message
        """
        if not self.use_obsidian:
            return "Obsidian integration is disabled."
            
        parts = command.split()
        
        if len(parts) < 2:
            return "Available Obsidian commands:\n- !obsidian list - List recent notes\n- !obsidian search <query> - Search notes\n- !obsidian import <path> - Import a note\n- !obsidian save - Save current conversation to a new note\n- !obsidian sync - Sync memory to Obsidian"
            
        action = parts[1].lower()
        
        if action == "list":
            return self._list_obsidian_notes()
        elif action == "search" and len(parts) > 2:
            search_query = " ".join(parts[2:])
            return self._search_obsidian_notes(search_query)
        elif action == "import" and len(parts) > 2:
            note_path = " ".join(parts[2:])
            return self._import_obsidian_note(note_path)
        elif action == "save":
            return self._save_conversation()
        elif action == "sync":
            return self._sync_to_obsidian()
        else:
            return "Unknown Obsidian command. Try !obsidian for help."
            
    def _sync_to_obsidian(self) -> str:
        """Sync all memory to Obsidian."""
        if not self.use_obsidian:
            return "Obsidian integration is disabled."
            
        try:
            self.memory._sync_metadata_to_obsidian()
            return "Successfully synced memory to Obsidian."
        except Exception as e:
            logger.error(f"Error syncing to Obsidian: {e}")
            return f"Error syncing to Obsidian: {str(e)}"
            
    def _save_conversation(self) -> str:
        """Save the current conversation to Obsidian."""
        if not self.use_obsidian:
            return "Obsidian integration is disabled."
            
        if not self.conversation_history:
            return "No conversation to save."
            
        success = self.memory.save_conversation_to_obsidian()
        if success:
            return "Successfully saved conversation to Obsidian."
        else:
            return "Failed to save conversation to Obsidian."
            
    def _list_obsidian_notes(self) -> str:
        """List recent Obsidian notes."""
        try:
            notes = self.memory.get_obsidian_memories(limit=5)
            
            if not notes:
                return "No notes found in Obsidian."
                
            result = ["Recent notes in Obsidian:"]
            
            for i, note in enumerate(notes, 1):
                path = note.get('path', 'Unknown')
                modified = note.get('modified', 'Unknown')
                result.append(f"{i}. {os.path.basename(path)} (Modified: {modified})")
                
            return "\n".join(result)
        except Exception as e:
            logger.error(f"Error listing Obsidian notes: {e}")
            return "Error listing Obsidian notes. Please check the logs for details."
        
    def _search_obsidian_notes(self, query: str) -> str:
        """Search Obsidian notes."""
        try:
            notes = self.memory.get_obsidian_memories(query=query)
            
            if not notes:
                return f"No notes found in Obsidian matching '{query}'."
                
            result = [f"Notes in Obsidian matching '{query}':"]
            
            for i, note in enumerate(notes, 1):
                path = note.get('path', 'Unknown')
                snippet = note.get('content', '')[:100] + "..." if note.get('content') else "No content"
                result.append(f"{i}. {os.path.basename(path)}")
                result.append(f"   {snippet}")
                
            return "\n".join(result)
        except Exception as e:
            logger.error(f"Error searching Obsidian notes: {e}")
            return "Error searching Obsidian notes. Please check the logs for details."
        
    def _import_obsidian_note(self, note_path: str) -> str:
        """Import an Obsidian note into memory."""
        try:
            success = self.memory.import_from_obsidian(note_path)
            
            if success:
                return f"Successfully imported note: {note_path}"
            else:
                return f"Failed to import note: {note_path}"
        except Exception as e:
            logger.error(f"Error importing Obsidian note: {e}")
            return "Error importing Obsidian note. Please check the logs for details."
        
    def start_chat(self) -> None:
        """Start the chat interface."""
        console.print("[bold blue]AI Know It All - Chatbot with Long-Term Memory[/bold blue]")
        console.print("Type '!exit' to quit, '!help' for help, or '!obsidian' for Obsidian commands.")
        console.print()
        
        while True:
            try:
                # Get user input
                query = Prompt.ask("[bold green]You[/bold green]")
                
                # Check for exit command
                if query.lower() in ["!exit", "!quit"]:
                    console.print("Goodbye!")
                    break
                    
                # Check for help command
                if query.lower() == "!help":
                    console.print(Panel(
                        "Available commands:\n"
                        "- !exit or !quit - Exit the chat\n"
                        "- !help - Show this help message\n"
                        "- !obsidian - Show Obsidian commands\n"
                        "- !obsidian list - List recent notes\n"
                        "- !obsidian search <query> - Search notes\n"
                        "- !obsidian import <path> - Import a note\n"
                        "- !obsidian save - Save current conversation\n"
                        "- !obsidian sync - Sync memory to Obsidian",
                        title="Help",
                        border_style="blue"
                    ))
                    continue
                    
                # Process the query
                response = self.process_query(query)
                
                # Format and print the response
                self._format_assistant_response(response)
                
            except KeyboardInterrupt:
                console.print("\nGoodbye!")
                break
                
            except Exception as e:
                logger.error(f"Error in chat loop: {e}")
                console.print(f"[bold red]Error:[/bold red] {str(e)}")