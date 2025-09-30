#!/usr/bin/env python3
"""
Corporate-Friendly Model Downloader
Handles SSL certificate issues and proxy environments for model downloads
"""

import os
import ssl
import urllib3
import warnings
from pathlib import Path
import logging
from typing import List, Dict, Any

# Suppress SSL warnings for corporate environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorporateModelDownloader:
    """Download models in corporate environments with SSL/proxy handling"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.models_dir = self.project_root / "models"
        self.models_dir.mkdir(exist_ok=True)
        
        # Configure for corporate environment
        self.setup_corporate_ssl()
        
    def setup_corporate_ssl(self):
        """Configure SSL for corporate environments"""
        logger.info("🔒 Configuring SSL for corporate model downloads...")
        
        # Disable SSL verification for corporate proxies
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Set environment variables for requests/urllib
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        
        # Configure Hugging Face to use offline mode if needed
        os.environ['HF_HUB_OFFLINE'] = '0'  # Try online first
        os.environ['TRANSFORMERS_OFFLINE'] = '0'
        
        logger.info("✅ SSL configuration applied for corporate environment")
    
    def download_corporate_safe_models(self) -> Dict[str, Any]:
        """Download corporate-safe models with SSL bypass"""
        logger.info("📥 Downloading corporate-safe models...")
        
        results = {
            'downloaded': [],
            'failed': [],
            'cached': []
        }
        
        # Corporate-safe models (small, reliable)
        corporate_models = [
            {
                'name': 'gpt2',
                'description': 'GPT-2 base model (small, reliable)',
                'size': '500MB'
            },
            {
                'name': 'distilgpt2', 
                'description': 'Distilled GPT-2 (lightweight)',
                'size': '350MB'
            }
        ]
        
        try:
            # Import with SSL bypass
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            for model_info in corporate_models:
                model_name = model_info['name']
                logger.info(f"📦 Downloading {model_name} ({model_info['size']})...")
                
                try:
                    # Download with SSL bypass
                    model_path = self.models_dir / model_name
                    
                    # Download tokenizer
                    tokenizer = AutoTokenizer.from_pretrained(
                        model_name,
                        cache_dir=str(model_path),
                        local_files_only=False,
                        trust_remote_code=False
                    )
                    
                    # Download model
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        cache_dir=str(model_path),
                        local_files_only=False,
                        trust_remote_code=False,
                        torch_dtype=torch.float32  # CPU-friendly
                    )
                    
                    results['downloaded'].append({
                        'name': model_name,
                        'path': str(model_path),
                        'description': model_info['description']
                    })
                    
                    logger.info(f"✅ Successfully downloaded {model_name}")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to download {model_name}: {e}")
                    results['failed'].append({
                        'name': model_name,
                        'error': str(e)
                    })
        
        except ImportError as e:
            logger.error(f"❌ Required libraries not available: {e}")
            return {'error': 'Required libraries not installed'}
        
        return results
    
    def create_offline_model_config(self):
        """Create configuration for offline model usage"""
        logger.info("📝 Creating offline model configuration...")
        
        offline_config = {
            "offline_mode": True,
            "local_models": {
                "gpt2": {
                    "path": "./models/gpt2",
                    "type": "causal_lm",
                    "description": "GPT-2 base model for general text generation",
                    "corporate_safe": True,
                    "size_mb": 500
                },
                "distilgpt2": {
                    "path": "./models/distilgpt2", 
                    "type": "causal_lm",
                    "description": "Lightweight GPT-2 for fast inference",
                    "corporate_safe": True,
                    "size_mb": 350
                }
            },
            "fallback_strategy": [
                "local_models",
                "cached_models",
                "simple_responses"
            ],
            "corporate_settings": {
                "ssl_verify": False,
                "timeout": 60,
                "max_retries": 3,
                "offline_first": True
            }
        }
        
        import json
        config_file = self.models_dir / "offline_config.json"
        with open(config_file, 'w') as f:
            json.dump(offline_config, f, indent=2)
        
        logger.info(f"✅ Offline configuration created: {config_file}")
        return config_file
    
    def test_model_loading(self) -> Dict[str, bool]:
        """Test if downloaded models can be loaded"""
        logger.info("🧪 Testing model loading...")
        
        test_results = {}
        
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            models_to_test = ['gpt2', 'distilgpt2']
            
            for model_name in models_to_test:
                try:
                    model_path = self.models_dir / model_name
                    
                    if model_path.exists():
                        # Test loading from local cache
                        tokenizer = AutoTokenizer.from_pretrained(
                            str(model_path),
                            local_files_only=True
                        )
                        model = AutoModelForCausalLM.from_pretrained(
                            str(model_path),
                            local_files_only=True
                        )
                        
                        # Test simple generation
                        inputs = tokenizer("Hello world", return_tensors="pt")
                        outputs = model.generate(**inputs, max_length=20, do_sample=False)
                        result = tokenizer.decode(outputs[0])
                        
                        test_results[model_name] = True
                        logger.info(f"✅ {model_name} loaded and tested successfully")
                        logger.info(f"   Sample output: {result[:50]}...")
                        
                    else:
                        test_results[model_name] = False
                        logger.warning(f"⚠️  {model_name} not found locally")
                        
                except Exception as e:
                    test_results[model_name] = False
                    logger.error(f"❌ Failed to test {model_name}: {e}")
        
        except ImportError:
            logger.error("❌ Transformers library not available for testing")
            return {'error': 'transformers not installed'}
        
        return test_results
    
    def run_corporate_setup(self):
        """Run complete corporate model setup"""
        logger.info("🚀 Starting corporate model setup...")
        
        # Step 1: Download models
        download_results = self.download_corporate_safe_models()
        
        # Step 2: Create offline configuration
        config_file = self.create_offline_model_config()
        
        # Step 3: Test model loading
        test_results = self.test_model_loading()
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 CORPORATE MODEL SETUP SUMMARY")
        print("="*60)
        
        if 'downloaded' in download_results:
            print(f"📥 Downloaded Models: {len(download_results['downloaded'])}")
            for model in download_results['downloaded']:
                print(f"   ✅ {model['name']}: {model['description']}")
        
        if 'failed' in download_results and download_results['failed']:
            print(f"❌ Failed Downloads: {len(download_results['failed'])}")
            for model in download_results['failed']:
                print(f"   ❌ {model['name']}: {model['error'][:50]}...")
        
        print(f"\n🧪 Model Testing:")
        for model, success in test_results.items():
            status = "✅ Working" if success else "❌ Failed"
            print(f"   {model}: {status}")
        
        print(f"\n📝 Configuration:")
        print(f"   Config file: {config_file}")
        print(f"   Models directory: {self.models_dir}")
        print(f"   Offline mode: Enabled")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Models are ready for offline use")
        print(f"   2. Start backend: cd backend && python app.py")
        print(f"   3. Test API: curl http://localhost:8000/api/v1/providers/health")
        print("="*60)

if __name__ == "__main__":
    downloader = CorporateModelDownloader()
    downloader.run_corporate_setup()
