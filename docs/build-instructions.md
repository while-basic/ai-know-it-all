### Prompt

Develop a CLI chatbot tool with long-term memory. I want it to remember all conversations and remember them even after stopping the program.

### Tech Stack
- Ollama: For inference
- sushruth/solar-uncensored:latest: Large language model to use
- FAISS: For long term memory and searching
- Python: Language to use
- Obsidian: For storing, viewing, and altering memories.

### Details
- Obsidian path: /Users/chriscelaya/ObsidianVaults
- Request returns all notes in root directory: GET /vault/ HTTP/1.1
- Authorization: Bearer 35d80b834a12ecea5e21f4838722b8af8575ce7186d56176a9ba7835a0334951
- URL: 127.0.0.1

### Code Requirements
- Do not create more than 300 lines in a single file
- Use approperiate file directories


### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running locally
- sushruth/solar-uncensored:latest model pulled in Ollama

### Installation

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

### Project Structure

```
ai-know-it-all/
├── src/
│   ├── __init__.py
│   ├── chat.py           # Chat interface handling
│   ├── memory.py         # FAISS vector store implementation
│   ├── llm.py            # LLM integration with Ollama
│   └── main.py           # CLI entry point
├── data/
│   └── memory/           # Persistent storage for vector embeddings
├── requirements.txt
├── README.md
└── docs/
    └── build-instructions.md
```

### Configuration

Create a `.env` file in the root directory with the following variables:
```
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=sushruth/solar-uncensored:latest
MEMORY_PATH=./data/memory
```

### Usage

1. Start the chatbot:
   ```bash
   python -m src.main
   ```

2. Chat with the bot. Your conversations will be stored in the vector database.

3. Exit the chat by typing `exit`, `quit`, or pressing `Ctrl+C`.

### Key Features

- **Long-term memory**: Conversations are stored in a FAISS vector database
- **Contextual responses**: The bot can recall previous conversations
- **Persistent storage**: Memory is preserved between sessions
- **Simple CLI interface**: Easy to use command-line interface

### Development

To extend or modify the chatbot:

1. The `memory.py` module handles vector storage and retrieval
2. The `llm.py` module manages communication with Ollama
3. The `chat.py` module handles the chat interface and user interaction
4. The `main.py` file ties everything together

### Testing

Run the tests to ensure everything is working correctly:
```bash
pytest tests/
```