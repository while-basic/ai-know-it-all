/**
 * ----------------------------------------------------------------------------
 *  File:        model-selector.js
 *  Project:     Celaya Solutions AI Know It All
 *  Created by:  Celaya Solutions, 2025
 *  Author:      Christopher Celaya <chris@celayasolutions.com>
 *  Description: Model selector component for AI Know It All
 *  Version:     1.0.0
 *  License:     MIT (SPDX-Identifier: MIT)
 *  Last Update: (May 2025)
 * ----------------------------------------------------------------------------
 */

// Initialize the model selector when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Model selector initializing...');
    initModelSelector();
});

// Global variable to store the current model
let currentModel = '';

/**
 * Initialize the model selector
 */
function initModelSelector() {
    // Get DOM elements
    const modelSelect = document.getElementById('modelSelect');
    const modelInfo = document.getElementById('modelInfo');
    const refreshModels = document.getElementById('refreshModels');
    
    console.log('Model selector elements:', {
        modelSelect,
        modelInfo,
        refreshModels
    });
    
    // Check if required elements exist
    if (!modelSelect || !modelInfo) {
        console.error('Required model selector elements not found');
        return;
    }
    
    // Load models initially
    loadModels();
    
    // Add event listeners
    modelSelect.addEventListener('change', function() {
        const selectedModel = this.value;
        if (selectedModel && selectedModel !== currentModel) {
            changeModel(selectedModel);
        }
    });
    
    if (refreshModels) {
        refreshModels.addEventListener('click', function() {
            console.log('Refresh models button clicked');
            loadModels();
        });
    }
}

/**
 * Load available models from the API
 */
function loadModels() {
    // Get DOM elements
    const modelSelect = document.getElementById('modelSelect');
    const modelInfo = document.getElementById('modelInfo');
    const refreshModels = document.getElementById('refreshModels');
    
    // Check if required elements exist
    if (!modelSelect || !modelInfo) {
        console.error('Required model selector elements not found');
        return;
    }
    
    // Show loading state
    modelSelect.disabled = true;
    if (refreshModels) refreshModels.disabled = true;
    modelInfo.textContent = 'Loading models...';
    
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
            modelSelect.innerHTML = '';
            
            if (data.error) {
                console.error('API returned error:', data.error);
                modelInfo.textContent = `Error: ${data.error}`;
                modelSelect.innerHTML = '<option value="" disabled selected>Error loading models</option>';
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
                    
                    modelSelect.appendChild(option);
                });
                
                // Update model info
                updateModelInfo(currentModel, data.models);
            } else {
                console.warn('No models found in API response');
                modelSelect.innerHTML = '<option value="" disabled selected>No models available</option>';
                modelInfo.textContent = 'No models available';
            }
            
            // Enable controls
            modelSelect.disabled = false;
            if (refreshModels) refreshModels.disabled = false;
        })
        .catch(error => {
            console.error('Error fetching models:', error);
            modelInfo.textContent = `Error: ${error.message}`;
            modelSelect.innerHTML = '<option value="" disabled selected>Error loading models</option>';
            modelSelect.disabled = false;
            if (refreshModels) refreshModels.disabled = false;
        });
}

/**
 * Update the model info display
 */
function updateModelInfo(modelName, models) {
    // Get DOM element
    const modelInfo = document.getElementById('modelInfo');
    
    // Check if modelInfo exists
    if (!modelInfo) {
        console.error('modelInfo element not found');
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

/**
 * Change the current model
 */
function changeModel(newModel) {
    // Get DOM elements
    const modelSelect = document.getElementById('modelSelect');
    const modelInfo = document.getElementById('modelInfo');
    const refreshModels = document.getElementById('refreshModels');
    
    // Check if required elements exist
    if (!modelSelect || !modelInfo) {
        console.error('Required model selector elements not found');
        return;
    }
    
    // Show loading state
    modelSelect.disabled = true;
    if (refreshModels) refreshModels.disabled = true;
    modelInfo.textContent = `Changing to ${newModel}...`;
    
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
            modelInfo.textContent = `Error: ${data.error}`;
            
            // Reset select to current model
            Array.from(modelSelect.options).forEach(option => {
                option.selected = option.value === currentModel;
            });
        } else {
            // Update current model
            currentModel = data.new_model;
            
            // Add system message about model change (if addMessage function exists)
            if (typeof addMessage === 'function') {
                addMessage(`Model changed from ${data.old_model} to ${data.new_model}`, 'system');
            }
            
            // Update model info
            fetch('/api/models')
                .then(response => response.json())
                .then(modelData => {
                    updateModelInfo(currentModel, modelData.models);
                });
        }
        
        // Enable controls
        modelSelect.disabled = false;
        if (refreshModels) refreshModels.disabled = false;
    })
    .catch(error => {
        console.error('Error changing model:', error);
        modelInfo.textContent = `Error: ${error.message}`;
        
        // Reset select to current model
        Array.from(modelSelect.options).forEach(option => {
            option.selected = option.value === currentModel;
        });
        
        // Enable controls
        modelSelect.disabled = false;
        if (refreshModels) refreshModels.disabled = false;
    });
} 