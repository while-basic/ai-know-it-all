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
                response = "I'm sorry, I couldn't generate a proper response. Please try again."
                
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