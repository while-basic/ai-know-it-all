# AI Know It All

AI Know It All is a chatbot with long-term memory and Obsidian integration. It remembers past conversations and can search through your Obsidian vault for relevant information.

## Features

- Long-term memory using vector embeddings
- Integration with Obsidian for knowledge management
- Web interface for chat interactions
- Support for adding new lines with Shift+Enter
- Dark mode support
- Responsive design

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-know-it-all.git
   cd ai-know-it-all
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```
   MODEL_NAME=sushruth/solar-uncensored:latest
   MEMORY_PATH=./data/memory
   OBSIDIAN_PATH=/path/to/your/obsidian/vault
   FLASK_SECRET_KEY=your-secret-key
   FLASK_DEBUG=false
   PORT=5000
   ```

## Usage

### Command Line Interface

Run the CLI version:

```
python run_enhanced.py
```

Options:
- `--model`: Model name to use
- `--memory-path`: Path to memory directory
- `--obsidian-path`: Path to Obsidian vault
- `--disable-obsidian`: Disable Obsidian integration

### Web Interface

Run the web interface:

```
python app.py
```

Then open your browser at http://localhost:5000

## Project Structure

- `src/`: Source code
  - `chat_enhanced.py`: Enhanced chat interface
  - `memory_enhanced.py`: Vector memory storage
  - `llm.py`: LLM client
  - `obsidian/`: Obsidian integration
    - `core.py`: Main ObsidianMemory class
    - `api.py`: API interactions
    - `filesystem.py`: File system operations
    - `utils.py`: Utility functions
  - `rag/`: Retrieval-Augmented Generation
    - `document.py`: Document and DocumentChunk classes
    - `embeddings.py`: EmbeddingProvider class
    - `retriever.py`: DocumentRetriever class
- `static/`: Static files for web interface
  - `css/`: CSS files
  - `js/`: JavaScript files
- `templates/`: HTML templates
- `data/`: Data directory
  - `memory/`: Memory storage
- `tests/`: Test files

## License

MIT

## Author

Christopher Celaya <chris@celayasolutions.com> 