"""
Enhanced Multi-Provider LLM System for NestWatch
Supports AWS Bedrock, Local NeMo, Anthropic, and OpenAI with intelligent fallbacks
Corporate/Zscaler environment optimized
"""

from typing import List, Dict, Any, Optional, Literal, Tuple, Union
import logging
import os
import warnings
import time
import json
import uuid
import re
import asyncio
import ssl
import urllib3
from enum import Enum
from dataclasses import dataclass
from jsonschema import validate, ValidationError

try:
    from .prompt_registry import SYSTEM_SRE, CARD_EVENT_ANALYSIS, SCHEMA_EVENT_ANALYSIS
    from .sre_context_compactor import context_compactor
except ImportError:
    from prompt_registry import SYSTEM_SRE, CARD_EVENT_ANALYSIS, SCHEMA_EVENT_ANALYSIS
    from sre_context_compactor import context_compactor

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class ProviderType(Enum):
    BEDROCK = "bedrock"
    NEMO_LOCAL = "nemo_local"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"

@dataclass
class ProviderResponse:
    content: str
    provider: ProviderType
    model: str
    tokens_used: int
    response_time: float
    cost_estimate: float
    success: bool
    error: Optional[str] = None

class CorporateEnvironmentHandler:
    """Handle corporate environment configurations like Zscaler"""
    
    def __init__(self):
        self.is_corporate = self._detect_corporate_environment()
        self.proxy_config = self._get_proxy_config()
        if self.is_corporate:
            self._configure_ssl_for_corporate()
    
    def _detect_corporate_environment(self) -> bool:
        """Detect if running in corporate environment"""
        corporate_indicators = [
            'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
            'CORPORATE_PROXY', 'ZSCALER_PROXY', 'CORPORATE_MODE'
        ]
        
        for indicator in corporate_indicators:
            if os.getenv(indicator):
                logger.info(f"🏢 Corporate environment detected: {indicator}")
                return True
        
        # Check hostname patterns
        hostname = os.getenv('HOSTNAME', '').lower()
        if any(corp in hostname for corp in ['corp', 'corporate', 'company']):
            logger.info("🏢 Corporate environment detected from hostname")
            return True
        
        return False
    
    def _get_proxy_config(self) -> Dict[str, str]:
        """Get proxy configuration for corporate environments"""
        return {
            'http': os.getenv('HTTP_PROXY') or os.getenv('http_proxy'),
            'https': os.getenv('HTTPS_PROXY') or os.getenv('https_proxy'),
            'no_proxy': os.getenv('NO_PROXY') or os.getenv('no_proxy', 'localhost,127.0.0.1')
        }
    
    def _configure_ssl_for_corporate(self):
        """Configure SSL settings for corporate environments"""
        logger.info("🔒 Configuring SSL for corporate environment")
        
        # Disable SSL verification for corporate proxies if needed
        if os.getenv('PYTHONHTTPSVERIFY', '1') == '0':
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            ssl._create_default_https_context = ssl._create_unverified_context
            logger.warning("⚠️  SSL verification disabled for corporate proxy")
    
    def get_requests_config(self) -> Dict[str, Any]:
        """Get requests configuration for corporate environments"""
        config = {
            'timeout': 60,  # Longer timeout for corporate networks
            'verify': os.getenv('PYTHONHTTPSVERIFY', '1') != '0'
        }
        
        if self.proxy_config['https'] or self.proxy_config['http']:
            config['proxies'] = {
                'http': self.proxy_config['http'],
                'https': self.proxy_config['https']
            }
            logger.info("🌐 Using proxy configuration for requests")
        
        return config

class ProviderAvailability:
    """Track availability of different AI providers"""
    
    def __init__(self):
        self.bedrock = self._check_bedrock()
        self.nemo_local = self._check_nemo_local()
        self.anthropic = self._check_anthropic()
        self.openai = self._check_openai()
        self.torch = self._check_torch()
        
    def _check_bedrock(self) -> bool:
        try:
            import boto3
            return True
        except ImportError:
            logger.warning("AWS Bedrock not available: boto3 not installed")
            return False
    
    def _check_nemo_local(self) -> bool:
        try:
            # Try NeMo first, fall back to transformers
            try:
                import nemo.collections.nlp as nemo_nlp
                import torch
                logger.info("✅ Real NVIDIA NeMo toolkit detected")
                return True
            except ImportError:
                # Fall back to transformers
                import torch
                from transformers import AutoTokenizer, AutoModelForCausalLM
                logger.info("✅ Transformers-based NeMo fallback available")
                return True
        except ImportError:
            logger.warning("Local NeMo not available: PyTorch and transformers not installed")
            return False
    
    def _check_anthropic(self) -> bool:
        try:
            import anthropic
            return True
        except ImportError:
            logger.warning("Anthropic not available: anthropic package not installed")
            return False
    
    def _check_openai(self) -> bool:
        try:
            from openai import OpenAI
            return True
        except ImportError:
            logger.warning("OpenAI not available: openai package not installed")
            return False
    
    def _check_torch(self) -> bool:
        try:
            import torch
            return True
        except ImportError:
            return False

class BedrockProvider:
    """AWS Bedrock provider for Claude models"""
    
    def __init__(self):
        self.client = None
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.model_id = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')
        self.initialized = False
        
    def initialize(self) -> bool:
        try:
            import boto3
            self.client = boto3.client('bedrock-runtime', region_name=self.region)
            self.initialized = True
            logger.info(f"✅ AWS Bedrock initialized: {self.model_id} in {self.region}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bedrock: {e}")
            return False
    
    async def generate(self, prompt: str, max_tokens: int = 600, temperature: float = 0.0) -> ProviderResponse:
        if not self.initialized:
            raise Exception("Bedrock provider not initialized")
        
        start_time = time.time()
        
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            })
            
            response = self.client.invoke_model(
                body=body,
                modelId=self.model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            content = response_body['content'][0]['text']
            
            response_time = time.time() - start_time
            tokens_used = response_body.get('usage', {}).get('output_tokens', 0)
            
            return ProviderResponse(
                content=content,
                provider=ProviderType.BEDROCK,
                model=self.model_id,
                tokens_used=tokens_used,
                response_time=response_time,
                cost_estimate=self._estimate_cost(tokens_used),
                success=True
            )
            
        except Exception as e:
            return ProviderResponse(
                content="",
                provider=ProviderType.BEDROCK,
                model=self.model_id,
                tokens_used=0,
                response_time=time.time() - start_time,
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    def _estimate_cost(self, tokens: int) -> float:
        # Bedrock Claude pricing (approximate)
        input_cost_per_1k = 0.003  # $3 per 1M input tokens
        output_cost_per_1k = 0.015  # $15 per 1M output tokens
        return (tokens / 1000) * output_cost_per_1k

class NeMoLocalProvider:
    """Local NVIDIA NeMo model provider"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_path = os.getenv('NEMO_MODEL_PATH', 'gpt-nemo-8b')
        self.initialized = False
        self.device = None
        
    def initialize(self) -> bool:
        try:
            # Try actual NeMo first, fall back to transformers
            try:
                import nemo.collections.nlp as nemo_nlp
                import torch
                
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                
                # Load NeMo model (this will take time on first load)
                logger.info(f"🔄 Loading NeMo model: {self.model_path} (this may take 30-60 seconds)")
                self.model = nemo_nlp.models.LanguageModelingModel.restore_from(self.model_path)
                self.model.to(self.device)
                self.model.eval()
                
                self.initialized = True
                logger.info(f"✅ Real NeMo initialized: {self.model_path} on {self.device}")
                return True
                
            except ImportError:
                # Fall back to transformers-based local model
                logger.info("🔄 NeMo not available, using transformers-based local model")
                return self._initialize_transformers_fallback()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize local NeMo: {e}")
            return False
    
    def _initialize_transformers_fallback(self) -> bool:
        """Initialize using transformers library as NeMo fallback"""
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Use a lightweight model for demonstration
            model_name = "microsoft/DialoGPT-medium"  # Small conversational model
            
            logger.info(f"🔄 Loading transformers model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model.to(self.device)
            self.model.eval()
            
            self.initialized = True
            self.model_path = model_name
            logger.info(f"✅ Transformers-based NeMo fallback initialized: {model_name} on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize transformers fallback: {e}")
            return False
    
    async def generate(self, prompt: str, max_tokens: int = 600, temperature: float = 0.0) -> ProviderResponse:
        if not self.initialized:
            raise Exception("NeMo local provider not initialized")
        
        start_time = time.time()
        
        try:
            # Check if we have a real NeMo model or transformers fallback
            if hasattr(self, 'tokenizer') and self.tokenizer is not None:
                # Using transformers fallback
                content = await self._generate_with_transformers(prompt, max_tokens, temperature)
            else:
                # Using real NeMo model
                content = await self._generate_with_nemo(prompt, max_tokens, temperature)
            
            response_time = time.time() - start_time
            
            return ProviderResponse(
                content=content,
                provider=ProviderType.NEMO_LOCAL,
                model=self.model_path,
                tokens_used=len(content.split()),  # Approximate
                response_time=response_time,
                cost_estimate=0.0,  # Local model = no API cost
                success=True
            )
            
        except Exception as e:
            return ProviderResponse(
                content="",
                provider=ProviderType.NEMO_LOCAL,
                model=self.model_path,
                tokens_used=0,
                response_time=time.time() - start_time,
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    async def _generate_with_nemo(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using real NeMo model"""
        import torch
        
        with torch.no_grad():
            response = self.model.generate(
                inputs=[prompt],
                length_params={"max_length": max_tokens, "min_length": 10},
                sampling_params={"temperature": temperature, "top_k": 50}
            )
        
        return response[0] if response else ""
    
    async def _generate_with_transformers(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate using transformers fallback"""
        import torch
        
        # Encode the prompt
        inputs = self.tokenizer.encode(prompt, return_tensors='pt').to(self.device)
        
        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=min(inputs.shape[1] + max_tokens, 1024),  # Limit total length
                temperature=max(temperature, 0.1),  # Avoid zero temperature
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=1
            )
        
        # Decode the response (exclude the input prompt)
        response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        return response.strip()

class AnthropicProvider:
    """Direct Anthropic API provider (existing functionality)"""
    
    def __init__(self):
        self.client = None
        self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        self.initialized = False
        
    def initialize(self) -> bool:
        try:
            import anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not set")
                return False
                
            self.client = anthropic.Anthropic(api_key=api_key)
            self.initialized = True
            logger.info(f"✅ Anthropic initialized: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic: {e}")
            return False
    
    async def generate(self, prompt: str, max_tokens: int = 600, temperature: float = 0.0) -> ProviderResponse:
        if not self.initialized:
            raise Exception("Anthropic provider not initialized")
        
        start_time = time.time()
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            response_time = time.time() - start_time
            tokens_used = response.usage.output_tokens
            
            return ProviderResponse(
                content=content,
                provider=ProviderType.ANTHROPIC,
                model=self.model,
                tokens_used=tokens_used,
                response_time=response_time,
                cost_estimate=self._estimate_cost(response.usage.input_tokens, tokens_used),
                success=True
            )
            
        except Exception as e:
            return ProviderResponse(
                content="",
                provider=ProviderType.ANTHROPIC,
                model=self.model,
                tokens_used=0,
                response_time=time.time() - start_time,
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Anthropic Claude pricing
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015
        return (input_tokens / 1000) * input_cost_per_1k + (output_tokens / 1000) * output_cost_per_1k

class OpenAIProvider:
    """OpenAI API provider (existing functionality)"""
    
    def __init__(self):
        self.client = None
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.initialized = False
        
    def initialize(self) -> bool:
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY not set")
                return False
                
            self.client = OpenAI(api_key=api_key)
            self.initialized = True
            logger.info(f"✅ OpenAI initialized: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI: {e}")
            return False
    
    async def generate(self, prompt: str, max_tokens: int = 600, temperature: float = 0.0) -> ProviderResponse:
        if not self.initialized:
            raise Exception("OpenAI provider not initialized")
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            response_time = time.time() - start_time
            tokens_used = response.usage.completion_tokens
            
            return ProviderResponse(
                content=content,
                provider=ProviderType.OPENAI,
                model=self.model,
                tokens_used=tokens_used,
                response_time=response_time,
                cost_estimate=self._estimate_cost(response.usage.prompt_tokens, tokens_used),
                success=True
            )
            
        except Exception as e:
            return ProviderResponse(
                content="",
                provider=ProviderType.OPENAI,
                model=self.model,
                tokens_used=0,
                response_time=time.time() - start_time,
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # OpenAI GPT pricing (approximate)
        input_cost_per_1k = 0.001
        output_cost_per_1k = 0.002
        return (input_tokens / 1000) * input_cost_per_1k + (output_tokens / 1000) * output_cost_per_1k

class MultiProviderLLM:
    """Enhanced multi-provider LLM system with intelligent routing and fallbacks"""
    
    def __init__(self, provider_priority: Optional[List[str]] = None):
        self.availability = ProviderAvailability()
        
        # Default provider priority (can be overridden by environment)
        default_priority = ["bedrock", "anthropic", "nemo_local", "openai"]
        env_priority = os.getenv('PROVIDER_PRIORITY', ','.join(default_priority)).split(',')
        self.provider_priority = provider_priority or env_priority
        
        # Initialize providers
        self.providers = {}
        self._init_providers()
        
        # Usage tracking
        self.usage_stats = {provider: {"requests": 0, "tokens": 0, "cost": 0.0, "errors": 0} 
                           for provider in self.provider_priority}
        
        logger.info(f"🚀 Multi-Provider LLM initialized with priority: {self.provider_priority}")
    
    def _init_providers(self):
        """Initialize all available providers"""
        
        # AWS Bedrock
        if self.availability.bedrock and os.getenv('ENABLE_BEDROCK', 'true').lower() == 'true':
            self.providers[ProviderType.BEDROCK.value] = BedrockProvider()
        
        # Local NeMo
        if self.availability.nemo_local and os.getenv('ENABLE_LOCAL_NEMO', 'false').lower() == 'true':
            self.providers[ProviderType.NEMO_LOCAL.value] = NeMoLocalProvider()
        
        # Anthropic (existing)
        if self.availability.anthropic:
            self.providers[ProviderType.ANTHROPIC.value] = AnthropicProvider()
        
        # OpenAI (existing)
        if self.availability.openai:
            self.providers[ProviderType.OPENAI.value] = OpenAIProvider()
    
    async def initialize(self) -> Dict[str, bool]:
        """Initialize all providers and return success status"""
        results = {}
        
        for provider_name, provider in self.providers.items():
            try:
                success = provider.initialize()
                results[provider_name] = success
                if success:
                    logger.info(f"✅ {provider_name} provider ready")
                else:
                    logger.warning(f"⚠️  {provider_name} provider failed to initialize")
            except Exception as e:
                logger.error(f"❌ {provider_name} provider error: {e}")
                results[provider_name] = False
        
        return results
    
    def select_provider(self, request_type: str = "general", context: Dict[str, Any] = None) -> str:
        """Intelligent provider selection based on request type and context"""
        
        context = context or {}
        
        # Security-sensitive requests → Local NeMo (if available)
        if request_type in ["sensitive_analysis", "confidential"] and "nemo_local" in self.providers:
            return "nemo_local"
        
        # Fast dashboard requests → Bedrock (lower latency than Anthropic direct)
        if request_type in ["dashboard_insights", "quick_analysis"] and "bedrock" in self.providers:
            return "bedrock"
        
        # Complex analysis → Anthropic direct (highest quality)
        if request_type in ["incident_analysis", "complex_reasoning"] and "anthropic" in self.providers:
            return "anthropic"
        
        # Batch processing → Local NeMo (no API costs)
        if request_type in ["batch_analysis", "bulk_processing"] and "nemo_local" in self.providers:
            return "nemo_local"
        
        # Cost optimization → cheapest available
        if context.get("optimize_cost", False):
            if "nemo_local" in self.providers:
                return "nemo_local"
            elif "bedrock" in self.providers:
                return "bedrock"
        
        # Default: follow priority order
        for provider in self.provider_priority:
            if provider in self.providers:
                return provider
        
        raise Exception("No providers available")
    
    async def generate_response(self, 
                              prompt: str, 
                              request_type: str = "general",
                              context: Dict[str, Any] = None,
                              max_tokens: int = 600,
                              temperature: float = 0.0,
                              retry_on_failure: bool = True) -> ProviderResponse:
        """Generate response with intelligent provider selection and fallbacks"""
        
        # Select primary provider
        try:
            primary_provider = self.select_provider(request_type, context)
        except Exception as e:
            logger.error(f"Provider selection failed: {e}")
            raise
        
        # Try primary provider
        response = await self._try_provider(primary_provider, prompt, max_tokens, temperature)
        
        if response.success:
            self._update_usage_stats(response)
            return response
        
        # Fallback to other providers if enabled
        if retry_on_failure:
            logger.warning(f"Primary provider {primary_provider} failed: {response.error}")
            
            for fallback_provider in self.provider_priority:
                if fallback_provider != primary_provider and fallback_provider in self.providers:
                    logger.info(f"Trying fallback provider: {fallback_provider}")
                    
                    response = await self._try_provider(fallback_provider, prompt, max_tokens, temperature)
                    
                    if response.success:
                        self._update_usage_stats(response)
                        logger.info(f"✅ Fallback successful with {fallback_provider}")
                        return response
                    else:
                        logger.warning(f"Fallback provider {fallback_provider} also failed: {response.error}")
        
        # All providers failed
        self.usage_stats[response.provider.value]["errors"] += 1
        raise Exception(f"All AI providers failed. Last error: {response.error}")
    
    async def _try_provider(self, provider_name: str, prompt: str, max_tokens: int, temperature: float) -> ProviderResponse:
        """Try a specific provider"""
        try:
            provider = self.providers[provider_name]
            return await provider.generate(prompt, max_tokens, temperature)
        except Exception as e:
            return ProviderResponse(
                content="",
                provider=ProviderType(provider_name),
                model="unknown",
                tokens_used=0,
                response_time=0.0,
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    def _update_usage_stats(self, response: ProviderResponse):
        """Update usage statistics"""
        provider_name = response.provider.value
        self.usage_stats[provider_name]["requests"] += 1
        self.usage_stats[provider_name]["tokens"] += response.tokens_used
        self.usage_stats[provider_name]["cost"] += response.cost_estimate
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all providers"""
        return {
            "stats": self.usage_stats,
            "available_providers": list(self.providers.keys()),
            "provider_priority": self.provider_priority,
            "total_requests": sum(stats["requests"] for stats in self.usage_stats.values()),
            "total_cost": sum(stats["cost"] for stats in self.usage_stats.values())
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        health = {}
        
        for provider_name, provider in self.providers.items():
            try:
                health[provider_name] = {
                    "available": True,
                    "initialized": getattr(provider, 'initialized', False),
                    "model": getattr(provider, 'model', 'unknown')
                }
            except Exception as e:
                health[provider_name] = {
                    "available": False,
                    "error": str(e)
                }
        
        return {
            "providers": health,
            "priority": self.provider_priority,
            "total_available": len([p for p in health.values() if p.get("available", False)])
        }

# Backward compatibility - create enhanced version of existing classes
class SRELLMProvider(MultiProviderLLM):
    """Enhanced SRE LLM Provider with multi-provider support (backward compatible)"""
    
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", use_openai: bool = False, use_anthropic: bool = True):
        # Determine provider priority based on legacy parameters
        if use_anthropic:
            priority = ["bedrock", "anthropic", "openai"]
        elif use_openai:
            priority = ["openai", "bedrock", "anthropic"]
        else:
            priority = ["bedrock", "anthropic", "openai"]
        
        super().__init__(provider_priority=priority)
        
        self.model_name = model_name
        self.use_openai = use_openai
        self.use_anthropic = use_anthropic
        
        # Legacy compatibility
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "600"))
        self.temperature = 0.0
        self.is_initialized = False
        self.last_usage = {}
    
    def initialize(self) -> bool:
        """Initialize the multi-provider system"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(super().initialize())
            self.is_initialized = any(results.values())
            return self.is_initialized
        except Exception as e:
            logger.error(f"Failed to initialize SRE LLM Provider: {e}")
            return False
    
    def generate_response(self, prompt: str, max_length: int = None, temperature: float = None) -> str:
        """Legacy method for backward compatibility"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(super().generate_response(
                prompt=prompt,
                max_tokens=max_length or self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                request_type="general"
            ))
            
            # Update legacy usage tracking
            self.last_usage = {
                "prompt_tokens": len(prompt.split()) * 1.3,  # Approximate
                "completion_tokens": response.tokens_used,
                "total_tokens": len(prompt.split()) * 1.3 + response.tokens_used,
                "provider": response.provider.value,
                "model": response.model,
                "cost": response.cost_estimate
            }
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: {str(e)}"
    
    def health_check(self) -> Dict[str, Any]:
        """Legacy health check method"""
        health = super().health_check()
        return {
            "status": "healthy" if health["total_available"] > 0 else "unhealthy",
            "providers": health["providers"],
            "model": self.model_name,
            "initialized": self.is_initialized
        }

class NeMoEnhancedSRE:
    """Enhanced SRE operations with multi-provider AI support"""
    
    def __init__(self, llm_provider: MultiProviderLLM):
        self.llm_provider = llm_provider
        
    async def intelligent_sre_analysis(self, query: str, context: str = "") -> str:
        """Perform intelligent SRE analysis using the best available provider"""
        
        # Construct SRE-focused prompt
        sre_prompt = f"""
        {SYSTEM_SRE}
        
        Context: {context}
        
        Query: {query}
        
        Provide a focused SRE analysis with actionable insights.
        """
        
        try:
            response = await self.llm_provider.generate_response(
                prompt=sre_prompt,
                request_type="incident_analysis",
                context={"sre_context": True}
            )
            
            return f"🤖 **NeMo SRE Analysis** (via {response.provider.value}):\n{response.content}"
            
        except Exception as e:
            logger.error(f"SRE analysis failed: {e}")
            return f"❌ SRE analysis unavailable: {str(e)}"
