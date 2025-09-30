"""
Configuration for Multi-Provider AI System
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class MultiProviderConfig:
    """Configuration management for multi-provider AI system"""
    
    # Provider Priority (can be overridden by environment)
    DEFAULT_PROVIDER_PRIORITY = ["bedrock", "anthropic", "nemo_local", "openai"]
    
    @classmethod
    def get_provider_priority(cls) -> List[str]:
        """Get provider priority from environment or use default"""
        env_priority = os.getenv('PROVIDER_PRIORITY')
        if env_priority:
            return [p.strip() for p in env_priority.split(',')]
        return cls.DEFAULT_PROVIDER_PRIORITY
    
    @classmethod
    def get_bedrock_config(cls) -> Dict[str, str]:
        """Get AWS Bedrock configuration"""
        return {
            'region': os.getenv('AWS_REGION', 'us-east-1'),
            'model_id': os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
            'enabled': os.getenv('ENABLE_BEDROCK', 'true').lower() == 'true'
        }
    
    @classmethod
    def get_nemo_config(cls) -> Dict[str, Any]:
        """Get local NeMo configuration"""
        return {
            'model_path': os.getenv('NEMO_MODEL_PATH', 'gpt-nemo-8b'),
            'enabled': os.getenv('ENABLE_LOCAL_NEMO', 'false').lower() == 'true',
            'device': os.getenv('NEMO_DEVICE', 'auto'),  # auto, cpu, cuda
            'max_memory_gb': int(os.getenv('NEMO_MAX_MEMORY_GB', '8'))
        }
    
    @classmethod
    def get_anthropic_config(cls) -> Dict[str, str]:
        """Get Anthropic configuration"""
        return {
            'api_key': os.getenv('ANTHROPIC_API_KEY'),
            'model': os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
            'enabled': bool(os.getenv('ANTHROPIC_API_KEY'))
        }
    
    @classmethod
    def get_openai_config(cls) -> Dict[str, str]:
        """Get OpenAI configuration"""
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            'enabled': bool(os.getenv('OPENAI_API_KEY'))
        }
    
    @classmethod
    def get_request_routing_rules(cls) -> Dict[str, str]:
        """Get request routing rules for intelligent provider selection"""
        return {
            # Security-sensitive requests
            'sensitive_analysis': os.getenv('SENSITIVE_PROVIDER', 'nemo_local'),
            'confidential': os.getenv('CONFIDENTIAL_PROVIDER', 'nemo_local'),
            
            # Performance-optimized requests
            'dashboard_insights': os.getenv('DASHBOARD_PROVIDER', 'bedrock'),
            'quick_analysis': os.getenv('QUICK_PROVIDER', 'bedrock'),
            
            # Quality-optimized requests
            'incident_analysis': os.getenv('INCIDENT_PROVIDER', 'anthropic'),
            'complex_reasoning': os.getenv('COMPLEX_PROVIDER', 'anthropic'),
            
            # Cost-optimized requests
            'batch_analysis': os.getenv('BATCH_PROVIDER', 'nemo_local'),
            'bulk_processing': os.getenv('BULK_PROVIDER', 'nemo_local')
        }
    
    @classmethod
    def get_quota_limits(cls) -> Dict[str, Any]:
        """Get quota and rate limiting configuration"""
        return {
            'max_tokens_per_request': int(os.getenv('MAX_TOKENS_PER_REQUEST', '600')),
            'max_requests_per_minute': int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60')),
            'max_cost_per_hour': float(os.getenv('MAX_COST_PER_HOUR', '10.0')),
            'enable_cost_tracking': os.getenv('ENABLE_COST_TRACKING', 'true').lower() == 'true'
        }
    
    @classmethod
    def get_fallback_config(cls) -> Dict[str, Any]:
        """Get fallback and retry configuration"""
        return {
            'enable_fallbacks': os.getenv('ENABLE_FALLBACKS', 'true').lower() == 'true',
            'max_retries': int(os.getenv('MAX_PROVIDER_RETRIES', '3')),
            'retry_delay_seconds': float(os.getenv('RETRY_DELAY_SECONDS', '1.0')),
            'circuit_breaker_threshold': int(os.getenv('CIRCUIT_BREAKER_THRESHOLD', '5'))
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'providers_configured': 0
        }
        
        # Check provider configurations
        bedrock_config = cls.get_bedrock_config()
        if bedrock_config['enabled']:
            if not os.getenv('AWS_ACCESS_KEY_ID') and not os.getenv('AWS_PROFILE'):
                validation['warnings'].append("Bedrock enabled but no AWS credentials configured")
            else:
                validation['providers_configured'] += 1
        
        anthropic_config = cls.get_anthropic_config()
        if anthropic_config['enabled']:
            validation['providers_configured'] += 1
        
        openai_config = cls.get_openai_config()
        if openai_config['enabled']:
            validation['providers_configured'] += 1
        
        nemo_config = cls.get_nemo_config()
        if nemo_config['enabled']:
            validation['warnings'].append("Local NeMo enabled - ensure GPU resources are available")
            validation['providers_configured'] += 1
        
        # Check if at least one provider is configured
        if validation['providers_configured'] == 0:
            validation['valid'] = False
            validation['errors'].append("No AI providers configured - system will not function")
        
        return validation

# Environment variable documentation
ENV_VARS_DOCUMENTATION = """
# Multi-Provider AI Configuration

## Provider Priority
PROVIDER_PRIORITY=bedrock,anthropic,nemo_local,openai

## AWS Bedrock Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
ENABLE_BEDROCK=true

## Local NeMo Configuration  
NEMO_MODEL_PATH=/models/gpt-nemo-8b
ENABLE_LOCAL_NEMO=false
NEMO_DEVICE=auto
NEMO_MAX_MEMORY_GB=8

## Anthropic Configuration (existing)
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

## OpenAI Configuration (existing)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-3.5-turbo

## Request Routing
SENSITIVE_PROVIDER=nemo_local
DASHBOARD_PROVIDER=bedrock
INCIDENT_PROVIDER=anthropic
BATCH_PROVIDER=nemo_local

## Quota Management
MAX_TOKENS_PER_REQUEST=600
MAX_REQUESTS_PER_MINUTE=60
MAX_COST_PER_HOUR=10.0
ENABLE_COST_TRACKING=true

## Fallback Configuration
ENABLE_FALLBACKS=true
MAX_PROVIDER_RETRIES=3
RETRY_DELAY_SECONDS=1.0
"""
