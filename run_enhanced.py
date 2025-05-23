# ----------------------------------------------------------------------------
#  File:        run_enhanced.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Script to run the enhanced AI Know It All implementation
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

# Add the current directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.chat_enhanced import EnhancedChatInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai-know-it-all-enhanced.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Enhanced AI Know It All with improved Obsidian integration"
    )
    
    parser.add_argument(
        "--obsidian-path",
        type=str,
        help="Path to Obsidian vault (default: from .env or /Users/chriscelaya/ObsidianVaults)"
    )
    
    parser.add_argument(
        "--memory-path",
        type=str,
        help="Path to memory directory (default: ./data/memory)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="Model name to use (default: sushruth/solar-uncensored:latest or from .env)"
    )
    
    parser.add_argument(
        "--disable-obsidian",
        action="store_true",
        help="Disable Obsidian integration"
    )
    
    return parser.parse_args()

def setup_environment(args):
    """Set up environment variables based on command line arguments."""
    if args.obsidian_path:
        os.environ["OBSIDIAN_PATH"] = args.obsidian_path
        
    if args.memory_path:
        os.environ["MEMORY_PATH"] = args.memory_path
        
    if args.model:
        os.environ["MODEL_NAME"] = args.model

def main():
    """Main entry point for the script."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up environment variables
    setup_environment(args)
    
    try:
        # Start the chat interface
        memory_path = args.memory_path or os.getenv("MEMORY_PATH", "./data/memory")
        model = args.model or os.getenv("MODEL_NAME", "sushruth/solar-uncensored:latest")
        
        print("\nStarting Enhanced Chat Interface...")
        print(f"Using model: {model}")
        print(f"Memory path: {memory_path}")
        print(f"Obsidian integration: {'Enabled' if not args.disable_obsidian else 'Disabled'}")
        
        # Create and start the chat interface
        chat = EnhancedChatInterface(
            memory_path=memory_path,
            model=model,
            use_obsidian=not args.disable_obsidian
        )
        
        # Start the chat session - this will run in a continuous loop
        chat.start_chat()
        
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 