# ----------------------------------------------------------------------------
#  File:        app.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Flask web interface for AI Know It All chatbot
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import logging
import json
import atexit
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
import threading
import time
import requests

# Add the current directory to the path so we can import the modules
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.chat_enhanced import EnhancedChatInterface
from src.llm import LLMClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ai-know-it-all-web.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ai-know-it-all-secret-key")

# Add ProxyFix middleware for handling reverse proxies (like Nginx)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Initialize chat interface
memory_path = os.getenv("MEMORY_PATH", "./data/memory")
model = os.getenv("MODEL_NAME", "sushruth/solar-uncensored:latest")
use_obsidian = os.getenv("USE_OBSIDIAN", "true").lower() == "true"
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Initialize chat interface with a timeout to prevent blocking startup
chat_interface = None
chat_interface_ready = False

def init_chat_interface():
    global chat_interface, chat_interface_ready
    try:
        chat_interface = EnhancedChatInterface(
            memory_path=memory_path,
            model=model,
            use_obsidian=use_obsidian
        )
        chat_interface_ready = True
        logger.info("Chat interface initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing chat interface: {e}", exc_info=True)
        chat_interface_ready = False

# Start initialization in a background thread
init_thread = threading.Thread(target=init_chat_interface)
init_thread.daemon = True
init_thread.start()

# Register shutdown function to stop file watcher
@atexit.register
def shutdown():
    """Clean up resources when the application exits."""
    logger.info("Application shutting down, cleaning up resources...")
    if chat_interface and chat_interface.use_obsidian and hasattr(chat_interface.memory, 'obsidian'):
        logger.info("Stopping Obsidian file watcher...")
        chat_interface.memory.obsidian.stop_file_watcher()

@app.route('/')
def index():
    """Render the chat interface."""
    return render_template('index.html')

@app.route('/debug')
def debug():
    """Render the debug page."""
    return render_template('debug.html')

@app.route('/test')
def test():
    """Render the test page."""
    return render_template('test.html')

@app.route('/api-test')
def api_test():
    """Render the API test page."""
    return render_template('api_test.html')

@app.route('/model-test')
def model_test():
    """Render the model test page."""
    return render_template('model_test.html')

@app.route('/health')
def health():
    """Health check endpoint."""
    status = "ok" if chat_interface_ready else "initializing"
    return jsonify({
        "status": status,
        "version": "1.0.0",
        "model": model,
        "obsidian_enabled": use_obsidian
    })

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'),
                               'favicon.png', mimetype='image/png')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process a chat message and return the response."""
    try:
        # Check if chat interface is ready
        if not chat_interface_ready:
            return jsonify({
                'error': 'Chat interface is still initializing. Please try again in a moment.'
            }), 503
            
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Process the message
        response = chat_interface.process_query(message)
        
        # Return the response
        return jsonify({
            'response': response
        })
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred processing your message'}), 500

@app.route('/api/history', methods=['GET'])
def history():
    """Get chat history."""
    try:
        # Check if chat interface is ready
        if not chat_interface_ready:
            return jsonify({
                'error': 'Chat interface is still initializing. Please try again in a moment.'
            }), 503
            
        # Get recent messages from memory
        recent_memories = chat_interface.memory.get_recent_memories(limit=50)
        
        # Format messages for display
        messages = []
        for memory in recent_memories:
            messages.append({
                'role': memory.get('role'),
                'content': memory.get('text'),
                'timestamp': memory.get('timestamp')
            })
            
        # Sort by timestamp
        messages.sort(key=lambda x: x.get('timestamp', 0))
        
        return jsonify({'history': messages})
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred retrieving chat history'}), 500

@app.route('/api/models', methods=['GET'])
def list_models():
    """List available Ollama models."""
    try:
        # Create a temporary LLM client to get models
        llm_client = LLMClient(base_url=ollama_base_url)
        
        # Get available models from Ollama API
        api_url = f"{ollama_base_url}/api/tags"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        models = result.get("models", [])
        
        # Format model information
        formatted_models = []
        for model_info in models:
            formatted_models.append({
                'name': model_info.get('name'),
                'size': model_info.get('size'),
                'modified_at': model_info.get('modified_at'),
                'details': model_info.get('details', {}),
                'is_current': model_info.get('name') == chat_interface.llm.model if chat_interface else False
            })
            
        # Sort models by name
        formatted_models.sort(key=lambda x: x.get('name', ''))
        
        return jsonify({
            'models': formatted_models,
            'current_model': chat_interface.llm.model if chat_interface else model
        })
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred retrieving models'}), 500

@app.route('/api/models/change', methods=['POST'])
def change_model():
    """Change the current Ollama model."""
    try:
        # Check if chat interface is ready
        if not chat_interface_ready:
            return jsonify({
                'error': 'Chat interface is still initializing. Please try again in a moment.'
            }), 503
            
        data = request.json
        new_model = data.get('model')
        
        if not new_model:
            return jsonify({'error': 'No model specified'}), 400
            
        # Validate that the model exists
        api_url = f"{ollama_base_url}/api/tags"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        available_models = [model.get('name') for model in result.get('models', [])]
        
        if new_model not in available_models:
            return jsonify({'error': f'Model {new_model} not found'}), 404
            
        # Update the model in the chat interface
        old_model = chat_interface.llm.model
        chat_interface.llm.model = new_model
        
        logger.info(f"Changed model from {old_model} to {new_model}")
        
        # Add a system message to the chat
        chat_interface.memory.add_memory(
            f"Model changed from {old_model} to {new_model}",
            role="system"
        )
        
        return jsonify({
            'success': True,
            'old_model': old_model,
            'new_model': new_model
        })
    except Exception as e:
        logger.error(f"Error changing model: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred changing the model'}), 500

# Add cache control headers to static files
@app.after_request
def add_cache_headers(response):
    """Add cache control headers to responses."""
    if request.path.startswith('/static/'):
        # Cache static assets for 1 week
        response.headers['Cache-Control'] = 'public, max-age=604800'
    return response

if __name__ == '__main__':
    # Start the Flask app
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"Starting AI Know It All web interface on port {port}")
    print(f"Using model: {model}")
    print(f"Memory path: {memory_path}")
    print(f"Obsidian integration: {'Enabled' if use_obsidian else 'Disabled'}")
    
    # Wait for chat interface to initialize before starting the server
    timeout = 60  # seconds
    start_time = time.time()
    while not chat_interface_ready and time.time() - start_time < timeout:
        time.sleep(1)
        
    if not chat_interface_ready:
        logger.warning(f"Chat interface not ready after {timeout} seconds, starting anyway")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 