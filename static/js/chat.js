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

// Global variables
let currentModel = '';

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM content loaded - initializing chat.js');
    
    // Initialize chat elements
    initChat();
    
    // Load models immediately
    console.log('Loading models on page load');
    setTimeout(loadModels, 500); // Give a small delay to ensure DOM is ready
    
    // Focus input field when the page loads
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.focus();
    }
});

function initChat() {
    const chatMessages = document.getElementById('chatMessages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const typingIndicator = document.getElementById('typingIndicator');
    const modelSelect = document.getElementById('modelSelect');
    const modelInfo = document.getElementById('modelInfo');
    const refreshModels = document.getElementById('refreshModels');
    
    // Log elements for debugging
    console.log('DOM Elements:', {
        chatMessages,
        messageInput,
        sendButton,
        typingIndicator,
        modelSelect,
        modelInfo,
        refreshModels
    });
    
    // Speech recognition variables
    let recognition = null;
    let isListening = false;
    
    // Page visibility tracking
    let isPageVisible = true;
    let notificationsEnabled = false;
    
    // Load chat history
    loadChatHistory();
    
    // Send message when Send button is clicked
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Send message when Enter key is pressed (but not with Shift)
    if (messageInput) {
        messageInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
            // Allow new line when Shift+Enter is pressed
            // Default behavior adds a new line
            
            // Auto-resize textarea as user types
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
    
    // Handle model selection change
    if (modelSelect) {
        modelSelect.addEventListener('change', function() {
            const selectedModel = this.value;
            if (selectedModel && selectedModel !== currentModel) {
                changeModel(selectedModel);
            }
        });
    }
    
    // Handle refresh models button
    if (refreshModels) {
        refreshModels.addEventListener('click', function() {
            console.log('Refresh models clicked');
            loadModels();
        });
    }
    
    // Initialize action buttons
    initActionButtons();
    
    // Initialize theme
    initTheme();
    
    // Initialize speech recognition if supported
    initSpeechRecognition();
    
    // Initialize notifications
    initNotifications();
    
    // Track page visibility
    document.addEventListener('visibilitychange', function() {
        isPageVisible = document.visibilityState === 'visible';
    });
}

function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input and reset height
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
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
            
            // Send notification if page is not visible
            if (!isPageVisible && notificationsEnabled) {
                sendNotification('New message from AI Know It All', {
                    body: data.response.substring(0, 100) + (data.response.length > 100 ? '...' : ''),
                    icon: '/static/img/favicon.png'
                });
            }
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
    
    // Render markdown for assistant messages
    if (role === 'assistant') {
        contentDiv.innerHTML = marked.parse(content);
        
        // Apply syntax highlighting to code blocks
        contentDiv.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    } else {
        contentDiv.textContent = content;
    }
    
    const timestamp = document.createElement('div');
    timestamp.classList.add('timestamp');
    timestamp.textContent = new Date().toLocaleTimeString();
    
    // Add message actions
    const actionsDiv = document.createElement('div');
    actionsDiv.classList.add('message-actions');
    
    if (role === 'assistant') {
        // Copy button
        const copyBtn = document.createElement('button');
        copyBtn.classList.add('action-btn');
        copyBtn.innerHTML = '<i class="bi bi-clipboard"></i>';
        copyBtn.title = 'Copy to clipboard';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(content)
                .then(() => {
                    copyBtn.innerHTML = '<i class="bi bi-clipboard-check"></i>';
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="bi bi-clipboard"></i>';
                    }, 2000);
                });
        });
        actionsDiv.appendChild(copyBtn);
    }
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timestamp);
    messageDiv.appendChild(actionsDiv);
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

function loadModels() {
    // Get DOM elements directly (don't rely on previously cached references)
    const modelSelectEl = document.getElementById('modelSelect');
    const modelInfoEl = document.getElementById('modelInfo');
    const refreshModelsEl = document.getElementById('refreshModels');
    
    // Check if DOM elements exist
    if (!modelSelectEl || !modelInfoEl) {
        console.error('Model selector elements not found in loadModels:', {
            modelSelect: modelSelectEl,
            modelInfo: modelInfoEl,
            refreshModels: refreshModelsEl
        });
        return;
    }
    
    // Show loading state
    modelSelectEl.disabled = true;
    if (refreshModelsEl) refreshModelsEl.disabled = true;
    modelInfoEl.textContent = 'Loading models...';
    
    console.log('Fetching models from API...');
    
    // Fetch available models from server
    fetch('/api/models')
        .then(response => {
            console.log('API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Models data received:', data);
            
            // Clear existing options
            modelSelectEl.innerHTML = '';
            
            if (data.error) {
                console.error('API returned error:', data.error);
                modelInfoEl.textContent = `Error: ${data.error}`;
                modelSelectEl.innerHTML = '<option value="" disabled selected>Error loading models</option>';
                return;
            }
            
            // Save current model
            currentModel = data.current_model;
            console.log('Current model set to:', currentModel);
            
            // Add options for each model
            if (data.models && data.models.length > 0) {
                console.log(`Adding ${data.models.length} models to selector`);
                data.models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = model.name;
                    
                    // Get parameter size if available
                    const paramSize = model.details?.parameter_size || '';
                    if (paramSize) {
                        option.textContent += ` (${paramSize})`;
                    }
                    
                    // Mark current model as selected
                    if (model.name === currentModel) {
                        option.selected = true;
                    }
                    
                    modelSelectEl.appendChild(option);
                });
                
                // Update model info
                updateModelInfoDirect(currentModel, data.models);
            } else {
                console.warn('No models found in API response');
                modelSelectEl.innerHTML = '<option value="" disabled selected>No models available</option>';
                modelInfoEl.textContent = 'No models available';
            }
            
            // Enable controls
            modelSelectEl.disabled = false;
            if (refreshModelsEl) refreshModelsEl.disabled = false;
        })
        .catch(error => {
            console.error('Error fetching models:', error);
            modelInfoEl.textContent = `Error: ${error.message}`;
            modelSelectEl.innerHTML = '<option value="" disabled selected>Error loading models</option>';
            modelSelectEl.disabled = false;
            if (refreshModelsEl) refreshModelsEl.disabled = false;
        });
}

function updateModelInfoDirect(modelName, models) {
    // Get DOM element directly
    const modelInfoEl = document.getElementById('modelInfo');
    
    // Check if modelInfo exists
    if (!modelInfoEl) {
        console.error('modelInfo element not found in updateModelInfoDirect');
        return;
    }
    
    // Find the selected model in the models array
    const model = models.find(m => m.name === modelName);
    
    if (model) {
        // Format size in MB or GB
        let sizeText = '';
        if (model.size) {
            const sizeInMB = model.size / (1024 * 1024);
            if (sizeInMB > 1000) {
                sizeText = `${(sizeInMB / 1024).toFixed(2)} GB`;
            } else {
                sizeText = `${sizeInMB.toFixed(2)} MB`;
            }
        }
        
        // Get quantization level if available
        const quantLevel = model.details?.quantization_level || '';
        
        // Format info text
        let infoText = `Using ${modelName}`;
        if (model.details?.parameter_size) {
            infoText += ` (${model.details.parameter_size})`;
        }
        if (sizeText) {
            infoText += ` | Size: ${sizeText}`;
        }
        if (quantLevel) {
            infoText += ` | Quantization: ${quantLevel}`;
        }
        
        modelInfoEl.textContent = infoText;
    } else {
        modelInfoEl.textContent = `Using ${modelName}`;
    }
}

function changeModel(newModel) {
    // Get DOM elements directly
    const modelSelectEl = document.getElementById('modelSelect');
    const modelInfoEl = document.getElementById('modelInfo');
    const refreshModelsEl = document.getElementById('refreshModels');
    
    // Check if DOM elements exist
    if (!modelSelectEl || !modelInfoEl) {
        console.error('Model selector elements not found in changeModel:', {
            modelSelect: modelSelectEl,
            modelInfo: modelInfoEl
        });
        return;
    }
    
    // Show loading state
    modelSelectEl.disabled = true;
    if (refreshModelsEl) refreshModelsEl.disabled = true;
    modelInfoEl.textContent = `Changing to ${newModel}...`;
    
    console.log('Changing model to:', newModel);
    
    // Send request to change model
    fetch('/api/models/change', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model: newModel }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Change model response:', data);
        
        if (data.error) {
            console.error('Error changing model:', data.error);
            addMessage(`Error changing model: ${data.error}`, 'system');
            // Reset select to current model
            Array.from(modelSelectEl.options).forEach(option => {
                option.selected = option.value === currentModel;
            });
        } else {
            // Update current model
            currentModel = data.new_model;
            
            // Add system message about model change
            addMessage(`Model changed from ${data.old_model} to ${data.new_model}`, 'system');
            
            // Update model info
            fetch('/api/models')
                .then(response => response.json())
                .then(modelData => {
                    updateModelInfoDirect(currentModel, modelData.models);
                });
        }
        
        // Enable controls
        modelSelectEl.disabled = false;
        if (refreshModelsEl) refreshModelsEl.disabled = false;
    })
    .catch(error => {
        console.error('Error changing model:', error);
        addMessage(`Error changing model: ${error.message}`, 'system');
        
        // Reset select to current model
        Array.from(modelSelectEl.options).forEach(option => {
            option.selected = option.value === currentModel;
        });
        
        // Enable controls
        modelSelectEl.disabled = false;
        if (refreshModelsEl) refreshModelsEl.disabled = false;
    });
}

function updateModelInfo(modelName, models) {
    // Check if modelInfo exists
    if (!modelInfo) {
        console.error('modelInfo element not available for updateModelInfo');
        return;
    }
    
    // Find the selected model in the models array
    const model = models.find(m => m.name === modelName);
    
    if (model) {
        // Format size in MB or GB
        let sizeText = '';
        if (model.size) {
            const sizeInMB = model.size / (1024 * 1024);
            if (sizeInMB > 1000) {
                sizeText = `${(sizeInMB / 1024).toFixed(2)} GB`;
            } else {
                sizeText = `${sizeInMB.toFixed(2)} MB`;
            }
        }
        
        // Get quantization level if available
        const quantLevel = model.details?.quantization_level || '';
        
        // Format info text
        let infoText = `Using ${modelName}`;
        if (model.details?.parameter_size) {
            infoText += ` (${model.details.parameter_size})`;
        }
        if (sizeText) {
            infoText += ` | Size: ${sizeText}`;
        }
        if (quantLevel) {
            infoText += ` | Quantization: ${quantLevel}`;
        }
        
        modelInfo.textContent = infoText;
    } else {
        modelInfo.textContent = `Using ${modelName}`;
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function initActionButtons() {
    // Add input actions container
    const chatInput = document.querySelector('.chat-input');
    const inputActions = document.createElement('div');
    inputActions.classList.add('input-actions');
    chatInput.appendChild(inputActions);
    
    // Add voice input button if supported
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const voiceButton = document.createElement('button');
        voiceButton.id = 'voiceInput';
        voiceButton.classList.add('btn', 'btn-outline-secondary', 'me-2');
        voiceButton.innerHTML = '<i class="bi bi-mic"></i>';
        voiceButton.title = 'Voice input';
        voiceButton.addEventListener('click', toggleSpeechRecognition);
        inputActions.appendChild(voiceButton);
    }
    
    // Add notification button if supported
    if ('Notification' in window) {
        const notificationButton = document.createElement('button');
        notificationButton.id = 'notificationToggle';
        notificationButton.classList.add('btn', 'btn-outline-secondary', 'me-2');
        notificationButton.innerHTML = '<i class="bi bi-bell"></i>';
        notificationButton.title = 'Enable notifications';
        notificationButton.addEventListener('click', toggleNotifications);
        inputActions.appendChild(notificationButton);
    }
    
    // Add clear chat button
    const chatHeader = document.querySelector('.chat-header');
    const clearButton = document.createElement('button');
    clearButton.classList.add('btn', 'btn-sm', 'btn-outline-danger', 'float-end');
    clearButton.innerHTML = '<i class="bi bi-trash"></i> Clear Chat';
    clearButton.addEventListener('click', clearChat);
    chatHeader.appendChild(clearButton);
    
    // Add export chat button
    const exportButton = document.createElement('button');
    exportButton.classList.add('btn', 'btn-sm', 'btn-outline-secondary', 'float-end', 'me-2');
    exportButton.innerHTML = '<i class="bi bi-download"></i> Export';
    exportButton.addEventListener('click', exportChat);
    chatHeader.appendChild(exportButton);
    
    // Add theme toggle button
    const themeButton = document.createElement('button');
    themeButton.id = 'themeToggle';
    themeButton.classList.add('btn', 'btn-sm', 'btn-outline-primary', 'float-end', 'me-2');
    themeButton.innerHTML = '<i class="bi bi-moon"></i>';
    themeButton.title = 'Toggle dark mode';
    themeButton.addEventListener('click', toggleTheme);
    chatHeader.appendChild(themeButton);
}

function clearChat() {
    if (confirm('Are you sure you want to clear the chat? This will only clear your local view.')) {
        chatMessages.innerHTML = '';
        addMessage('Chat cleared. How can I help you today?', 'system');
    }
}

function exportChat() {
    // Get all messages
    const messages = [];
    document.querySelectorAll('.message').forEach(msg => {
        const role = msg.classList.contains('user-message') ? 'User' : 
                    msg.classList.contains('assistant-message') ? 'Assistant' : 'System';
        const content = msg.querySelector('.message-content').textContent;
        const time = msg.querySelector('.timestamp').textContent;
        messages.push(`${role} (${time}):\n${content}\n\n`);
    });
    
    // Create file content
    const content = messages.join('---\n\n');
    const filename = `ai-know-it-all-chat-${new Date().toISOString().slice(0, 10)}.md`;
    
    // Create download link
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

function initTheme() {
    // Check for saved theme preference or use system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-theme');
        updateThemeButton(true);
    } else {
        document.body.classList.remove('dark-theme');
        updateThemeButton(false);
    }
}

function toggleTheme() {
    const isDarkTheme = document.body.classList.toggle('dark-theme');
    localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
    updateThemeButton(isDarkTheme);
}

function updateThemeButton(isDark) {
    const themeButton = document.getElementById('themeToggle');
    if (themeButton) {
        themeButton.innerHTML = isDark ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon"></i>';
        themeButton.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
    }
}

function initSpeechRecognition() {
    // Check if speech recognition is supported
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.log('Speech recognition not supported');
        return;
    }
    
    // Create speech recognition instance
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    
    // Configure recognition
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    // Handle results
    recognition.onresult = function(event) {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');
            
        messageInput.value = transcript;
        messageInput.style.height = 'auto';
        messageInput.style.height = (messageInput.scrollHeight) + 'px';
    };
    
    // Handle end of speech
    recognition.onend = function() {
        isListening = false;
        updateVoiceButton();
    };
    
    // Handle errors
    recognition.onerror = function(event) {
        console.error('Speech recognition error', event.error);
        isListening = false;
        updateVoiceButton();
        
        if (event.error === 'not-allowed') {
            addMessage('Microphone access denied. Please check your browser permissions.', 'system');
        }
    };
}

function toggleSpeechRecognition() {
    if (!recognition) return;
    
    if (isListening) {
        recognition.stop();
        isListening = false;
    } else {
        recognition.start();
        isListening = true;
        messageInput.value = '';
        messageInput.placeholder = 'Listening...';
    }
    
    updateVoiceButton();
}

function updateVoiceButton() {
    const voiceButton = document.getElementById('voiceInput');
    if (voiceButton) {
        if (isListening) {
            voiceButton.classList.add('btn-danger');
            voiceButton.classList.remove('btn-outline-secondary');
            voiceButton.innerHTML = '<i class="bi bi-mic-fill"></i>';
            voiceButton.title = 'Stop listening';
        } else {
            voiceButton.classList.remove('btn-danger');
            voiceButton.classList.add('btn-outline-secondary');
            voiceButton.innerHTML = '<i class="bi bi-mic"></i>';
            voiceButton.title = 'Voice input';
            messageInput.placeholder = 'Type your message here...';
        }
    }
}

function initNotifications() {
    // Check if notifications are supported
    if (!('Notification' in window)) {
        console.log('Notifications not supported');
        return;
    }
    
    // Check if notifications are already enabled
    if (Notification.permission === 'granted') {
        notificationsEnabled = true;
        updateNotificationButton();
    }
}

function toggleNotifications() {
    if (!('Notification' in window)) return;
    
    if (Notification.permission === 'granted') {
        // Toggle notifications
        notificationsEnabled = !notificationsEnabled;
        updateNotificationButton();
    } else if (Notification.permission !== 'denied') {
        // Request permission
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                notificationsEnabled = true;
                updateNotificationButton();
                sendNotification('Notifications enabled', {
                    body: 'You will now receive notifications when new messages arrive while the tab is not active.',
                    icon: '/static/img/favicon.png'
                });
            }
        });
    } else {
        // Permission denied
        addMessage('Notification permission denied. Please enable notifications in your browser settings.', 'system');
    }
}

function updateNotificationButton() {
    const notificationButton = document.getElementById('notificationToggle');
    if (notificationButton) {
        if (notificationsEnabled) {
            notificationButton.classList.add('btn-primary');
            notificationButton.classList.remove('btn-outline-secondary');
            notificationButton.innerHTML = '<i class="bi bi-bell-fill"></i>';
            notificationButton.title = 'Disable notifications';
        } else {
            notificationButton.classList.remove('btn-primary');
            notificationButton.classList.add('btn-outline-secondary');
            notificationButton.innerHTML = '<i class="bi bi-bell"></i>';
            notificationButton.title = 'Enable notifications';
        }
    }
}

function sendNotification(title, options) {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    
    const notification = new Notification(title, options);
    
    // Focus window when notification is clicked
    notification.onclick = function() {
        window.focus();
        notification.close();
    };
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        notification.close();
    }, 5000);
}