"""
NVIDIA NeMo LLM Provider for SRE Toolkit
This module provides LLM integration using NVIDIA NeMo framework and OpenAI API
"""

from typing import List, Dict, Any, Optional, Literal, Tuple
import logging
import os
import warnings
import time
import json
import uuid
import re
from jsonschema import validate, ValidationError
try:
    from .prompt_registry import SYSTEM_SRE, CARD_EVENT_ANALYSIS, SCHEMA_EVENT_ANALYSIS
    from .sre_context_compactor import context_compactor
except ImportError:
    # Fallback for when running as standalone
    from prompt_registry import SYSTEM_SRE, CARD_EVENT_ANALYSIS, SCHEMA_EVENT_ANALYSIS
    from sre_context_compactor import context_compactor

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

# Try to import torch, fall back gracefully if not available
try:
    import torch  # type: ignore
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    logger.warning("PyTorch not available, some features may be limited")

# Try to import OpenAI, fall back to local models if not available
try:
    from openai import OpenAI  # type: ignore
    import ssl
    import certifi
    import httpx
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not available, falling back to local models")

# Try to import Anthropic, fall back to other providers if not available
try:
    import anthropic  # type: ignore
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not available, falling back to other providers")

# Try to import transformers for local models
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM  # type: ignore
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers package not available")

class SRELLMProvider:
    """Custom LLM Provider for SRE Toolkit using OpenAI API, Anthropic Claude, or local models with quota controls"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", use_openai: bool = True, use_anthropic: bool = False):
        self.model_name = model_name
        # Ensure mutual exclusivity - Anthropic takes priority
        if use_anthropic and ANTHROPIC_AVAILABLE:
            self.use_openai = False
            self.use_anthropic = True
        else:
            self.use_openai = use_openai and OPENAI_AVAILABLE
            self.use_anthropic = False
        self.openai_client = None
        self.anthropic_client = None
        self.tokenizer = None
        self.model = None
        
        # Quota control settings
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "600"))
        self.temperature = 0.0  # Deterministic output
        self.n = 1  # Single response
        
        # Handle device initialization based on torch availability
        if TORCH_AVAILABLE:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = "cpu"  # Fallback to string representation
            logger.warning("PyTorch not available, using CPU fallback")
            
        self.is_initialized = False
        
        if self.use_anthropic:
            logger.info(f"🤖 Initializing SRE LLM Provider with Anthropic Claude model: {model_name}")
            logger.info(f"💰 Quota controls: max_tokens={self.max_tokens}, temperature={self.temperature}")
        elif self.use_openai:
            logger.info(f"🤖 Initializing SRE LLM Provider with OpenAI model: {model_name}")
            logger.info(f"💰 Quota controls: max_tokens={self.max_tokens}, temperature={self.temperature}")
        else:
            logger.info(f"🤖 Initializing SRE LLM Provider with local model: {model_name}")
            logger.info(f"🖥️  Device: {self.device}")
        
    def initialize(self) -> bool:
        """Initialize the LLM model and tokenizer"""
        try:
            if self.use_anthropic:
                # Initialize Anthropic client
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.error("❌ ANTHROPIC_API_KEY environment variable not set")
                    return False
                
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                self.is_initialized = True
                logger.info(f"✅ Anthropic LLM Provider initialized successfully with {self.model_name}")
                return True
                
            elif self.use_openai:
                # Initialize OpenAI client
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.error("❌ OPENAI_API_KEY environment variable not set")
                    return False
                
                # Configure SSL context for OpenAI client (handle Zscaler/proxy environments)
                try:
                    # Check if we're in a corporate environment with Zscaler/proxy
                    import subprocess
                    zscaler_running = False
                    try:
                        result = subprocess.run(['pgrep', '-f', 'Zscaler'], capture_output=True, text=True)
                        zscaler_running = bool(result.stdout.strip())
                    except:
                        pass
                    
                    if zscaler_running:
                        logger.info("🔒 Detected Zscaler/proxy environment - using relaxed SSL verification")
                        # In corporate environments with Zscaler, we need to relax SSL verification
                        http_client = httpx.Client(
                            verify=False,  # Disable SSL verification for Zscaler compatibility
                            timeout=30.0,
                            follow_redirects=True
                        )
                    else:
                        # Normal SSL verification for non-corporate environments
                        http_client = httpx.Client(
                            verify=certifi.where(),
                            timeout=30.0
                        )
                    
                    self.openai_client = OpenAI(
                        api_key=api_key,
                        http_client=http_client,
                        # Use configurable organization ID
                        organization=os.getenv("OPENAI_ORGANIZATION_ID", "org-KnJtwT0yz5x4vZhqNVtLPvyF")
                    )
                    self.is_initialized = True
                    logger.info(f"✅ OpenAI LLM Provider initialized successfully with {self.model_name}")
                    return True
                except Exception as ssl_error:
                    logger.warning(f"SSL context creation failed: {ssl_error}")
                    # Fallback: try without explicit SSL context
                    try:
                        self.openai_client = OpenAI(
                            api_key=api_key,
                            organization=os.getenv("OPENAI_ORGANIZATION_ID", "org-KnJtwT0yz5x4vZhqNVtLPvyF")  # Use configurable organization ID
                        )
                        self.is_initialized = True
                        logger.info(f"✅ OpenAI LLM Provider initialized successfully with {self.model_name} (fallback SSL)")
                        return True
                    except Exception as fallback_error:
                        logger.error(f"OpenAI client initialization failed: {fallback_error}")
                        return False
            else:
                # Initialize local model
                if not TRANSFORMERS_AVAILABLE:
                    logger.error("❌ Transformers not available for local models")
                    return False
                
                if not TORCH_AVAILABLE:
                    logger.error("❌ PyTorch not available for local models")
                    return False
                
                logger.info("📥 Loading tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                
                logger.info("📥 Loading model...")
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                self.model.to(self.device)
                
                # Add padding token if not present
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                    
                self.is_initialized = True
                logger.info(f"✅ Local LLM Provider initialized successfully with {self.model_name}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM Provider: {e}")
            self.is_initialized = False
            return False
    
    def generate_response(self, prompt: str, max_length: int = 300, temperature: float = 0.7) -> str:
        """Generate response from the LLM"""
        if not self.is_initialized:
            return "❌ LLM not initialized. Please call initialize() first."
        
        # Implement proper rate limiting instead of blanket delay
        if not hasattr(self, '_last_request_time'):
            self._last_request_time = 0
        
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        # Minimum 1 second between requests to prevent rate limiting
        if time_since_last < 1.0:
            sleep_time = 1.0 - time_since_last
            logger.info(f"⏳ Rate limiting: waiting {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
            
        try:
            if self.use_anthropic:
                # Use Anthropic Claude API
                response = self.anthropic_client.messages.create(
                    model=self.model_name,
                    max_tokens=min(500, max_length),
                    temperature=temperature,
                    system="You are an expert SRE (Site Reliability Engineer) assistant. Provide helpful, professional responses focused on practical solutions, best practices, and actionable recommendations for SRE operations.",
                    messages=[
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ]
                )
                
                return response.content[0].text.strip()
            elif self.use_openai:
                # Use OpenAI API
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert SRE (Site Reliability Engineer) assistant. Provide helpful, professional responses focused on practical solutions, best practices, and actionable recommendations for SRE operations."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    max_tokens=min(500, max_length),
                    temperature=temperature
                )
                
                return response.choices[0].message.content.strip()
            else:
                # Use local model
                # Prepare the prompt for SRE context
                sre_prompt = f"SRE Assistant: {prompt}\nResponse:"
                
                # Tokenize input
                inputs = self.tokenizer.encode(sre_prompt, return_tensors="pt")
                if TORCH_AVAILABLE and hasattr(self.device, 'type'):
                    inputs = inputs.to(self.device)
                
                # Generate response
                if TORCH_AVAILABLE:
                    with torch.no_grad():
                        outputs = self.model.generate(
                            inputs,
                            max_new_tokens=50,
                            temperature=temperature,
                            do_sample=True,
                            pad_token_id=self.tokenizer.eos_token_id,
                            eos_token_id=self.tokenizer.eos_token_id,
                            no_repeat_ngram_size=2
                        )
                else:
                    # Fallback without torch context manager
                    outputs = self.model.generate(
                        inputs,
                        max_new_tokens=50,
                        temperature=temperature,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        no_repeat_ngram_size=2
                    )
                
                # Decode response
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Remove the input prompt from response
                if sre_prompt in response:
                    response = response.replace(sre_prompt, "").strip()
                    
                # Clean up the response
                if response.startswith("Response:"):
                    response = response.replace("Response:", "").strip()
                    
                return response if response else "I understand your SRE query. How can I help you further?"
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        info = {
            "model_name": self.model_name,
            "provider": "Anthropic" if self.use_anthropic else ("OpenAI" if self.use_openai else "Local"),
            "is_initialized": self.is_initialized,
            "use_openai": self.use_openai,
            "use_anthropic": self.use_anthropic
        }
        
        if self.use_anthropic:
            info.update({
                "api_available": self.anthropic_client is not None,
                "model_type": "Anthropic Claude"
            })
        elif self.use_openai:
            info.update({
                "api_available": self.openai_client is not None,
                "model_type": "OpenAI GPT"
            })
        else:
            info.update({
                "device": str(self.device),
                "parameters": sum(p.numel() for p in self.model.parameters()) if self.model else 0,
                "cuda_available": torch.cuda.is_available() if TORCH_AVAILABLE else False,
                "torch_version": torch.__version__ if TORCH_AVAILABLE else "Not available",
                "torch_available": TORCH_AVAILABLE
            })
        
        return info
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the LLM provider"""
        try:
            if not self.is_initialized:
                return {"status": "not_initialized", "message": "LLM not initialized"}
            
            # Add minimal delay before health check to prevent rapid calls
            logger.info("⏳ Adding 1-second delay before health check...")
            time.sleep(1)
            
            # Test generation with a simple prompt
            test_response = self.generate_response("Hello, are you working?", max_length=50)
            
            return {
                "status": "healthy",
                "message": "LLM provider is working correctly",
                "test_response": test_response,
                "model_info": self.get_model_info(),
                "provider": "Anthropic" if self.use_anthropic else ("OpenAI" if self.use_openai else "Local")
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "provider": "Anthropic" if self.use_anthropic else ("OpenAI" if self.use_openai else "Local")
            }

    def idem(self) -> str:
        """Generate idempotency key."""
        return str(uuid.uuid4())

    def build_messages(self, card: str, user_text: str, context: str, profile: str = "json") -> List[Dict[str, str]]:
        """Build messages for LLM with system prompt, task card, and context."""
        system = SYSTEM_SRE + f"\n\nActive output profile: {profile}"
        return [
            {"role": "system", "content": system},
            {"role": "system", "name": "task_card", "content": card},
            {"role": "system", "name": "context", "content": context},
            {"role": "user", "content": user_text}
        ]

    def parse_json_first(self, text: str) -> Tuple[Dict[str, Any], str]:
        """Parse JSON from LLM output, return (json_dict, remaining_text)."""
        s = text.find("{")
        e = text.rfind("}")
        if s < 0 or e < s:
            raise ValueError("No JSON found in LLM output")
        j = json.loads(text[s:e+1])
        rest = text[e+1:].strip()
        return j, rest
    
    def parse_json_only(self, text: str) -> Tuple[Dict[str, Any], str]:
        """Parse JSON-only response, return (json, empty_string)"""
        # Remove any markdown code fences
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        # Try to parse as JSON directly
        try:
            j = json.loads(text)
            return j, ""
        except json.JSONDecodeError:
            # Fallback to finding first JSON object
            return self.parse_json_first(text)

    def run_event_analysis(self, events: List[Dict[str, Any]], window: str = "last_24h", profile: Literal["json", "chat"] = "json") -> Tuple[Dict[str, Any], str]:
        """Run event analysis using the new deterministic prompt system with quota controls."""
        try:
            # Check if we have a valid client
            if self.use_anthropic and (not hasattr(self, 'anthropic_client') or not self.anthropic_client):
                logger.warning("No Anthropic client available, using fallback analysis")
                return self._fallback_analysis(events, window)
            elif self.use_openai and (not hasattr(self, 'openai_client') or not self.openai_client):
                logger.warning("No OpenAI client available, using fallback analysis")
                return self._fallback_analysis(events, window)
            
            # Use compact context to reduce tokens
            ctx = context_compactor.compact_context(events)
            msgs = self.build_messages(CARD_EVENT_ANALYSIS, f"Analyze events window={window}.", ctx, profile=profile)
            
            # Use quota-controlled settings
            if self.use_anthropic:
                # Anthropic API call
                system_msg = next((msg["content"] for msg in msgs if msg["role"] == "system"), "")
                user_msg = next((msg["content"] for msg in msgs if msg["role"] == "user"), "")
                
                response = self.anthropic_client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_msg,
                    messages=[{"role": "user", "content": user_msg}]
                )
                content = response.content[0].text
            else:
                # OpenAI API call
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=msgs,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    n=self.n
                )
                content = response.choices[0].message.content
            
            # For JSON profile, enforce strict JSON-only response
            if profile == "json":
                payload, summary = self.parse_json_only(content)
            else:
                payload, summary = self.parse_json_first(content)
            
            # Validate against schema
            schema = json.loads(SCHEMA_EVENT_ANALYSIS)
            validate(payload, schema)
            
            # Inject idempotency keys for actions if missing (defense-in-depth)
            for action in payload.get("actions", []):
                action.setdefault("idempotency_key", self.idem())
                action.setdefault("dry_run", True)
                action.setdefault("requires_approval", action.get("requires_approval", True))
            
            return payload, summary
            
        except Exception as e:
            logger.error(f"Error in run_event_analysis: {e}")
            return self._fallback_analysis(events, window, str(e))

    def _fallback_analysis(self, events: List[Dict[str, Any]], window: str, error: str = None) -> tuple[Dict[str, Any], str]:
        """Fallback analysis when LLM is not available."""
        from collections import Counter
        
        # Count events by priority and source
        by_priority = Counter(event.get("priority", "P3") for event in events)
        by_source = Counter(event.get("source", "unknown") for event in events)
        
        # Find top events (simple heuristic)
        top_events = []
        for event in events[:5]:  # Top 5 events
            priority = event.get("priority", "P3")
            source = event.get("source", "unknown")
            summary = event.get("summary", "")[:100]
            top_events.append({
                "id": event.get("id", "unknown"),
                "priority": priority,
                "source": source,
                "why_top": f"High priority {priority} event from {source}: {summary}"
            })
        
        # Generate recommendations
        recommendations = []
        if by_priority.get("P1", 0) > 0:
            recommendations.append(f"🚨 {by_priority['P1']} P1 critical events require immediate attention")
        if by_priority.get("P2", 0) > 0:
            recommendations.append(f"⚠️ {by_priority['P2']} P2 high priority events need monitoring")
        if by_priority.get("P3", 0) > 10:
            recommendations.append(f"📋 {by_priority['P3']} P3 events - consider batch processing")
        
        # Generate actions
        actions = []
        if by_priority.get("P1", 0) > 0 or by_priority.get("P2", 0) > 0:
            actions.append({
                "provider": "slack",
                "operation": "post",
                "params": {
                    "channel": "#sre-alerts",
                    "message": f"Alert: {by_priority.get('P1', 0)} P1 and {by_priority.get('P2', 0)} P2 events need attention"
                },
                "why": "Notify SRE team of high priority events",
                "risk": "Low - informational only",
                "rollback": "Post correction message if needed",
                "requires_approval": False,
                "dry_run": True,
                "idempotency_key": self.idem()
            })
        
        payload = {
            "window": window,
            "totals": len(events),
            "by_priority": {
                "P1": by_priority.get("P1", 0),
                "P2": by_priority.get("P2", 0),
                "P3": by_priority.get("P3", 0)
            },
            "by_source": {
                "datadog": by_source.get("datadog", 0),
                "jira": by_source.get("jira", 0),
                "jams": by_source.get("jams", 0)
            },
            "clusters": [],
            "top_events": top_events,
            "recommendations": recommendations,
            "actions": actions,
            "next_data_to_fetch": ["Detailed event logs", "Performance metrics"]
        }
        
        summary = f"Fallback analysis: {len(events)} events, {by_priority.get('P1', 0)} P1, {by_priority.get('P2', 0)} P2, {by_priority.get('P3', 0)} P3"
        if error:
            summary += f" (LLM error: {error})"
        
        return payload, summary

class NeMoEnhancedSRE:
    """NeMo-enhanced SRE operations with intelligent analysis"""
    
    def __init__(self, llm_provider: SRELLMProvider):
        self.llm_provider = llm_provider
        
    def intelligent_sre_analysis(self, query: str, events_context: str = "") -> str:
        """Use NeMo LLM for intelligent SRE analysis"""
        try:
            # Add minimal delay to prevent rapid analysis calls
            logger.info("⏳ Adding 1-second delay before SRE analysis...")
            time.sleep(1)
            
            # Create enhanced prompt with SRE context
            enhanced_prompt = f"SRE Assistant: {query}\nResponse:"
            
            response = self.llm_provider.generate_response(
                enhanced_prompt, 
                max_length=300, 
                temperature=0.7
            )
            
            return f"🤖 **NeMo SRE Analysis**:\n{response}"
            
        except Exception as e:
            logger.error(f"Error in intelligent SRE analysis: {e}")
            return f"❌ Error in SRE analysis: {str(e)}"
    
    def generate_incident_response(self, incident_details: str) -> str:
        """Generate intelligent incident response using NeMo LLM"""
        try:
            # Add minimal delay to prevent rapid incident response calls
            logger.info("⏳ Adding 1-second delay before incident response generation...")
            time.sleep(1)
            
            prompt = f"""
            As an SRE expert, analyze this incident and provide a structured response:
            
            Incident Details: {incident_details}
            
            Please provide:
            1. Immediate actions to take
            2. Root cause analysis approach
            3. Prevention strategies
            4. Communication plan
            
            Format your response clearly and professionally.
            """
            
            response = self.llm_provider.generate_response(prompt, max_length=400)
            return f"🚨 **NeMo Incident Response**:\n{response}"
            
        except Exception as e:
            return f"❌ Error generating incident response: {str(e)}"
    
    def suggest_optimizations(self, system_metrics: str) -> str:
        """Suggest system optimizations based on metrics"""
        try:
            # Add minimal delay to prevent rapid optimization calls
            logger.info("⏳ Adding 1-second delay before optimization suggestions...")
            time.sleep(1)
            
            prompt = f"""
            As an SRE expert, analyze these system metrics and suggest optimizations:
            
            System Metrics: {system_metrics}
            
            Please provide:
            1. Performance bottlenecks identified
            2. Optimization recommendations
            3. Monitoring improvements
            4. Capacity planning suggestions
            
            Focus on actionable, measurable improvements.
            """
            
            response = self.llm_provider.generate_response(prompt, max_length=350)
            return f"⚡ **NeMo Optimization Suggestions**:\n{response}"
            
        except Exception as e:
            return f"❌ Error generating optimization suggestions: {str(e)}"
