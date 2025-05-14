# ----------------------------------------------------------------------------
#  File:        embeddings.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Embedding generation for RAG implementation
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Embedding generation for RAG implementation."""

from typing import List, Dict, Any, Optional, Union
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
import requests
import json
import os
from dotenv import load_dotenv

from .document import DocumentChunk, Document

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """A provider for generating embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_ollama: bool = False):
        """
        Initialize the embedding provider.
        
        Args:
            model_name: Name of the embedding model to use
            use_ollama: Whether to use Ollama for embeddings
        """
        self.model_name = model_name
        self.use_ollama = use_ollama
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Initialize the model if not using Ollama
        if not use_ollama:
            try:
                self.model = SentenceTransformer(model_name)
                self.vector_size = self.model.get_sentence_embedding_dimension()
                logger.info(f"Initialized embedding model: {model_name}")
            except Exception as e:
                logger.error(f"Error initializing embedding model: {e}")
                raise
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embeddings
        """
        if not texts:
            return []
            
        if self.use_ollama:
            return self._get_ollama_embeddings(texts)
        else:
            return self._get_local_embeddings(texts)
    
    def _get_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using the local model.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embeddings
        """
        try:
            embeddings = self.model.encode(texts)
            # Convert numpy arrays to lists
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * self.vector_size] * len(texts)
    
    def _get_ollama_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Ollama.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embeddings
        """
        embeddings = []
        
        try:
            for text in texts:
                response = requests.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={"model": self.model_name, "prompt": text}
                )
                
                if response.status_code == 200:
                    embedding = response.json().get("embedding", [])
                    embeddings.append(embedding)
                else:
                    logger.error(f"Error from Ollama API: {response.status_code} - {response.text}")
                    # Add a zero vector as a placeholder
                    embeddings.append([0.0] * 384)  # Default size for many embedding models
        except Exception as e:
            logger.error(f"Error generating embeddings with Ollama: {e}")
            # Add zero vectors as placeholders
            embeddings = [[0.0] * 384 for _ in range(len(texts))]
            
        return embeddings
    
    def embed_document(self, document: Document) -> Document:
        """
        Generate embeddings for a document's chunks.
        
        Args:
            document: Document to generate embeddings for
            
        Returns:
            Document with embeddings added to chunks
        """
        # Make sure the document has chunks
        if not document.chunks:
            document.split_into_chunks()
            
        # Get all chunk texts
        texts = [chunk.text for chunk in document.chunks]
        
        # Generate embeddings
        embeddings = self.get_embeddings(texts)
        
        # Add embeddings to chunks
        for i, embedding in enumerate(embeddings):
            if i < len(document.chunks):
                document.chunks[i].embedding = embedding
                
        return document
    
    def embed_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Generate embeddings for a list of document chunks.
        
        Args:
            chunks: List of document chunks to generate embeddings for
            
        Returns:
            List of document chunks with embeddings added
        """
        # Get all chunk texts
        texts = [chunk.text for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.get_embeddings(texts)
        
        # Add embeddings to chunks
        for i, embedding in enumerate(embeddings):
            if i < len(chunks):
                chunks[i].embedding = embedding
                
        return chunks 