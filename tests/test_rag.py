# ----------------------------------------------------------------------------
#  File:        test_rag.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Test script for RAG implementation
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""Test script for RAG implementation."""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path

# Add the parent directory to the path so we can import the src package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.rag.document import Document, DocumentChunk
from src.rag.embeddings import EmbeddingProvider
from src.rag.retriever import DocumentRetriever


class TestRAG(unittest.TestCase):
    """Test case for RAG implementation."""
    
    def setUp(self):
        """Set up the test case."""
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.test_dir, "index")
        
        # Create some test documents
        self.docs = [
            Document(
                content="Python is a programming language that lets you work quickly and integrate systems more effectively.",
                metadata={"title": "Python", "source": "test"}
            ),
            Document(
                content="JavaScript is a programming language that conforms to the ECMAScript specification.",
                metadata={"title": "JavaScript", "source": "test"}
            ),
            Document(
                content="FAISS is a library for efficient similarity search and clustering of dense vectors.",
                metadata={"title": "FAISS", "source": "test"}
            ),
            Document(
                content="Obsidian is a powerful knowledge base that works on top of a local folder of plain text Markdown files.",
                metadata={"title": "Obsidian", "source": "test"}
            )
        ]
        
        # Create the embedding provider
        self.embedding_provider = EmbeddingProvider()
        
        # Create the document retriever
        self.retriever = DocumentRetriever(
            index_path=self.index_path,
            embedding_provider=self.embedding_provider
        )
        
    def tearDown(self):
        """Clean up after the test."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_document_chunking(self):
        """Test document chunking."""
        # Create a document with content that should be split into chunks
        content = "This is the first paragraph of the document. " * 10
        content += "This is the second paragraph of the document. " * 10
        
        doc = Document(content=content, metadata={"title": "Test Document"})
        
        # Split the document into chunks
        chunks = doc.split_into_chunks(chunk_size=100, chunk_overlap=20)
        
        # Check that the document was split into chunks
        self.assertGreater(len(chunks), 1)
        
        # Check that the chunks have the correct metadata
        for i, chunk in enumerate(chunks):
            self.assertEqual(chunk.metadata["doc_id"], doc.doc_id)
            self.assertEqual(chunk.metadata["chunk_index"], i)
            
    def test_embedding_generation(self):
        """Test embedding generation."""
        # Create a document
        doc = self.docs[0]
        
        # Generate embeddings for the document
        doc = self.embedding_provider.embed_document(doc)
        
        # Check that embeddings were generated
        self.assertGreater(len(doc.chunks), 0)
        for chunk in doc.chunks:
            self.assertIsNotNone(chunk.embedding)
            self.assertGreater(len(chunk.embedding), 0)
            
    def test_document_retrieval(self):
        """Test document retrieval."""
        # Add the documents to the index
        for doc in self.docs:
            self.retriever.add_document(doc)
            
        # Search for documents
        results = self.retriever.search("Python programming language")
        
        # Check that results were returned
        self.assertGreater(len(results), 0)
        
        # Check that the first result is about Python
        self.assertIn("Python", results[0]["text"])
        

if __name__ == "__main__":
    unittest.main() 