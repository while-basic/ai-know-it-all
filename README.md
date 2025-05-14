# AI Know It All

A CLI chatbot with long-term memory powered by Ollama, FAISS vector database, and Obsidian integration.

## Features

- **Long-term Memory**: Conversations are stored in a FAISS vector database and persist between sessions
- **Contextual Responses**: The chatbot retrieves relevant past conversations to provide context-aware responses
- **Simple CLI Interface**: Easy-to-use command-line interface with rich text formatting
- **Powered by Ollama**: Uses the lightweight Ollama API for running LLMs locally
- **Obsidian Integration**: Store, view, and alter memories using Obsidian
- **Customizable**: Configure model, memory storage location, and more

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- llama3.2:1b model pulled in Ollama
- [Obsidian](https://obsidian.md/) (optional, for advanced memory management)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-know-it-all.git
   cd ai-know-it-all
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file (optional):
   ```
   OLLAMA_BASE_URL=http://localhost:11434
   MODEL_NAME=llama3.2:1b
   MEMORY_PATH=./data/memory
   OBSIDIAN_PATH=(path to your Obsidian vault)
   OBSIDIAN_API_URL=127.0.0.1
   OBSIDIAN_API_TOKEN=(your Obsidian API token)
   ```

## Usage

1. Make sure Ollama is running and you have the llama3.2:1b model:
   ```bash
   ollama pull llama3.2:1b
   ```

2. Start the chatbot:
   ```bash
   python -m src.main
   ```

3. Chat with the bot. Your conversations will be stored in both the vector database and Obsidian (if enabled).

4. Use special Obsidian commands:
   - `!obsidian list` - List recent notes
   - `!obsidian search <query>` - Search notes
   - `!obsidian import <path>` - Import a note
   - `!obsidian save` - Save current conversation to Obsidian

5. Exit the chat by typing `exit`, `quit`, or pressing `Ctrl+C`.

## Command Line Options

- `--model`: Specify the model name (default: llama3.2:1b or from .env)
- `--base-url`: Specify the Ollama API base URL (default: http://localhost:11434 or from .env)
- `--memory-path`: Specify the memory storage path (default: ./data/memory or from .env)
- `--debug`: Enable debug logging
- `--obsidian-path`: Path to Obsidian vault
- `--obsidian-api-url`: Obsidian API URL
- `--obsidian-api-port`: Obsidian API port
- `--obsidian-api-token`: Obsidian API token
- `--disable-obsidian`: Disable Obsidian integration

## Project Structure

```
ai-know-it-all/
├── src/
│   ├── __init__.py
│   ├── chat.py           # Chat interface handling
│   ├── memory.py         # FAISS vector store implementation
│   ├── llm.py            # LLM integration with Ollama
│   ├── obsidian.py       # Obsidian integration for memory management
│   └── main.py           # CLI entry point
├── data/
│   └── memory/           # Persistent storage for vector embeddings
├── requirements.txt
├── README.md
└── docs/
    └── build-instructions.md
```

## Obsidian Integration

The chatbot can store and retrieve memories in Obsidian, a powerful knowledge management tool. This enables:

1. **Persistent Memory**: Conversations are stored as Markdown notes in your Obsidian vault
2. **Visual Exploration**: Browse and search your conversation history in Obsidian
3. **Manual Editing**: Edit memories directly in Obsidian for better context
4. **Knowledge Integration**: Connect conversation memories with your existing notes

To use this feature, ensure you have Obsidian installed and specify your vault path in the `.env` file or via command-line options.

## License

MIT

## Author

Christopher Celaya <chris@celayasolutions.com> 