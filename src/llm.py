# ----------------------------------------------------------------------------
#  File:        llm.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: LLM integration with Ollama for the chatbot
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import json
import requests
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for interacting with Ollama LLM API.
    """
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            base_url: Base URL for Ollama API, defaults to env var or localhost
            model: Model name to use, defaults to env var or sushruth/solar-uncensored:latest
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("MODEL_NAME", "sushruth/solar-uncensored:latest")
        
        # Ensure base_url doesn't end with a slash
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
            
        logger.info(f"Initialized LLM client with model: {self.model}")
        
    def generate_response(self, 
                         prompt: str, 
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: int = 500) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        api_url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            logger.debug(f"Sending request to Ollama API: {json.dumps(payload)}")
            response = requests.post(api_url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            if "response" not in result:
                logger.error(f"Unexpected response format from Ollama API: {result}")
                return "Error: Unexpected response format from the model."
                
            return result.get("response", "")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            return f"Error: Could not generate response. Please ensure Ollama is running with the {self.model} model."
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {e}")
            return "Error: Invalid response from the model."
        except Exception as e:
            logger.error(f"Unexpected error in generate_response: {e}")
            return "Error: An unexpected error occurred while generating a response."
            
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       system_prompt: Optional[str] = None,
                       temperature: float = 0.3) -> str:
        """
        Generate a chat completion response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Generated assistant response
        """
        api_url = f"{self.base_url}/api/chat"
        
        # Clean and validate messages
        clean_messages = []
        for msg in messages:
            if not isinstance(msg, dict):
                continue
                
            if "role" not in msg or "content" not in msg:
                continue
                
            if not isinstance(msg["content"], str):
                msg["content"] = str(msg["content"])
                
            clean_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        payload = {
            "model": self.model,
            "messages": clean_messages,
            "temperature": temperature,
            "stream": False
        }
        
        if system_prompt:
            # Add system prompt as a system message at the beginning if not already present
            if not any(msg.get("role") == "system" for msg in clean_messages):
                payload["messages"].insert(0, {"role": "system", "content": system_prompt})
            
        try:
            logger.debug(f"Sending chat request to Ollama API: {json.dumps(payload)}")
            response = requests.post(api_url, json=payload, timeout=60)
            
            # Check for HTTP errors
            if response.status_code != 200:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return self._fallback_to_generate(clean_messages, system_prompt, temperature)
            
            # Parse the JSON response
            try:
                result = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return self._fallback_to_generate(clean_messages, system_prompt, temperature)
            
            # Extract the response content based on the response format
            if "message" in result and isinstance(result["message"], dict) and "content" in result["message"]:
                return result["message"]["content"]
            elif "response" in result and isinstance(result["response"], str):
                return result["response"]
            else:
                logger.error(f"Unexpected response format: {result}")
                return self._fallback_to_generate(clean_messages, system_prompt, temperature)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            # Fall back to generate API
            return self._fallback_to_generate(clean_messages, system_prompt, temperature)
        except Exception as e:
            logger.error(f"Unexpected error in chat_completion: {e}")
            return self._fallback_to_generate(clean_messages, system_prompt, temperature)
            
    def _fallback_to_generate(self, messages: List[Dict[str, str]], system_prompt: Optional[str], temperature: float) -> str:
        """
        Fall back to generate API if chat API fails.
        
        Args:
            messages: List of message dicts
            system_prompt: Optional system prompt
            temperature: Temperature for generation
            
        Returns:
            Generated response
        """
        logger.warning("Falling back to generate API")
        
        # Format messages into a prompt
        prompt_parts = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                continue
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
                
        # Construct the final prompt
        prompt = "\n".join(prompt_parts)
        
        # Add the final instruction for the assistant to respond
        prompt += "\nAssistant:"
        
        # Use the generate API
        return self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=1000
        )
            
    def check_model_availability(self) -> bool:
        """
        Check if the model is available in Ollama.
        
        Returns:
            True if model is available, False otherwise
        """
        api_url = f"{self.base_url}/api/tags"
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            models = [model.get("name") for model in result.get("models", [])]
            
            return self.model in models
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking model availability: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response when checking model availability: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in check_model_availability: {e}")
            return False 