# ----------------------------------------------------------------------------
#  File:        retriever.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Document retrieval for RAG implementation
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Document retrieval for RAG implementation."""

from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np
import faiss
import os
import json
import time
from pathlib import Path

from .document import DocumentChunk, Document
from .embeddings import EmbeddingProvider

# Configure logging
logger = logging.getLogger(__name__)


class DocumentRetriever:
    """A retriever for finding relevant document chunks."""
    
    def __init__(self, 
                 index_path: str = "./data/rag",
                 embedding_provider: Optional[EmbeddingProvider] = None):
        """
        Initialize the document retriever.
        
        Args:
            index_path: Path to store the FAISS index and metadata
            embedding_provider: Provider for generating embeddings
        """
        self.index_path = index_path
        self.faiss_index_path = os.path.join(index_path, "faiss_index.bin")
        self.metadata_path = os.path.join(index_path, "metadata.json")
        
        # Create the embedding provider if not provided
        if embedding_provider is None:
            self.embedding_provider = EmbeddingProvider()
        else:
            self.embedding_provider = embedding_provider
            
        # Create the index directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
        
        # Load or create the index and metadata
        self.index, self.metadata = self._load_or_create_resources()
        
    def _load_or_create_resources(self) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
        """
        Load existing index and metadata or create new ones.
        
        Returns:
            Tuple of (faiss index, metadata list)
        """
        # Create or load FAISS index
        if os.path.exists(self.faiss_index_path):
            logger.info(f"Loading existing index from {self.faiss_index_path}")
            index = faiss.read_index(self.faiss_index_path)
            
            # Load metadata
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                logger.warning(f"Metadata file not found: {self.metadata_path}")
                metadata = []
        else:
            logger.info("Creating new FAISS index")
            # Get the vector size from the embedding provider
            if hasattr(self.embedding_provider, 'vector_size'):
                vector_size = self.embedding_provider.vector_size
            else:
                # Use a default size if not available
                vector_size = 384
                
            # Create a new index
            index = faiss.IndexFlatL2(vector_size)
            metadata = []
            
        return index, metadata
        
    def _save_resources(self) -> None:
        """Save the index and metadata."""
        try:
            # Save the FAISS index
            faiss.write_index(self.index, self.faiss_index_path)
            
            # Save the metadata
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
                
            logger.info(f"Saved index and metadata to {self.index_path}")
        except Exception as e:
            logger.error(f"Error saving resources: {e}")
            
    def add_document(self, document: Document) -> bool:
        """
        Add a document to the index.
        
        Args:
            document: Document to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Make sure the document has chunks and embeddings
            if not document.chunks:
                document.split_into_chunks()
                
            # Generate embeddings if needed
            chunks_with_embeddings = []
            chunks_without_embeddings = []
            
            for chunk in document.chunks:
                if chunk.embedding is None:
                    chunks_without_embeddings.append(chunk)
                else:
                    chunks_with_embeddings.append(chunk)
                    
            # Generate embeddings for chunks without them
            if chunks_without_embeddings:
                self.embedding_provider.embed_chunks(chunks_without_embeddings)
                chunks_with_embeddings.extend(chunks_without_embeddings)
                
            # Add the chunks to the index
            embeddings = []
            for chunk in chunks_with_embeddings:
                if chunk.embedding is not None:
                    embeddings.append(chunk.embedding)
                    
                    # Add metadata
                    self.metadata.append({
                        "chunk_id": chunk.chunk_id,
                        "doc_id": chunk.metadata.get("doc_id", ""),
                        "text": chunk.text,
                        "metadata": chunk.metadata
                    })
                    
            # Convert embeddings to numpy array
            if embeddings:
                embeddings_array = np.array(embeddings).astype('float32')
                
                # Add to the index
                self.index.add(embeddings_array)
                
                # Save the updated index and metadata
                self._save_resources()
                
                logger.info(f"Added document with {len(embeddings)} chunks to the index")
                return True
            else:
                logger.warning("No valid embeddings to add to the index")
                return False
        except Exception as e:
            logger.error(f"Error adding document to index: {e}")
            return False
            
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant document chunks with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_provider.get_embeddings([query])[0]
            query_embedding_array = np.array([query_embedding]).astype('float32')
            
            # Search the index
            if self.index.ntotal == 0:
                logger.warning("Index is empty, no results to return")
                return []
                
            # Limit k to the number of items in the index
            k = min(k, self.index.ntotal)
            
            # Perform the search
            distances, indices = self.index.search(query_embedding_array, k)
            
            # Get the results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadata):
                    result = dict(self.metadata[idx])
                    result["distance"] = float(distances[0][i])
                    result["score"] = 1.0 / (1.0 + float(distances[0][i]))  # Convert distance to score
                    results.append(result)
                    
            return results
        except Exception as e:
            logger.error(f"Error searching index: {e}")
            return []
            
    def add_documents_from_directory(self, directory: str, 
                                    file_types: List[str] = [".txt", ".md"]) -> int:
        """
        Add documents from a directory to the index.
        
        Args:
            directory: Directory to scan for documents
            file_types: List of file extensions to include
            
        Returns:
            Number of documents added
        """
        try:
            # Check if the directory exists
            if not os.path.exists(directory):
                logger.error(f"Directory does not exist: {directory}")
                return 0
                
            # Scan for files
            files = []
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    if any(filename.endswith(ext) for ext in file_types):
                        files.append(os.path.join(root, filename))
                        
            logger.info(f"Found {len(files)} files to process")
            
            # Process each file
            documents_added = 0
            for file_path in files:
                try:
                    # Read the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Create a document
                    document = Document(
                        content=content,
                        metadata={
                            "filename": file_path,
                            "source_type": "file",
                            "created": time.time()
                        }
                    )
                    
                    # Add the document to the index
                    if self.add_document(document):
                        documents_added += 1
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    
            logger.info(f"Added {documents_added} documents to the index")
            return documents_added
        except Exception as e:
            logger.error(f"Error adding documents from directory: {e}")
            return 0 