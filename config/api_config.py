#!/usr/bin/env python3
"""
API Configuration for NeMo Agent Toolkit
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv

class APIConfig:
    """Centralized API configuration management"""
    
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Optional[str]]:
        """Load configuration from environment variables"""
        return {
            # Datadog Configuration
            'datadog_api_key': os.getenv('DATADOG_API_KEY'),
            'datadog_app_key': os.getenv('DATADOG_APP_KEY'),
            'datadog_site': os.getenv('DATADOG_SITE', 'datadoghq.com'),
            
            # JIRA Configuration
            'jira_base_url': os.getenv('JIRA_BASE_URL'),
            'jira_username': os.getenv('JIRA_USERNAME'),
            'jira_api_token': os.getenv('JIRA_API_TOKEN'),
            
            # Slack Configuration
            'slack_bot_token': os.getenv('SLACK_BOT_TOKEN'),
            'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
            
            # SRE API Configuration
            'sre_api_base_url': os.getenv('SRE_API_BASE_URL', 'https://sre-api-service-ext.bestegg.com'),
            'sre_api_key': os.getenv('SRE_API_KEY'),
            
            # OpenAI Configuration
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
        }
    
    def get_datadog_config(self) -> Dict[str, str]:
        """Get Datadog API configuration"""
        return {
            'api_key': self.config['datadog_api_key'],
            'app_key': self.config['datadog_app_key'],
            'site': self.config['datadog_site']
        }
    
    def get_jira_config(self) -> Dict[str, str]:
        """Get JIRA API configuration"""
        return {
            'base_url': self.config['jira_base_url'],
            'username': self.config['jira_username'],
            'api_token': self.config['jira_api_token']
        }
    
    def get_slack_config(self) -> Dict[str, str]:
        """Get Slack API configuration"""
        return {
            'bot_token': self.config['slack_bot_token'],
            'webhook_url': self.config['slack_webhook_url']
        }
    
    def is_configured(self, service: str) -> bool:
        """Check if a service is properly configured"""
        if service == 'datadog':
            return all([
                self.config['datadog_api_key'],
                self.config['datadog_app_key']
            ])
        elif service == 'jira':
            return all([
                self.config['jira_base_url'],
                self.config['jira_username'],
                self.config['jira_api_token']
            ])
        elif service == 'slack':
            return any([
                self.config['slack_bot_token'],
                self.config['slack_webhook_url']
            ])
        return False
    
    def get_missing_config(self, service: str) -> list:
        """Get list of missing configuration for a service"""
        missing = []
        if service == 'datadog':
            if not self.config['datadog_api_key']:
                missing.append('DATADOG_API_KEY')
            if not self.config['datadog_app_key']:
                missing.append('DATADOG_APP_KEY')
        elif service == 'jira':
            if not self.config['jira_base_url']:
                missing.append('JIRA_BASE_URL')
            if not self.config['jira_username']:
                missing.append('JIRA_USERNAME')
            if not self.config['jira_api_token']:
                missing.append('JIRA_API_TOKEN')
        elif service == 'slack':
            if not self.config['slack_bot_token'] and not self.config['slack_webhook_url']:
                missing.append('SLACK_BOT_TOKEN or SLACK_WEBHOOK_URL')
        return missing

# Global configuration instance
api_config = APIConfig()
