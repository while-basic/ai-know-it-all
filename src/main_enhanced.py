# ----------------------------------------------------------------------------
#  File:        main_enhanced.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Enhanced main entry point with improved Obsidian integration
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

from .chat_enhanced import EnhancedChatInterface

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Default to DEBUG level
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
        description="AI Know It All Enhanced - CLI chatbot with improved Obsidian integration"
    )
    
    parser.add_argument(
        "--model", 
        type=str,
        help="Model name to use (default: llama3.2:1b or from .env)"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        help="Ollama API base URL (default: http://localhost:11434 or from .env)"
    )
    
    parser.add_argument(
        "--memory-path",
        type=str,
        help="Path to store memory (default: ./data/memory or from .env)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    # Obsidian options
    parser.add_argument(
        "--obsidian-path",
        type=str,
        help="Path to Obsidian vault (default: from .env or /Users/chriscelaya/ObsidianVaults)"
    )
    
    parser.add_argument(
        "--obsidian-api-url",
        type=str,
        help="Obsidian API URL (default: from .env or 127.0.0.1)"
    )
    
    parser.add_argument(
        "--obsidian-api-port",
        type=int,
        help="Obsidian API port (default: from .env or 27124)"
    )
    
    parser.add_argument(
        "--obsidian-api-token",
        type=str,
        help="Obsidian API token (default: from .env)"
    )
    
    parser.add_argument(
        "--disable-obsidian",
        action="store_true",
        help="Disable Obsidian integration"
    )
    
    parser.add_argument(
        "--sync-obsidian",
        action="store_true",
        help="Sync memory to Obsidian at startup"
    )
    
    return parser.parse_args()

def setup_environment(args):
    """Set up environment variables based on command line arguments."""
    # Ollama settings
    if args.model:
        os.environ["MODEL_NAME"] = args.model
        
    if args.base_url:
        os.environ["OLLAMA_BASE_URL"] = args.base_url
        
    if args.memory_path:
        os.environ["MEMORY_PATH"] = args.memory_path
        
    # Obsidian settings
    if args.obsidian_path:
        os.environ["OBSIDIAN_PATH"] = args.obsidian_path
        
    if args.obsidian_api_url:
        os.environ["OBSIDIAN_API_URL"] = args.obsidian_api_url
        
    if args.obsidian_api_port:
        os.environ["OBSIDIAN_API_PORT"] = str(args.obsidian_api_port)
        
    if args.obsidian_api_token:
        os.environ["OBSIDIAN_API_TOKEN"] = args.obsidian_api_token

def main():
    """Main entry point for the enhanced application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up environment variables
    setup_environment(args)
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Create and start enhanced chat interface
        chat = EnhancedChatInterface(
            memory_path=args.memory_path,
            base_url=args.base_url,
            model=args.model,
            use_obsidian=not args.disable_obsidian
        )
        
        # Sync memory to Obsidian if requested
        if args.sync_obsidian and not args.disable_obsidian:
            logger.info("Syncing memory to Obsidian...")
            chat.memory._sync_metadata_to_obsidian()
            logger.info("Memory sync completed")
        
        # Start the chat session
        chat.start_chat()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 