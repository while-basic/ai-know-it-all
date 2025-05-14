// ----------------------------------------------------------------------------
//  File:        chat.js
//  Project:     Celaya Solutions AI Know It All
//  Created by:  Celaya Solutions, 2025
//  Author:      Christopher Celaya <chris@celayasolutions.com>
//  Description: JavaScript for AI Know It All web interface
//  Version:     1.0.0
//  License:     MIT (SPDX-Identifier: MIT)
//  Last Update: (May 2025)
// ----------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const typingIndicator = document.getElementById('typingIndicator');
    
    // Load chat history
    loadChatHistory();
    
    // Send message when Send button is clicked
    sendButton.addEventListener('click', sendMessage);
    
    // Send message when Enter key is pressed (but not with Shift)
    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
        // Allow new line when Shift+Enter is pressed
        // Default behavior adds a new line
    });
    
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        messageInput.value = '';
        
        // Show typing indicator
        typingIndicator.style.display = 'flex';
        
        // Scroll to bottom
        scrollToBottom();
        
        // Send message to server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            typingIndicator.style.display = 'none';
            
            // Add assistant message to chat
            if (data.error) {
                addMessage(`Error: ${data.error}`, 'system');
            } else {
                addMessage(data.response, 'assistant');
            }
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            // Hide typing indicator
            typingIndicator.style.display = 'none';
            
            // Add error message to chat
            addMessage(`Error: ${error.message}`, 'system');
            
            // Scroll to bottom
            scrollToBottom();
        });
    }
    
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        
        if (role === 'user') {
            messageDiv.classList.add('user-message');
        } else if (role === 'assistant') {
            messageDiv.classList.add('assistant-message');
        } else {
            messageDiv.classList.add('system-message');
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        contentDiv.textContent = content;
        
        const timestamp = document.createElement('div');
        timestamp.classList.add('timestamp');
        timestamp.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timestamp);
        chatMessages.appendChild(messageDiv);
    }
    
    function loadChatHistory() {
        // Show typing indicator
        typingIndicator.style.display = 'flex';
        
        // Get chat history from server
        fetch('/api/history')
            .then(response => response.json())
            .then(data => {
                // Hide typing indicator
                typingIndicator.style.display = 'none';
                
                // Clear chat messages
                chatMessages.innerHTML = '';
                
                // Add welcome message
                addMessage('Welcome to AI Know It All! How can I help you today?', 'system');
                
                // Add messages from history
                if (data.history && data.history.length > 0) {
                    data.history.forEach(msg => {
                        addMessage(msg.content, msg.role);
                    });
                }
                
                // Scroll to bottom
                scrollToBottom();
            })
            .catch(error => {
                // Hide typing indicator
                typingIndicator.style.display = 'none';
                
                // Add error message
                addMessage(`Error loading chat history: ${error.message}`, 'system');
            });
    }
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Focus input field
    messageInput.focus();
}); 