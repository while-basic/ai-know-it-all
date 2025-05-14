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

# Add the current directory to the path so we can import the modules
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.chat_enhanced import EnhancedChatInterface

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