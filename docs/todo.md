# TODO

## Incompleted Tasks

- Add a feature to the flask interface to allow the user to change Ollama models.
- Combine all README.md files into a single README.md in the root directory.
- Make chat interface background to all black.

## Completed Tasks

✅ When user creates a new document in "Users/chriscelaya/ObsidianVaults/ai-know-it-all", the AI should be aware of these files.
✅ Add values to memories that are important to have the AI mention context that is relevant to the user.
✅ Improve chat interface.
✅ Optimize program for production.
✅ Build Flask frontend chat interface.
✅ Improve system prompt.
✅ Refactor large files, more than 300 lines of code.
✅ Move all tests to a tests folder.
✅ Remove context about stress and Dallas as it is not relevant to me. These are hardcoded and should not be. Instead, the AI should query what we discussed the day/week before and generate a response based off that context.
✅ Add RAG
✅ Add support for adding new lines. When the user uses (shift+enter), a new line should be created rather than submitting the users query.
✅ Update memory path (Obsidian Vault) to "Users/chriscelaya/ObsidianVaults/ai-know-it-all"
✅ Add markdown rendering for assistant messages
✅ Add code syntax highlighting
✅ Add copy to clipboard button for assistant messages
✅ Add dark/light mode toggle with system preference detection
✅ Add auto-resizing textarea for input
✅ Add export chat functionality
✅ Add voice input for dictating messages
✅ Add browser notifications for new messages when tab is not active
✅ When user creates a new document in "Users/chriscelaya/ObsidianVaults/ai-know-it-all", the AI should be aware of these files.
✅ Add values to memories that are important to have the AI mention context that is relevant to the user.
✅ Improve chat interface.
✅ Optimize program for production.

### Refactoring Large Files
- Refactored obsidian.py into a proper module structure with:
  - core.py - Main ObsidianMemory class
  - api.py - API interactions
  - filesystem.py - File system operations
  - utils.py - Utility functions

### Moving Tests
- Created a tests directory
- Moved all test files to the tests directory
- Added proper __init__.py file to the tests directory

### Adding RAG
- Created a rag module with:
  - document.py - Document and DocumentChunk classes
  - embeddings.py - EmbeddingProvider class for generating embeddings
  - retriever.py - DocumentRetriever class for finding relevant documents

### Building Flask Frontend
- Created a Flask web application (app.py)
- Implemented HTML, CSS, and JavaScript for the chat interface
- Added support for Shift+Enter to create new lines
- Implemented dark mode support
- Added chat history loading

### Improving System Prompt
- Removed hardcoded context about stress and Dallas
- Made the prompt more generic and focused on remembering past conversations
- Added instructions to query previous conversations for context

### Updating Obsidian Path
- Changed the memory directory from "AI-Know-It-All" to "ai-know-it-all"
- Updated all references in the codebase

### Enhanced UI Features
- Added markdown rendering for assistant messages
- Added code syntax highlighting with highlight.js
- Added copy to clipboard functionality for assistant messages
- Implemented dark/light mode toggle with system preference detection
- Added auto-resizing textarea for the input field
- Added export chat functionality to save conversations
- Added voice input for dictating messages using Web Speech API
- Added browser notifications for new messages when tab is not active

### New Document Awareness
- Added file watcher using watchdog to monitor the Obsidian vault
- Implemented handlers for file creation and modification events
- Added new files to concept cache for auto-linking
- Added graceful shutdown of file watchers

### Important Memory Recognition
- Added detection of important memories based on keywords and patterns
- Implemented personal information extraction using regex patterns
- Added similarity-based retrieval of important memories relevant to queries
- Enhanced prompt building to include important memories

### Chat Interface Improvements
- Enhanced UI with better styling and animations
- Improved dark mode support
- Added custom scrollbars
- Optimized message display and formatting
- Improved button styling and layout

### Production Optimization
- Added asynchronous initialization of chat interface
- Implemented health check endpoint
- Added proper cache control for static assets
- Created WSGI entry point for production servers
- Added Gunicorn configuration with environment variable support
- Created systemd service file for Linux deployments
- Added comprehensive deployment guide
- Implemented graceful handling of initialization delays