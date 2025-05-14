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
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from dotenv import load_dotenv

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

# Initialize chat interface
memory_path = os.getenv("MEMORY_PATH", "./data/memory")
model = os.getenv("MODEL_NAME", "sushruth/solar-uncensored:latest")
use_obsidian = os.getenv("USE_OBSIDIAN", "true").lower() == "true"

chat_interface = EnhancedChatInterface(
    memory_path=memory_path,
    model=model,
    use_obsidian=use_obsidian
)

@app.route('/')
def index():
    """Render the chat interface."""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'),
                               'favicon.png', mimetype='image/png')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process a chat message and return the response."""
    try:
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

if __name__ == '__main__':
    # Start the Flask app
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"Starting AI Know It All web interface on port {port}")
    print(f"Using model: {model}")
    print(f"Memory path: {memory_path}")
    print(f"Obsidian integration: {'Enabled' if use_obsidian else 'Disabled'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 