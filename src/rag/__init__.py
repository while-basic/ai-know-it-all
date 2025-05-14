# ----------------------------------------------------------------------------
#  File:        __init__.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: RAG (Retrieval-Augmented Generation) module initialization
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------
"""RAG (Retrieval-Augmented Generation) for AI Know It All."""

from .retriever import DocumentRetriever
from .document import Document, DocumentChunk
from .embeddings import EmbeddingProvider

__all__ = ['DocumentRetriever', 'Document', 'DocumentChunk', 'EmbeddingProvider'] 