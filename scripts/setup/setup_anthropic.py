#!/usr/bin/env python3
"""
Setup script for Anthropic Claude API integration
"""

import os
import sys
from pathlib import Path

def setup_anthropic():
    """Setup Anthropic Claude API configuration"""
    print("🤖 Anthropic Claude API Setup")
    print("=" * 50)
    
    # Check if .env file exists
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found. Please run the main setup first.")
        return False
    
    print("\n📋 Current Anthropic Configuration:")
    print("-" * 30)
    
    # Read current .env file
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Check current settings
    anthropic_key = None
    anthropic_model = None
    
    for line in content.split('\n'):
        if line.startswith('ANTHROPIC_API_KEY='):
            anthropic_key = line.split('=', 1)[1]
        elif line.startswith('ANTHROPIC_MODEL='):
            anthropic_model = line.split('=', 1)[1]
    
    print(f"API Key: {'✅ Set' if anthropic_key and anthropic_key != 'your_anthropic_api_key_here' else '❌ Not set'}")
    print(f"Model: {anthropic_model}")
    
    print("\n🔧 Configuration Options:")
    print("1. Set Anthropic API Key")
    print("2. Change Claude Model")
    print("3. Test Anthropic Connection")
    print("4. View Available Models")
    print("5. Exit")
    
    while True:
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            api_key = input("Enter your Anthropic API Key: ").strip()
            if api_key:
                # Update .env file
                new_content = content.replace(
                    "ANTHROPIC_API_KEY=your_anthropic_api_key_here",
                    f"ANTHROPIC_API_KEY={api_key}"
                )
                with open(env_path, 'w') as f:
                    f.write(new_content)
                print("✅ Anthropic API Key updated!")
            else:
                print("❌ API Key cannot be empty")
        
        elif choice == "2":
            print("\nAvailable Claude Models:")
            models = [
                ("claude-3-5-sonnet-20241022", "Claude 3.5 Sonnet (Latest, Recommended)"),
                ("claude-3-opus-20240229", "Claude 3 Opus (Most Capable)"),
                ("claude-3-sonnet-20240229", "Claude 3 Sonnet (Balanced)"),
                ("claude-3-haiku-20240307", "Claude 3 Haiku (Fastest)")
            ]
            
            for i, (model, desc) in enumerate(models, 1):
                print(f"{i}. {model} - {desc}")
            
            model_choice = input("Select model (1-4): ").strip()
            try:
                model_idx = int(model_choice) - 1
                if 0 <= model_idx < len(models):
                    selected_model = models[model_idx][0]
                    new_content = content.replace(
                        f"ANTHROPIC_MODEL={anthropic_model}",
                        f"ANTHROPIC_MODEL={selected_model}"
                    )
                    with open(env_path, 'w') as f:
                        f.write(new_content)
                    print(f"✅ Model updated to {selected_model}")
                else:
                    print("❌ Invalid selection")
            except ValueError:
                print("❌ Invalid input")
        
        elif choice == "3":
            print("\n🧪 Testing Anthropic Connection...")
            try:
                import anthropic
                from dotenv import load_dotenv
                
                load_dotenv()
                api_key = os.getenv("ANTHROPIC_API_KEY")
                
                if not api_key or api_key == "your_anthropic_api_key_here":
                    print("❌ Anthropic API Key not set")
                    continue
                
                client = anthropic.Anthropic(api_key=api_key)
                
                # Test with a simple message
                response = client.messages.create(
                    model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                    max_tokens=100,
                    messages=[{
                        "role": "user",
                        "content": "Hello! This is a test message. Please respond with 'Test successful!'"
                    }]
                )
                
                print("✅ Anthropic connection successful!")
                print(f"Response: {response.content[0].text}")
                
            except ImportError:
                print("❌ Anthropic package not installed. Run: pip install anthropic")
            except Exception as e:
                print(f"❌ Connection failed: {e}")
        
        elif choice == "4":
            print("\n📚 Available Claude Models:")
            print("-" * 40)
            
            model_info = {
                "claude-3-5-sonnet-20241022": {
                    "name": "Claude 3.5 Sonnet",
                    "description": "Latest model with improved reasoning and code generation",
                    "context_window": "200k tokens",
                    "cost_per_1k_tokens": "$0.003 (input) / $0.015 (output)",
                    "best_for": "Advanced SRE analysis, complex troubleshooting, code generation"
                },
                "claude-3-opus-20240229": {
                    "name": "Claude 3 Opus",
                    "description": "Most capable model, best for complex SRE analysis and reasoning",
                    "context_window": "200k tokens",
                    "cost_per_1k_tokens": "$0.015 (input) / $0.075 (output)",
                    "best_for": "Complex incident analysis, root cause analysis, detailed recommendations"
                },
                "claude-3-sonnet-20240229": {
                    "name": "Claude 3 Sonnet",
                    "description": "Balanced performance and cost, recommended for most SRE tasks",
                    "context_window": "200k tokens",
                    "cost_per_1k_tokens": "$0.003 (input) / $0.015 (output)",
                    "best_for": "General SRE analysis, event correlation, standard recommendations"
                },
                "claude-3-haiku-20240307": {
                    "name": "Claude 3 Haiku",
                    "description": "Fastest and most cost-effective, good for simple SRE tasks",
                    "context_window": "200k tokens",
                    "cost_per_1k_tokens": "$0.00025 (input) / $0.00125 (output)",
                    "best_for": "Quick summaries, simple analysis, high-volume processing"
                }
            }
            
            for model, info in model_info.items():
                print(f"\n🤖 {info['name']} ({model})")
                print(f"   Description: {info['description']}")
                print(f"   Context Window: {info['context_window']}")
                print(f"   Cost: {info['cost_per_1k_tokens']}")
                print(f"   Best For: {info['best_for']}")
        
        elif choice == "5":
            print("\n👋 Setup complete!")
            break
        
        else:
            print("❌ Invalid option. Please select 1-5.")
    
    return True

if __name__ == "__main__":
    setup_anthropic()
