#!/usr/bin/env python3
"""
Zscaler-Aware Multi-Provider AI Setup Script
Handles corporate proxy environments and secure downloads
"""

import os
import sys
import subprocess
import urllib.request
import ssl
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZscalerAwareSetup:
    """Setup class that handles Zscaler proxy configurations"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"
        self.proxy_detected = self.detect_proxy_environment()
        
    def detect_proxy_environment(self) -> bool:
        """Detect if we're in a corporate proxy environment"""
        proxy_indicators = [
            'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
            'CORPORATE_PROXY', 'ZSCALER_PROXY'
        ]
        
        for indicator in proxy_indicators:
            if os.getenv(indicator):
                logger.info(f"🔍 Detected proxy environment: {indicator}")
                return True
                
        # Check for common corporate domains in environment
        hostname = os.getenv('HOSTNAME', '').lower()
        if any(corp in hostname for corp in ['corp', 'corporate', 'company']):
            logger.info("🔍 Detected corporate environment from hostname")
            return True
            
        return False
    
    def configure_pip_for_proxy(self):
        """Configure pip to work with corporate proxies"""
        logger.info("🔧 Configuring pip for corporate proxy environment...")
        
        pip_conf_dir = Path.home() / ".pip"
        pip_conf_dir.mkdir(exist_ok=True)
        pip_conf_file = pip_conf_dir / "pip.conf"
        
        # Basic proxy-friendly pip configuration
        pip_config = """[global]
timeout = 60
retries = 5
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
               download.pytorch.org
               developer.download.nvidia.com

[install]
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
               download.pytorch.org
               developer.download.nvidia.com
"""
        
        # Add proxy configuration if detected
        if self.proxy_detected:
            http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
            https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
            
            if http_proxy or https_proxy:
                pip_config += f"""
proxy = {https_proxy or http_proxy}
"""
        
        with open(pip_conf_file, 'w') as f:
            f.write(pip_config)
            
        logger.info(f"✅ Pip configuration written to {pip_conf_file}")
    
    def setup_ssl_context(self):
        """Setup SSL context for corporate environments"""
        logger.info("🔒 Configuring SSL for corporate environment...")
        
        # Create unverified SSL context for corporate proxies
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Set environment variables for requests/urllib
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        
        logger.info("✅ SSL context configured for corporate proxy")
    
    def install_dependencies_safely(self):
        """Install dependencies with proxy-aware methods"""
        logger.info("📦 Installing dependencies with proxy awareness...")
        
        # Activate virtual environment
        if not self.venv_path.exists():
            logger.error("❌ Virtual environment not found. Please create it first.")
            return False
            
        # Use the virtual environment's pip
        pip_cmd = str(self.venv_path / "bin" / "pip")
        if sys.platform == "win32":
            pip_cmd = str(self.venv_path / "Scripts" / "pip.exe")
        
        # Install dependencies in stages for better proxy handling
        dependency_groups = [
            # Core dependencies first
            ["fastapi>=0.104.1", "uvicorn[standard]>=0.24.0", "pydantic>=2.5.0"],
            
            # AI dependencies
            ["openai>=1.0.0", "anthropic>=0.18.0", "python-dotenv>=1.0.0"],
            
            # AWS dependencies
            ["boto3>=1.34.0", "botocore>=1.34.0"],
            
            # PyTorch (special handling for corporate environments)
            ["torch>=2.0.0", "--index-url", "https://download.pytorch.org/whl/cpu"],
            
            # Transformers and other ML dependencies
            ["transformers>=4.21.0", "omegaconf>=2.3.0", "hydra-core>=1.3.0"]
        ]
        
        for group in dependency_groups:
            logger.info(f"📦 Installing: {' '.join(group)}")
            
            cmd = [pip_cmd, "install", "--timeout", "300", "--retries", "5"] + group
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if result.returncode != 0:
                    logger.warning(f"⚠️  Installation warning for {group}: {result.stderr}")
                else:
                    logger.info(f"✅ Successfully installed: {' '.join(group)}")
            except subprocess.TimeoutExpired:
                logger.error(f"❌ Timeout installing {group}")
            except Exception as e:
                logger.error(f"❌ Error installing {group}: {e}")
        
        return True
    
    def setup_nemo_for_corporate(self):
        """Setup NeMo with corporate-friendly model downloads"""
        logger.info("🤖 Setting up NeMo for corporate environment...")
        
        # Create models directory
        models_dir = self.project_root / "models"
        models_dir.mkdir(exist_ok=True)
        
        # Use Hugging Face models that work well in corporate environments
        corporate_friendly_models = [
            "microsoft/DialoGPT-medium",  # Good for conversational AI
            "microsoft/DialoGPT-small",   # Lightweight option
            "gpt2",                       # Classic, reliable
        ]
        
        # Create model configuration for corporate use
        model_config = {
            "corporate_models": corporate_friendly_models,
            "download_method": "huggingface_hub",
            "cache_dir": str(models_dir),
            "offline_mode": False,
            "proxy_friendly": True
        }
        
        import json
        with open(models_dir / "corporate_config.json", 'w') as f:
            json.dump(model_config, f, indent=2)
        
        logger.info("✅ NeMo corporate configuration created")
        return True
    
    def create_zscaler_env_template(self):
        """Create environment template with Zscaler-specific settings"""
        logger.info("📝 Creating Zscaler-aware environment template...")
        
        zscaler_env_content = """# Zscaler-Aware Multi-Provider Configuration
# Corporate Environment Settings

# ==============================================
# PROXY CONFIGURATION (if needed)
# ==============================================
# Uncomment and configure if your corporate environment requires explicit proxy settings
# HTTP_PROXY=http://proxy.company.com:8080
# HTTPS_PROXY=http://proxy.company.com:8080
# NO_PROXY=localhost,127.0.0.1,.company.com

# ==============================================
# SSL/TLS CONFIGURATION FOR CORPORATE NETWORKS
# ==============================================
# For corporate environments with SSL inspection
PYTHONHTTPSVERIFY=0
REQUESTS_CA_BUNDLE=""
CURL_CA_BUNDLE=""

# ==============================================
# PROVIDER PRIORITY (CORPORATE OPTIMIZED)
# ==============================================
# Prioritize providers that work well with corporate networks
PROVIDER_PRIORITY=bedrock,anthropic,openai

# ==============================================
# AWS BEDROCK (CORPORATE FRIENDLY)
# ==============================================
# AWS Bedrock works well through corporate proxies
ENABLE_BEDROCK=true
AWS_REGION=us-east-1
# Use IAM roles or AWS CLI profiles when possible
# AWS_PROFILE=your-corporate-profile
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# ==============================================
# LOCAL NEMO (CORPORATE SAFE)
# ==============================================
# Local models for sensitive corporate data
ENABLE_LOCAL_NEMO=false
NEMO_MODEL_PATH=microsoft/DialoGPT-medium
NEMO_DEVICE=cpu
NEMO_MAX_MEMORY_GB=4

# ==============================================
# ANTHROPIC (EXISTING CORPORATE SETUP)
# ==============================================
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# ==============================================
# OPENAI (CORPORATE FALLBACK)
# ==============================================
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# ==============================================
# CORPORATE SECURITY SETTINGS
# ==============================================
# Route sensitive requests to local processing
SENSITIVE_PROVIDER=nemo_local
CONFIDENTIAL_PROVIDER=nemo_local

# Conservative quota settings for corporate use
MAX_TOKENS_PER_REQUEST=300
MAX_REQUESTS_PER_MINUTE=30
MAX_COST_PER_HOUR=5.0
ENABLE_COST_TRACKING=true

# ==============================================
# RELIABILITY FOR CORPORATE NETWORKS
# ==============================================
ENABLE_FALLBACKS=true
MAX_PROVIDER_RETRIES=5
RETRY_DELAY_SECONDS=2.0
CIRCUIT_BREAKER_THRESHOLD=3

# ==============================================
# CORPORATE DEPLOYMENT FLAGS
# ==============================================
MULTI_PROVIDER_ENABLED=true
BEDROCK_ROLLOUT_PERCENTAGE=100
NEMO_ROLLOUT_PERCENTAGE=0
CORPORATE_MODE=true
"""
        
        env_file = self.project_root / "zscaler.env.example"
        with open(env_file, 'w') as f:
            f.write(zscaler_env_content)
        
        logger.info(f"✅ Zscaler environment template created: {env_file}")
        return True
    
    def test_network_connectivity(self):
        """Test network connectivity to required services"""
        logger.info("🌐 Testing network connectivity...")
        
        test_urls = [
            ("PyPI", "https://pypi.org/simple/"),
            ("AWS Bedrock", "https://bedrock-runtime.us-east-1.amazonaws.com/"),
            ("Anthropic", "https://api.anthropic.com/"),
            ("OpenAI", "https://api.openai.com/"),
            ("Hugging Face", "https://huggingface.co/"),
        ]
        
        results = {}
        for name, url in test_urls:
            try:
                response = urllib.request.urlopen(url, timeout=10)
                results[name] = "✅ Connected"
                logger.info(f"✅ {name}: Connected")
            except Exception as e:
                results[name] = f"❌ Failed: {str(e)[:50]}..."
                logger.warning(f"❌ {name}: {e}")
        
        return results
    
    def run_setup(self):
        """Run the complete Zscaler-aware setup"""
        logger.info("🚀 Starting Zscaler-aware multi-provider setup...")
        
        # Step 1: Configure for proxy environment
        if self.proxy_detected:
            self.configure_pip_for_proxy()
            self.setup_ssl_context()
        
        # Step 2: Test connectivity
        connectivity = self.test_network_connectivity()
        
        # Step 3: Install dependencies
        self.install_dependencies_safely()
        
        # Step 4: Setup NeMo for corporate use
        self.setup_nemo_for_corporate()
        
        # Step 5: Create corporate environment template
        self.create_zscaler_env_template()
        
        logger.info("🎉 Zscaler-aware setup complete!")
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 ZSCALER-AWARE SETUP SUMMARY")
        print("="*60)
        print(f"📁 Project Root: {self.project_root}")
        print(f"🔍 Proxy Detected: {'Yes' if self.proxy_detected else 'No'}")
        print("\n📊 Network Connectivity:")
        for service, status in connectivity.items():
            print(f"   {service}: {status}")
        
        print(f"\n📝 Next Steps:")
        print(f"   1. Copy zscaler.env.example to .env.local")
        print(f"   2. Configure your API keys in .env.local")
        print(f"   3. Test with: python -m pytest tests/ -v")
        print(f"   4. Start server: cd backend && python app.py")
        print("="*60)

if __name__ == "__main__":
    setup = ZscalerAwareSetup()
    setup.run_setup()
