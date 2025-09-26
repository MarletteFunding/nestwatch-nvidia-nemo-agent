"""
Configuration management for SRE Tools
Handles secure credential loading from environment variables
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Try to load from credentials.py if it exists
try:
    import credentials
    CREDENTIALS_AVAILABLE = True
except ImportError:
    CREDENTIALS_AVAILABLE = False

class Config:
    """Configuration class for SRE Tools"""
    
    # Slack Configuration
    SLACK_SIGNING_SECRET: str = os.getenv('SLACK_SIGNING_SECRET') or (getattr(credentials, 'SLACK_SIGNING_SECRET', None) if CREDENTIALS_AVAILABLE else None) or ''
    SLACK_TOKEN: str = os.getenv('SLACK_TOKEN') or (getattr(credentials, 'SLACK_TOKEN', None) if CREDENTIALS_AVAILABLE else None) or ''
    SLACK_WEBHOOK_URL: str = os.getenv('SLACK_WEBHOOK_URL') or (getattr(credentials, 'SLACK_WEBHOOK_URL', None) if CREDENTIALS_AVAILABLE else None) or 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    
    # JIRA Configuration
    JIRA_API_KEY: str = os.getenv('JIRA_API_KEY') or (getattr(credentials, 'JIRA_API_KEY', None) if CREDENTIALS_AVAILABLE else None) or ''
    JIRA_USERNAME: str = os.getenv('JIRA_USERNAME') or (getattr(credentials, 'JIRA_USERNAME', None) if CREDENTIALS_AVAILABLE else None) or ''
    JIRA_BASE_URL: str = os.getenv('JIRA_BASE_URL') or (getattr(credentials, 'JIRA_BASE_URL', None) if CREDENTIALS_AVAILABLE else None) or ''
    
    # JAMS Configuration
    JAMS_USERNAME: str = os.getenv('JAMS_USERNAME') or (getattr(credentials, 'JAMS_USERNAME', None) if CREDENTIALS_AVAILABLE else None) or ''
    JAMS_PASSWORD: str = os.getenv('JAMS_PASSWORD') or (getattr(credentials, 'JAMS_PASSWORD', None) if CREDENTIALS_AVAILABLE else None) or ''
    JAMS_BASE_URL: str = os.getenv('JAMS_BASE_URL') or (getattr(credentials, 'JAMS_BASE_URL', None) if CREDENTIALS_AVAILABLE else None) or 'https://your-jams-instance.com'
    
    # Datadog Configuration
    DATADOG_API_KEY: str = os.getenv('DATADOG_API_KEY') or (getattr(credentials, 'DATADOG_API_KEY', None) if CREDENTIALS_AVAILABLE else None) or ''
    DATADOG_APP_KEY: str = os.getenv('DATADOG_APP_KEY') or (getattr(credentials, 'DATADOG_APP_KEY', None) if CREDENTIALS_AVAILABLE else None) or ''
    
    # SRE API Configuration (BestEgg SRE API Service)
    SRE_API_BASE_URL: str = os.getenv('SRE_API_BASE_URL') or (getattr(credentials, 'SRE_API_BASE_URL', None) if CREDENTIALS_AVAILABLE else None) or 'https://sre-api-service-ext.bestegg.com'
    SRE_API_KEY: str = os.getenv('SRE_API_KEY') or (getattr(credentials, 'SRE_API_KEY', None) if CREDENTIALS_AVAILABLE else None) or ''
    SRE_API_TOKEN: str = os.getenv('SRE_API_TOKEN') or (getattr(credentials, 'SRE_API_TOKEN', None) if CREDENTIALS_AVAILABLE else None) or ''
    
    # BestEgg Environment Configuration
    BESTEGG_ENV: str = os.getenv('BESTEGG_ENV') or (getattr(credentials, 'BESTEGG_ENV', None) if CREDENTIALS_AVAILABLE else None) or 'sbx'  # sbx, uat, prd
    BESTEGG_WAF_ACL: str = os.getenv('BESTEGG_WAF_ACL') or (getattr(credentials, 'BESTEGG_WAF_ACL', None) if CREDENTIALS_AVAILABLE else None) or ''
    
    # Security Settings
    ENCRYPTION_KEY: str = os.getenv('ENCRYPTION_KEY') or (getattr(credentials, 'ENCRYPTION_KEY', None) if CREDENTIALS_AVAILABLE else None) or 'default_encryption_key_change_me'
    
    @classmethod
    def validate_credentials(cls) -> dict:
        """Validate that required credentials are present"""
        validation_results = {
            'slack': {
                'signing_secret': bool(cls.SLACK_SIGNING_SECRET and cls.SLACK_SIGNING_SECRET != 'your_slack_signing_secret_here'),
                'token': bool(cls.SLACK_TOKEN and cls.SLACK_TOKEN != 'your_slack_bot_token_here'),
                'webhook_url': bool(cls.SLACK_WEBHOOK_URL and 'YOUR/SLACK/WEBHOOK' not in cls.SLACK_WEBHOOK_URL)
            },
            'jira': {
                'api_key': bool(cls.JIRA_API_KEY and cls.JIRA_API_KEY != 'your_jira_api_key_here'),
                'username': bool(cls.JIRA_USERNAME and cls.JIRA_USERNAME != 'your_jira_username_here'),
                'base_url': bool(cls.JIRA_BASE_URL)
            },
            'jams': {
                'username': bool(cls.JAMS_USERNAME and cls.JAMS_USERNAME != 'your_jams_username_here'),
                'password': bool(cls.JAMS_PASSWORD and cls.JAMS_PASSWORD != 'your_jams_password_here'),
                'base_url': bool(cls.JAMS_BASE_URL and 'your_jams_base_url_here' not in cls.JAMS_BASE_URL)
            },
            'datadog': {
                'api_key': bool(cls.DATADOG_API_KEY and cls.DATADOG_API_KEY != 'your_datadog_api_key_here'),
                'app_key': bool(cls.DATADOG_APP_KEY and cls.DATADOG_APP_KEY != 'your_datadog_app_key_here')
            }
        }
        
        return validation_results
    
    @classmethod
    def get_credential_status(cls) -> str:
        """Get a human-readable status of credential configuration"""
        validation = cls.validate_credentials()
        
        status_lines = ["🔐 CREDENTIAL STATUS REPORT", ""]
        
        # Slack status
        slack_status = "✅" if all(validation['slack'].values()) else "⚠️"
        status_lines.append(f"{slack_status} Slack: {'Configured' if all(validation['slack'].values()) else 'Partially configured'}")
        if not validation['slack']['signing_secret']:
            status_lines.append("   ❌ Missing: SLACK_SIGNING_SECRET")
        if not validation['slack']['token']:
            status_lines.append("   ❌ Missing: SLACK_TOKEN")
        if not validation['slack']['webhook_url']:
            status_lines.append("   ❌ Missing: SLACK_WEBHOOK_URL")
        
        # JIRA status
        jira_status = "✅" if all(validation['jira'].values()) else "⚠️"
        status_lines.append(f"{jira_status} JIRA: {'Configured' if all(validation['jira'].values()) else 'Partially configured'}")
        if not validation['jira']['api_key']:
            status_lines.append("   ❌ Missing: JIRA_API_KEY")
        if not validation['jira']['username']:
            status_lines.append("   ❌ Missing: JIRA_USERNAME")
        
        # JAMS status
        jams_status = "✅" if all(validation['jams'].values()) else "⚠️"
        status_lines.append(f"{jams_status} JAMS: {'Configured' if all(validation['jams'].values()) else 'Partially configured'}")
        if not validation['jams']['username']:
            status_lines.append("   ❌ Missing: JAMS_USERNAME")
        if not validation['jams']['password']:
            status_lines.append("   ❌ Missing: JAMS_PASSWORD")
        if not validation['jams']['base_url']:
            status_lines.append("   ❌ Missing: JAMS_BASE_URL")
        
        # Datadog status
        datadog_status = "✅" if all(validation['datadog'].values()) else "⚠️"
        status_lines.append(f"{datadog_status} Datadog: {'Configured' if all(validation['datadog'].values()) else 'Optional - not configured'}")
        
        return "\n".join(status_lines)

# Global config instance
config = Config()
