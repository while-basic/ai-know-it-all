# ----------------------------------------------------------------------------
#  File:        main.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Main entry point for the AI Know It All CLI chatbot
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

from .chat import ChatInterface

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Default to DEBUG level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai-know-it-all.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AI Know It All - CLI chatbot with long-term memory"
    )
    
    parser.add_argument(
        "--model", 
        type=str,
        help="Model name to use (default: sushruth/solar-uncensored:latest or from .env)"
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
    """Main entry point for the application."""
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
        # Create and start chat interface
        chat = ChatInterface(
            memory_path=args.memory_path,
            base_url=args.base_url,
            model=args.model,
            use_obsidian=not args.disable_obsidian
        )
        
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