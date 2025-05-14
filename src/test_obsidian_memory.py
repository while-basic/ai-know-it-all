# ----------------------------------------------------------------------------
#  File:        test_obsidian_memory.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Test script to verify Obsidian memory integration
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import sys
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory import VectorMemory
from src.obsidian import ObsidianMemory

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("obsidian_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_obsidian_connection():
    """Test the connection to Obsidian."""
    print("Testing Obsidian connection...")
    
    # Load environment variables
    load_dotenv()
    
    # Get Obsidian path from environment or use default
    obsidian_path = os.getenv("OBSIDIAN_PATH", "/Users/chriscelaya/ObsidianVaults")
    api_url = os.getenv("OBSIDIAN_API_URL", "127.0.0.1")
    api_port = int(os.getenv("OBSIDIAN_API_PORT", "27124"))
    api_token = os.getenv("OBSIDIAN_API_TOKEN", "35d80b834a12ecea5e21f4838722b8af8575ce7186d56176a9ba7835a0334951")
    
    # Create Obsidian memory handler
    obsidian = ObsidianMemory(
        obsidian_path=obsidian_path,
        api_url=api_url,
        api_port=api_port,
        api_token=api_token
    )
    
    # Check if API is available
    if obsidian.api_available:
        print(f"✅ Obsidian API is available at {api_url}:{api_port}")
    else:
        print(f"❌ Obsidian API is not available at {api_url}:{api_port}")
        print(f"Falling back to file system operations at {obsidian_path}")
    
    # Check if memory directory exists
    memory_dir = Path(obsidian.memory_dir)
    if memory_dir.exists():
        print(f"✅ Obsidian memory directory exists: {memory_dir}")
        
        # Count notes in memory directory
        notes = list(memory_dir.glob("*.md"))
        print(f"Found {len(notes)} notes in memory directory")
        
        # List the first 5 notes
        if notes:
            print("Recent notes:")
            for note in sorted(notes, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                print(f"  - {note.name} ({note.stat().st_size} bytes)")
    else:
        print(f"❌ Obsidian memory directory does not exist: {memory_dir}")
    
    return obsidian

def test_vector_memory():
    """Test the vector memory integration with Obsidian."""
    print("\nTesting vector memory integration with Obsidian...")
    
    # Load environment variables
    load_dotenv()
    
    # Get memory path from environment or use default
    memory_path = os.getenv("MEMORY_PATH", "./data/memory")
    
    # Create vector memory handler
    memory = VectorMemory(memory_path, use_obsidian=True)
    
    # Check if memory files exist
    index_path = Path(memory.index_path)
    metadata_path = Path(memory.metadata_path)
    
    if index_path.exists():
        print(f"✅ FAISS index exists: {index_path} ({index_path.stat().st_size} bytes)")
    else:
        print(f"❌ FAISS index does not exist: {index_path}")
    
    if metadata_path.exists():
        print(f"✅ Metadata file exists: {metadata_path} ({metadata_path.stat().st_size} bytes)")
        
        # Load metadata to check number of entries
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                print(f"Found {len(metadata)} entries in metadata file")
                
                # Check for session IDs
                session_ids = set(entry.get("session_id", "") for entry in metadata if "session_id" in entry)
                print(f"Found {len(session_ids)} unique session IDs")
                
                # Check for recent entries
                if metadata:
                    print("Recent entries:")
                    for entry in sorted(metadata, key=lambda x: x.get("timestamp", 0), reverse=True)[:3]:
                        print(f"  - Role: {entry.get('role', 'unknown')}")
                        print(f"    Text: {entry.get('text', '')[:50]}...")
                        print(f"    Session: {entry.get('session_id', 'unknown')}")
                        print(f"    Timestamp: {entry.get('timestamp', 0)}")
                        print()
        except Exception as e:
            print(f"❌ Error loading metadata: {e}")
    else:
        print(f"❌ Metadata file does not exist: {metadata_path}")
    
    # Check if Obsidian integration is working
    if hasattr(memory, "obsidian") and memory.obsidian:
        print(f"✅ Obsidian integration is enabled")
        print(f"Active note path: {memory.active_note_path}")
    else:
        print(f"❌ Obsidian integration is not enabled")
    
    return memory

def fix_obsidian_integration():
    """Fix Obsidian integration issues."""
    print("\nFixing Obsidian integration issues...")
    
    # Load environment variables
    load_dotenv()
    
    # Get memory path from environment or use default
    memory_path = os.getenv("MEMORY_PATH", "./data/memory")
    
    # Load metadata
    metadata_path = os.path.join(memory_path, "metadata.json")
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            print(f"Loaded {len(metadata)} entries from metadata file")
    except Exception as e:
        print(f"❌ Error loading metadata: {e}")
        return False
    
    # Create vector memory handler
    memory = VectorMemory(memory_path, use_obsidian=True)
    
    # Create a new conversation note with all metadata
    print("Creating new conversation note with all metadata...")
    
    # Group entries by session ID
    sessions = {}
    for entry in metadata:
        session_id = entry.get("session_id", "unknown")
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(entry)
    
    print(f"Found {len(sessions)} unique sessions")
    
    # Create a note for each session
    for session_id, entries in sessions.items():
        # Sort entries by timestamp
        sorted_entries = sorted(entries, key=lambda x: x.get("timestamp", 0))
        
        # Create a note for this session
        note_path = memory.obsidian.create_memory_note(
            sorted_entries,
            custom_filename=f"Session_{session_id}"
        )
        
        if note_path:
            print(f"✅ Created note for session {session_id}: {note_path}")
        else:
            print(f"❌ Failed to create note for session {session_id}")
    
    # Reset active conversation
    memory.reset_active_conversation()
    print("Reset active conversation")
    
    return True

def test_memory_retrieval():
    """Test memory retrieval from Obsidian."""
    print("\nTesting memory retrieval from Obsidian...")
    
    # Create vector memory handler
    memory = VectorMemory("./data/memory", use_obsidian=True)
    
    # Test queries
    test_queries = [
        "What is my name?",
        "Where do I work?",
        "What is my work schedule?",
        "What is my birthday?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Get relevant memories from vector store
        relevant_memories = memory.search(query, k=3)
        print(f"Vector memories: {len(relevant_memories)}")
        for i, mem in enumerate(relevant_memories):
            print(f"  {i+1}. {mem.get('role', 'unknown')}: {mem.get('text', '')[:50]}...")
        
        # Get relevant memories from Obsidian
        obsidian_memories = memory.get_obsidian_memories(query, limit=2)
        print(f"Obsidian memories: {len(obsidian_memories)}")
        for i, mem in enumerate(obsidian_memories):
            print(f"  {i+1}. {os.path.basename(mem.get('path', 'unknown'))}")
            content = mem.get('content', '')[:100]
            print(f"     {content}...")

def main():
    """Main function to test Obsidian memory integration."""
    print("=" * 50)
    print("Obsidian Memory Integration Test")
    print("=" * 50)
    
    # Test Obsidian connection
    obsidian = test_obsidian_connection()
    
    # Test vector memory
    memory = test_vector_memory()
    
    # Fix Obsidian integration if needed
    fix_result = fix_obsidian_integration()
    
    # Test memory retrieval
    test_memory_retrieval()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

if __name__ == "__main__":
    main() 