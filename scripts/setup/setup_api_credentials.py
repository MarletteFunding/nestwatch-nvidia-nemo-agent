#!/usr/bin/env python3
"""
Setup script for NeMo Agent Toolkit API credentials
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with template values"""
    env_path = Path('.env')
    
    if env_path.exists():
        print("⚠️  .env file already exists. Backing up to .env.backup")
        env_path.rename('.env.backup')
    
    env_content = """# NeMo Agent Toolkit - Environment Configuration
# Fill in your actual API credentials below

# Datadog API Configuration
DATADOG_API_KEY=your_datadog_api_key_here
DATADOG_APP_KEY=your_datadog_app_key_here
DATADOG_SITE=datadoghq.com

# JIRA API Configuration
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your_email@company.com
JIRA_API_TOKEN=your_jira_api_token_here

# Slack API Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# OpenAI Configuration (for AI features)
OPENAI_API_KEY=sk-your_openai_api_key_here

# SRE API Configuration
SRE_API_BASE_URL=https://sre-api-service-ext.bestegg.com
SRE_API_KEY=your_sre_api_key_here

# Development Settings
NODE_ENV=development
NEXT_PUBLIC_API_URL=http://localhost:8000
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file at {env_path.absolute()}")
    return env_path

def print_setup_instructions():
    """Print setup instructions for each service"""
    print("\n" + "="*60)
    print("🚀 NeMo Agent Toolkit - API Setup Instructions")
    print("="*60)
    
    print("\n📊 DATADOG SETUP:")
    print("1. Go to https://app.datadoghq.com/organization-settings/application-keys")
    print("2. Create a new API Key and Application Key")
    print("3. Set DATADOG_API_KEY and DATADOG_APP_KEY in .env file")
    print("4. Optional: Set DATADOG_SITE if using EU/US3 (default: datadoghq.com)")
    
    print("\n🎫 JIRA SETUP:")
    print("1. Go to https://id.atlassian.com/manage-profile/security/api-tokens")
    print("2. Create a new API token")
    print("3. Set JIRA_BASE_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
    print("4. Example: JIRA_BASE_URL=https://yourcompany.atlassian.net")
    
    print("\n💬 SLACK SETUP:")
    print("Option A - Bot Token:")
    print("1. Go to https://api.slack.com/apps")
    print("2. Create a new app and get Bot User OAuth Token")
    print("3. Set SLACK_BOT_TOKEN in .env file")
    print("\nOption B - Webhook:")
    print("1. Go to https://api.slack.com/messaging/webhooks")
    print("2. Create a new webhook URL")
    print("3. Set SLACK_WEBHOOK_URL in .env file")
    
    print("\n🤖 OPENAI SETUP (Optional for AI features):")
    print("1. Go to https://platform.openai.com/api-keys")
    print("2. Create a new API key")
    print("3. Set OPENAI_API_KEY in .env file")
    
    print("\n🔧 SRE API SETUP:")
    print("1. Get your SRE API credentials from your SRE team")
    print("2. Set SRE_API_BASE_URL and SRE_API_KEY in .env file")
    print("3. If using BestEgg, the base URL is already configured")

def main():
    """Main setup function"""
    print("🔧 Setting up NeMo Agent Toolkit API credentials...")
    
    # Create .env file
    env_path = create_env_file()
    
    # Print instructions
    print_setup_instructions()
    
    print("\n" + "="*60)
    print("📝 NEXT STEPS:")
    print("1. Edit the .env file with your actual API credentials")
    print("2. Run: python scripts/test_api_connections.py")
    print("3. Start the application: npm run dev")
    print("4. Visit: http://localhost:3000")
    print("="*60)
    
    print(f"\n✅ Setup complete! Edit {env_path.absolute()} with your credentials.")

if __name__ == "__main__":
    main()
