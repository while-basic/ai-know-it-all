# ----------------------------------------------------------------------------
#  File:        test_proactive.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Test script for proactive assistant features
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import os
import sys
import logging
from dotenv import load_dotenv
from pathlib import Path

# Add the current directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.proactive import ProactiveAssistant
from src.llm import LLMClient
from src.obsidian import ObsidianMemory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_welcome_message():
    """Test the welcome message generation."""
    print("\n" + "=" * 50)
    print("Testing Welcome Message Generation")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get Obsidian path from environment or use default
    obsidian_path = os.getenv("OBSIDIAN_PATH", "/Users/chriscelaya/ObsidianVaults")
    
    # Create Obsidian memory handler
    obsidian = ObsidianMemory(obsidian_path=obsidian_path)
    
    # Create LLM client
    llm_client = LLMClient(model="sushruth/solar-uncensored:latest")
    
    # Create proactive assistant
    proactive = ProactiveAssistant(
        obsidian=obsidian,
        llm_client=llm_client
    )
    
    # Generate welcome message
    welcome_message = proactive.generate_welcome_message()
    
    print("\nWelcome Message:")
    print(welcome_message)
    
    return proactive

def test_proactive_suggestion(proactive: ProactiveAssistant):
    """Test proactive suggestion generation."""
    print("\n" + "=" * 50)
    print("Testing Proactive Suggestion Generation")
    print("=" * 50)
    
    # Generate proactive suggestion
    suggestion = proactive.generate_proactive_suggestion()
    
    print("\nProactive Suggestion:")
    print(suggestion if suggestion else "No suggestion generated")
    
def test_reflective_prompt(proactive: ProactiveAssistant):
    """Test reflective prompt generation."""
    print("\n" + "=" * 50)
    print("Testing Reflective Prompt Generation")
    print("=" * 50)
    
    # Generate reflective prompt
    reflective_prompt = proactive.generate_reflective_prompt()
    
    print("\nReflective Prompt:")
    print(reflective_prompt if reflective_prompt else "No reflective prompt generated")
    
def test_insight_generation(proactive: ProactiveAssistant):
    """Test insight generation."""
    print("\n" + "=" * 50)
    print("Testing Insight Generation")
    print("=" * 50)
    
    # Create a test conversation
    test_conversation = [
        {
            "role": "system",
            "content": "New conversation started"
        },
        {
            "role": "user",
            "content": "I'm planning a trip to Alaska next month."
        },
        {
            "role": "assistant",
            "content": "That sounds exciting! Alaska is beautiful. Do you have specific places in mind to visit?"
        },
        {
            "role": "user",
            "content": "I'm thinking about Anchorage and Denali National Park. I'm also concerned about my budget."
        },
        {
            "role": "assistant",
            "content": "Anchorage and Denali are great choices! For budget considerations, you might want to look into package deals and consider the shoulder season for better rates."
        }
    ]
    
    # Generate insight
    insight = proactive.generate_insight(test_conversation)
    
    print("\nGenerated Insight:")
    print(insight if insight else "No insight generated")
    
    # Check if insight was saved
    print("\nInsight saved to:")
    print(proactive.insights_path)
    
def main():
    """Main test function."""
    try:
        # Test welcome message
        proactive = test_welcome_message()
        
        # Test proactive suggestion
        test_proactive_suggestion(proactive)
        
        # Test reflective prompt
        test_reflective_prompt(proactive)
        
        # Test insight generation
        test_insight_generation(proactive)
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Error in tests: {e}", exc_info=True)
        print(f"\nError: {str(e)}")
        
if __name__ == "__main__":
    main() 