# ----------------------------------------------------------------------------
#  File:        test_obsidian_enhanced.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Test script for enhanced Obsidian integration features
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
from src.obsidian import ObsidianMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("obsidian_enhanced_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_daily_notes():
    """Test the daily notes feature."""
    print("=" * 50)
    print("Testing Daily Notes Feature")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get Obsidian path from environment or use default
    obsidian_path = os.getenv("OBSIDIAN_PATH", "/Users/chriscelaya/ObsidianVaults")
    
    # Create Obsidian handler
    obsidian = ObsidianMemory(obsidian_path=obsidian_path)
    
    # Create a daily note
    print("\nCreating daily note...")
    daily_note_path = obsidian.create_daily_note()
    
    if daily_note_path:
        print(f"✅ Created daily note: {daily_note_path}")
        
        # Update the daily note with a conversation link
        print("\nUpdating daily note with conversation link...")
        conversation_link = os.path.join(obsidian.memory_dir, "test_conversation.md")
        success = obsidian.update_daily_note(daily_note_path, conversation_link, "This is a test conversation summary")
        
        if success:
            print(f"✅ Updated daily note with conversation link")
        else:
            print(f"❌ Failed to update daily note with conversation link")
    else:
        print("❌ Failed to create daily note")
    
    print("\n" + "=" * 50)
    print("Daily Notes Test completed!")
    print("=" * 50)

def test_auto_linking():
    """Test the auto-linking feature."""
    print("\n" + "=" * 50)
    print("Testing Auto-Linking Feature")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get Obsidian path from environment or use default
    obsidian_path = os.getenv("OBSIDIAN_PATH", "/Users/chriscelaya/ObsidianVaults")
    
    # Create Obsidian handler
    obsidian = ObsidianMemory(obsidian_path=obsidian_path)
    
    # Test extracting concepts
    test_text = "I visited Dallas last week and met with John Smith. We discussed Machine Learning and Artificial Intelligence."
    
    print("\nExtracting concepts from text...")
    concepts = obsidian._extract_concepts(test_text)
    print(f"Extracted concepts: {concepts}")
    
    print("\nAuto-linking concepts in text...")
    linked_text = obsidian._auto_link_concepts(test_text)
    print(f"Text with auto-linked concepts: {linked_text}")
    
    print("\n" + "=" * 50)
    print("Auto-Linking Test completed!")
    print("=" * 50)

def test_collapsible_sections():
    """Test the collapsible sections feature."""
    print("\n" + "=" * 50)
    print("Testing Collapsible Sections Feature")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get memory path from environment or use default
    memory_path = os.getenv("MEMORY_PATH", "./data/memory")
    
    # Create memory handler
    memory = EnhancedVectorMemory(memory_path, use_obsidian=True)
    
    # Create LLM client with the new model
    llm_client = LLMClient(model="sushruth/solar-uncensored:latest")
    
    # Create a test conversation
    test_conversation = [
        {"role": "system", "content": "New conversation started", "timestamp": 1747208125.004056},
        {"role": "user", "content": "Tell me about Dallas and Machine Learning", "timestamp": 1747208125.396436},
        {"role": "assistant", "content": "Dallas is a city in Texas, and Machine Learning is a field of artificial intelligence.", "timestamp": 1747208158.229043}
    ]
    
    # Create retrieved memories
    retrieved_memories = [
        {"role": "user", "text": "I visited Dallas last week and it was amazing!"},
        {"role": "assistant", "text": "That's great! Dallas has many attractions like the Dallas Museum of Art."},
        {"role": "user", "text": "Machine Learning is fascinating. I'm learning about neural networks."}
    ]
    
    # Create a test note with retrieved memories
    print("\nCreating test note with collapsible sections...")
    
    # Reset the active conversation
    memory.reset_active_conversation()
    
    # Add test messages to the conversation
    for msg in test_conversation:
        memory._add_to_obsidian(msg)
    
    # Check if the note was created
    if memory.active_note_path:
        print(f"✅ Created note with collapsible sections: {memory.active_note_path}")
    else:
        print("❌ Failed to create note with collapsible sections")
    
    print("\n" + "=" * 50)
    print("Collapsible Sections Test completed!")
    print("=" * 50)

def test_enhanced_obsidian():
    """Run all tests for the enhanced Obsidian integration."""
    print("\n" + "=" * 50)
    print("Testing Enhanced Obsidian Integration")
    print("=" * 50)
    
    test_daily_notes()
    test_auto_linking()
    test_collapsible_sections()
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    test_enhanced_obsidian() 