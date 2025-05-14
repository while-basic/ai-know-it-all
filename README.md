# AI Know It All

AI Know It All is a chatbot with long-term memory and Obsidian integration. It remembers past conversations and can search through your Obsidian vault for relevant information.

## Features

- Long-term memory using vector embeddings
- Integration with Obsidian for knowledge management
- Web interface for chat interactions
- Support for adding new lines with Shift+Enter
- Dark mode support
- Responsive design
- Automatic conversation naming
- Enhanced Obsidian integration with daily notes and auto-linking
- Proactive features like suggestions and reflective prompts
- Important memory recognition and retrieval

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-know-it-all.git
   cd ai-know-it-all
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```
   FLASK_SECRET_KEY=your-secure-secret-key
   MEMORY_PATH=./data/memory
   MODEL_NAME=sushruth/solar-uncensored:latest
   USE_OBSIDIAN=true
   OBSIDIAN_PATH=/Users/chriscelaya/ObsidianVaults
   OBSIDIAN_API_URL=127.0.0.1
   OBSIDIAN_API_PORT=27124
   OBSIDIAN_API_TOKEN=35d80b834a12ecea5e21f4838722b8af8575ce7186d56176a9ba7835a0334951
   PORT=8080
   FLASK_DEBUG=false
   ```

## Usage

### Command Line Interface

Run the CLI version:

```bash
python run_enhanced.py
```

Options:
- `--model`: Model name to use
- `--memory-path`: Path to memory directory
- `--obsidian-path`: Path to Obsidian vault
- `--disable-obsidian`: Disable Obsidian integration

### Web Interface

Run the web interface:

```bash
python app.py
```

Then open your browser at http://localhost:8080

### Production Deployment

For production deployments, we recommend using Gunicorn:

```bash
gunicorn -c gunicorn_config.py wsgi:application
```

See the [Deployment Guide](DEPLOYMENT.md) for detailed instructions on setting up a production environment.

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
  - `proactive.py`: Proactive assistant features
- `static/`: Static files for web interface
  - `css/`: CSS files
  - `js/`: JavaScript files
- `templates/`: HTML templates
- `data/`: Data directory
  - `memory/`: Memory storage
- `tests/`: Test files

## Key Features

### Long-term Memory

The chatbot uses a FAISS vector database to store and retrieve memories. This allows it to remember past conversations and recall relevant information when needed. The memory system includes:

- Vector embeddings for semantic search
- Metadata storage for additional information
- Important memory recognition based on keywords and patterns
- Personal information extraction using regex patterns

### Obsidian Integration

The chatbot integrates with Obsidian for knowledge management:

- Daily notes: On each chatbot session, a new daily note is generated (`chat-YYYY-MM-DD.md`)
- Auto-linking concepts: Mentions of concepts that exist in the Obsidian vault are automatically linked with `[[Concept]]` syntax
- Collapsible sections: Retrieved memories are added as collapsible sections in the notes
- Tags: Notes are tagged with `#retrieved`, `#generated`, `#prompt`, and `#reflection` as appropriate
- File watcher: The chatbot monitors the Obsidian vault for new files and adds them to its concept cache

### Proactive Features

The chatbot includes proactive features to enhance the user experience:

- Welcome message: On startup, the chatbot displays a welcome message with contextual information
- Proactive suggestions: The chatbot occasionally offers suggestions based on topics mentioned frequently in recent conversations
- Reflective prompts: The chatbot occasionally offers reflective questions based on conversation patterns
- Insights generation: The chatbot generates insights based on conversations and saves them for future reference

### Automatic Conversation Naming

The chatbot automatically names conversations based on context:

- Initially, conversations start with generic timestamp-based names
- Once enough context is available (at least 2 user messages), the chatbot uses the LLM to generate a descriptive name
- The conversation note is then renamed in Obsidian with the generated name

### Web Interface

The web interface provides a user-friendly way to interact with the chatbot:

- Responsive design that works on desktop and mobile
- Dark mode support with system preference detection
- Markdown rendering for assistant messages
- Code syntax highlighting
- Copy to clipboard functionality for assistant messages
- Auto-resizing textarea for the input field
- Export chat functionality to save conversations
- Voice input for dictating messages
- Browser notifications for new messages when tab is not active

## Environment Variables

The application can be configured using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| FLASK_SECRET_KEY | Secret key for Flask sessions | ai-know-it-all-secret-key |
| MEMORY_PATH | Path to store memory files | ./data/memory |
| MODEL_NAME | Name of the LLM model to use | sushruth/solar-uncensored:latest |
| USE_OBSIDIAN | Whether to use Obsidian integration | true |
| OBSIDIAN_PATH | Path to the Obsidian vault | /Users/chriscelaya/ObsidianVaults |
| OBSIDIAN_API_URL | URL for the Obsidian API | 127.0.0.1 |
| OBSIDIAN_API_PORT | Port for the Obsidian API | 27124 |
| OBSIDIAN_API_TOKEN | Token for the Obsidian API | (none) |
| PORT | Port for the Flask app to listen on | 8080 |
| FLASK_DEBUG | Whether to run Flask in debug mode | false |

## License

MIT

## Author

Christopher Celaya <chris@celayasolutions.com> 