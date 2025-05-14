# ----------------------------------------------------------------------------
#  File:        test_auto_naming.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Test script for automatic conversation naming feature
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import sys
import logging
from dotenv import load_dotenv
from pathlib import Path

# Add the current directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.memory_enhanced import EnhancedVectorMemory
from src.llm import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_naming_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_conversation_naming():
    """Test the automatic conversation naming feature."""
    print("=" * 50)
    print("Testing Automatic Conversation Naming")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get memory path from environment or use default
    memory_path = os.getenv("MEMORY_PATH", "./data/memory")
    
    # Create memory handler
    memory = EnhancedVectorMemory(memory_path, use_obsidian=True)
    
    # Create LLM client
    llm_client = LLMClient()
    
    # Create a test conversation
    test_conversation = [
        {"role": "system", "content": "New conversation started", "timestamp": 1747208125.004056},
        {"role": "user", "content": "Hello, I need help with Python programming", "timestamp": 1747208125.396436},
        {"role": "assistant", "content": "I'd be happy to help with Python programming. What specifically do you need assistance with?", "timestamp": 1747208158.229043},
        {"role": "user", "content": "I'm trying to understand how to use decorators in Python", "timestamp": 1747208158.530833}
    ]
    
    # Generate a name for the conversation
    print("\nGenerating conversation name...")
    conversation_name = memory.generate_conversation_name(test_conversation, llm_client)
    print(f"Generated name: {conversation_name}")
    
    # Create a test note
    print("\nCreating test conversation note...")
    memory._create_new_conversation_note()
    original_path = memory.active_note_path
    
    if original_path:
        print(f"Original note path: {original_path}")
        
        # Add test messages to the conversation
        for msg in test_conversation:
            if msg["role"] != "system":  # Skip the system message as it's already added
                memory._add_to_obsidian(msg)
        
        # Try to rename the note
        print("\nRenaming conversation note...")
        success = memory.rename_conversation_note(llm_client)
        
        if success:
            print(f"Successfully renamed note to: {memory.active_note_path}")
            
            # Check if the file exists
            if os.path.exists(memory.active_note_path):
                print(f"✅ New note file exists: {memory.active_note_path}")
            else:
                print(f"❌ New note file does not exist: {memory.active_note_path}")
                
            # Check if the old file is gone
            if not os.path.exists(original_path):
                print(f"✅ Original note file is gone: {original_path}")
            else:
                print(f"❌ Original note file still exists: {original_path}")
        else:
            print("❌ Failed to rename conversation note")
    else:
        print("❌ Failed to create test conversation note")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_conversation_naming() 