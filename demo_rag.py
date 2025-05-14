# ----------------------------------------------------------------------------
#  File:        demo_rag.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Demo script for RAG implementation
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Demo script for RAG implementation."""

import os
import sys
import logging
import argparse
from pathlib import Path
import requests
from dotenv import load_dotenv

from src.rag.document import Document
from src.rag.embeddings import EmbeddingProvider
from src.rag.retriever import DocumentRetriever
from src.rag_integration import RAGManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_demo_documents(rag_manager):
    """Set up demo documents for the RAG system."""
    # Create some demo documents
    documents = [
        {
            "content": "Python is a programming language that lets you work quickly and integrate systems more effectively. "
                      "Python is an interpreted, object-oriented, high-level programming language with dynamic semantics. "
                      "Its high-level built in data structures, combined with dynamic typing and dynamic binding, "
                      "make it very attractive for Rapid Application Development.",
            "metadata": {"title": "Python", "source": "demo"}
        },
        {
            "content": "JavaScript, often abbreviated as JS, is a programming language that is one of the core technologies of the World Wide Web, "
                      "alongside HTML and CSS. As of 2022, 98% of websites use JavaScript on the client side for webpage behavior, "
                      "often incorporating third-party libraries. All major web browsers have a dedicated JavaScript engine to execute the code.",
            "metadata": {"title": "JavaScript", "source": "demo"}
        },
        {
            "content": "Retrieval-Augmented Generation (RAG) is a technique that enhances Large Language Models by providing them with external knowledge. "
                      "RAG combines the strengths of retrieval-based and generation-based approaches. "
                      "It retrieves relevant documents or passages from a knowledge base and then uses them to augment the context for the language model, "
                      "allowing it to generate more accurate and informed responses.",
            "metadata": {"title": "RAG", "source": "demo"}
        },
        {
            "content": "Obsidian is a powerful knowledge base that works on top of a local folder of plain text Markdown files. "
                      "It allows you to create a network of interconnected notes and ideas, perfect for building a personal knowledge base. "
                      "Obsidian emphasizes linking between notes, allowing you to create a web of knowledge that mimics how your brain works.",
            "metadata": {"title": "Obsidian", "source": "demo"}
        }
    ]
    
    # Add the documents to the RAG system
    for doc in documents:
        rag_manager.add_document(doc["content"], doc["metadata"])
        
    logger.info("Demo documents added to the RAG system")


def query_llm(prompt, base_url="http://localhost:11434"):
    """Query the LLM with a prompt."""
    try:
        # Use the Ollama API
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": os.getenv("MODEL_NAME", "sushruth/solar-uncensored:latest"),
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            logger.error(f"Error from LLM API: {response.status_code} - {response.text}")
            return "Error querying LLM"
    except Exception as e:
        logger.error(f"Error querying LLM: {e}")
        return "Error querying LLM"


def main():
    """Main function for the demo script."""
    parser = argparse.ArgumentParser(description="Demo script for RAG implementation")
    parser.add_argument("--setup", action="store_true", help="Set up demo documents")
    parser.add_argument("--query", type=str, help="Query to search for")
    parser.add_argument("--index-path", type=str, default="./data/rag_demo", help="Path to the index")
    args = parser.parse_args()
    
    # Create the RAG manager
    rag_manager = RAGManager(index_path=args.index_path)
    
    # Set up demo documents if requested
    if args.setup:
        setup_demo_documents(rag_manager)
        
    # Query the RAG system if requested
    if args.query:
        # Get the base prompt
        base_prompt = "You are a helpful assistant. Answer the user's question based on the context provided."
        
        # Enhance the prompt with context
        enhanced_prompt = rag_manager.enhance_prompt_with_context(args.query, base_prompt)
        
        # Print the enhanced prompt
        print("\n--- Enhanced Prompt ---\n")
        print(enhanced_prompt)
        print("\n--- End of Enhanced Prompt ---\n")
        
        # Query the LLM
        print("\n--- LLM Response ---\n")
        response = query_llm(enhanced_prompt)
        print(response)
        print("\n--- End of LLM Response ---\n")
        
    # If no arguments provided, print help
    if not args.setup and not args.query:
        parser.print_help()


if __name__ == "__main__":
    main() 