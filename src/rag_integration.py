# ----------------------------------------------------------------------------
#  File:        rag_integration.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Integration of RAG with the main application
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Integration of RAG with the main application."""

import os
import logging
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from .rag.document import Document
from .rag.embeddings import EmbeddingProvider
from .rag.retriever import DocumentRetriever

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class RAGManager:
    """Manager for RAG integration with the main application."""
    
    def __init__(self, index_path: str = "./data/rag"):
        """
        Initialize the RAG manager.
        
        Args:
            index_path: Path to store the FAISS index and metadata
        """
        self.index_path = index_path
        
        # Create the embedding provider
        use_ollama = os.getenv("USE_OLLAMA_EMBEDDINGS", "false").lower() == "true"
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.embedding_provider = EmbeddingProvider(model_name=model_name, use_ollama=use_ollama)
        
        # Create the document retriever
        self.retriever = DocumentRetriever(
            index_path=index_path,
            embedding_provider=self.embedding_provider
        )
        
        logger.info(f"Initialized RAG manager with index path: {index_path}")
        
    def add_document(self, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Add a document to the index.
        
        Args:
            content: Document content
            metadata: Document metadata
            
        Returns:
            True if successful, False otherwise
        """
        if metadata is None:
            metadata = {}
            
        # Create the document
        document = Document(content=content, metadata=metadata)
        
        # Add the document to the index
        return self.retriever.add_document(document)
        
    def add_documents_from_directory(self, directory: str, file_types: List[str] = None) -> int:
        """
        Add documents from a directory to the index.
        
        Args:
            directory: Directory to scan for documents
            file_types: List of file extensions to include
            
        Returns:
            Number of documents added
        """
        if file_types is None:
            file_types = [".txt", ".md"]
            
        return self.retriever.add_documents_from_directory(directory, file_types)
        
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant document chunks with metadata
        """
        return self.retriever.search(query, k)
        
    def get_context_for_query(self, query: str, k: int = 3, max_tokens: int = 1000) -> str:
        """
        Get context for a query to use in a prompt.
        
        Args:
            query: Search query
            k: Number of results to return
            max_tokens: Maximum number of tokens to return
            
        Returns:
            Context string for the query
        """
        # Search for relevant documents
        results = self.search(query, k)
        
        if not results:
            return "No relevant information found."
            
        # Format the results as context
        context = "Relevant information:\n\n"
        
        for i, result in enumerate(results):
            text = result.get("text", "")
            source = result.get("metadata", {}).get("filename", "Unknown")
            score = result.get("score", 0.0)
            
            # Add the result to the context
            context += f"[{i+1}] Source: {source} (Relevance: {score:.2f})\n"
            context += f"{text}\n\n"
            
            # Check if we've reached the maximum number of tokens
            if len(context) > max_tokens * 4:  # Rough approximation of tokens
                context += "... (truncated due to length)"
                break
                
        return context
        
    def enhance_prompt_with_context(self, query: str, prompt: str) -> str:
        """
        Enhance a prompt with context from relevant documents.
        
        Args:
            query: User query
            prompt: Original prompt
            
        Returns:
            Enhanced prompt with context
        """
        # Get context for the query
        context = self.get_context_for_query(query)
        
        # Add the context to the prompt
        enhanced_prompt = prompt + "\n\n"
        enhanced_prompt += "### Relevant Context\n"
        enhanced_prompt += context + "\n\n"
        enhanced_prompt += "### User Query\n"
        enhanced_prompt += query + "\n\n"
        enhanced_prompt += "Please respond to the user's query using the provided context when relevant."
        
        return enhanced_prompt 