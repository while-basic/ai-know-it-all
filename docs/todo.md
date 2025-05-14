# TODO

- Remove unessecary files from codebase.
- Place files in their proper directory.
- Add values to memories that are important to have the AI mention context that is relevant to the user.
## Completed Tasks

✅ Build Flask frontend chat interface.
✅ Improve system prompt.
✅ Refactor large files, more than 300 lines of code.
✅ Move all tests to a tests folder.
✅ Remove context about stress and Dallas as it is not relevant to me. These are hardcoded and should not be. Instead, the AI should query what we discussed the day/week before and generate a response based off that context.
✅ Add RAG
✅ Add support for adding new lines. When the user uses (shift+enter), a new line should be created rather than submitting the users quer✅ ✅ Update memory path (Obsidian Vault) to "Users/chriscelaya/ObsidianVaults/ai-know-it-all"

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