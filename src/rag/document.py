# ----------------------------------------------------------------------------
#  File:        document.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Document classes for RAG implementation
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Document classes for RAG implementation."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import os
import hashlib
import time


@dataclass
class DocumentChunk:
    """A chunk of text from a document with metadata."""
    
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    chunk_id: str = ""
    
    def __post_init__(self):
        """Initialize the chunk ID if not provided."""
        if not self.chunk_id:
            # Generate a unique ID based on text and timestamp
            content_hash = hashlib.md5(self.text.encode()).hexdigest()
            timestamp = str(int(time.time() * 1000))
            self.chunk_id = f"{content_hash[:10]}_{timestamp[-6:]}"


@dataclass
class Document:
    """A document with metadata that can be split into chunks."""
    
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[DocumentChunk] = field(default_factory=list)
    doc_id: str = ""
    
    def __post_init__(self):
        """Initialize the document ID if not provided."""
        if not self.doc_id:
            # Use filename if available, otherwise generate a hash
            filename = self.metadata.get("filename", "")
            if filename:
                base_name = os.path.basename(filename)
                self.doc_id = base_name
            else:
                # Generate a unique ID based on content and timestamp
                content_hash = hashlib.md5(self.content.encode()).hexdigest()
                timestamp = str(int(time.time()))
                self.doc_id = f"doc_{content_hash[:8]}_{timestamp[-6:]}"
    
    def split_into_chunks(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[DocumentChunk]:
        """
        Split the document into chunks of specified size with overlap.
        
        Args:
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            
        Returns:
            List of document chunks
        """
        self.chunks = []
        
        # If the content is smaller than chunk_size, return a single chunk
        if len(self.content) <= chunk_size:
            chunk = DocumentChunk(
                text=self.content,
                metadata={**self.metadata, "doc_id": self.doc_id, "chunk_index": 0}
            )
            self.chunks.append(chunk)
            return self.chunks
            
        # Split the content into chunks
        start = 0
        chunk_index = 0
        
        while start < len(self.content):
            # Calculate end position
            end = start + chunk_size
            
            # Adjust end position to avoid cutting words
            if end < len(self.content):
                # Try to find a space to break at
                while end > start and self.content[end] != ' ':
                    end -= 1
                    
                # If we couldn't find a space, just use the original end
                if end == start:
                    end = start + chunk_size
                    
            # Extract the chunk text
            chunk_text = self.content[start:end]
            
            # Create a chunk
            chunk = DocumentChunk(
                text=chunk_text,
                metadata={
                    **self.metadata,
                    "doc_id": self.doc_id,
                    "chunk_index": chunk_index
                }
            )
            
            self.chunks.append(chunk)
            chunk_index += 1
            
            # Move the start position for the next chunk
            start = end - chunk_overlap
            if start < 0:
                start = 0
                
        return self.chunks 