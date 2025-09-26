#!/usr/bin/env python3
"""
Minimal NeMo Agent Toolkit Backend
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import os
import re
import operator
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# VPN/Corporate network SSL configuration
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure SSL context for VPN environments
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Add plugins to path
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
plugins_path = project_root / "plugins"
middleware_path = project_root / "middleware"

sys.path.insert(0, str(plugins_path))
sys.path.insert(0, str(middleware_path))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NeMo Agent Toolkit", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
try:
    from rate_limit import rate_limit_middleware
    app.middleware("http")(rate_limit_middleware)
    logger.info("✅ Rate limiting middleware added")
except ImportError as e:
    logger.warning(f"Rate limiting middleware not available: {e}")

# Import quota control modules
try:
    
    from llm_cache import llm_cache
    from llm_circuit import llm_circuit_breaker, CircuitBreakerOpenError
    from fallback_summaries import fallback_summarizer
    from llm_meter import llm_usage_meter
    from sre_context_compactor import context_compactor
    QUOTA_CONTROLS_AVAILABLE = True
    logger.info("✅ Quota control modules loaded")
except ImportError as e:
    QUOTA_CONTROLS_AVAILABLE = False
    logger.warning(f"Quota control modules not available: {e}")

# Response caching to reduce API calls (legacy)
ENHANCED_SUMMARY_CACHE = {}
CACHE_DURATION = 300  # 5 minutes cache

# Rate limiting to prevent excessive polling (legacy)
RATE_LIMIT_CACHE = {}
RATE_LIMIT_WINDOW = 10  # 10 seconds
RATE_LIMIT_MAX_REQUESTS = 3  # Max 3 requests per 10 seconds per IP

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    messages: List[Dict[str, Any]]

class ChatResponse(BaseModel):
    response: str
    status: str = "success"

class SafeCalculator:
    """Safe calculator implementation without eval()."""
    
    def calculate(self, expression: str) -> str:
        """Calculate the result of an expression."""
        try:
            if not expression or not expression.strip():
                raise ValueError("Empty expression provided")
            
            result = self._safe_evaluate(expression)
            
            # Format result appropriately
            if result == int(result):
                return f"The result is: {int(result)}"
            else:
                return f"The result is: {result}"
            
        except ZeroDivisionError:
            return "Error: Division by zero is not allowed"
        except ValueError as e:
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error: Could not calculate '{expression}' - {str(e)}"
    
    def _safe_evaluate(self, expression: str) -> float:
        """Safely evaluate a mathematical expression without using eval()."""
        # Replace common text with operators first
        expression = expression.replace('plus', '+').replace('minus', '-')
        expression = expression.replace('times', '*').replace('multiplied by', '*')
        expression = expression.replace('divided by', '/').replace('over', '/')
        
        # Remove whitespace
        expression = expression.replace(' ', '')
        
        # Validate expression contains only allowed characters
        if not re.match(r'^[0-9+\-*/().,]+$', expression):
            raise ValueError("Expression contains invalid characters")
        
        # Validate parentheses are balanced
        if expression.count('(') != expression.count(')'):
            raise ValueError("Unbalanced parentheses")
        
        # Validate expression doesn't start or end with operators (except minus for negative numbers)
        if expression and expression[0] in '+*/':
            raise ValueError("Expression cannot start with operator")
        if expression and expression[-1] in '+-*/':
            raise ValueError("Expression cannot end with operator")
        
        # Handle negative numbers at the beginning
        if expression.startswith('-'):
            expression = '0' + expression
        
        # Replace consecutive operators (like --) with proper handling
        expression = re.sub(r'--', '+', expression)
        expression = re.sub(r'\+-', '-', expression)
        expression = re.sub(r'-\+', '-', expression)
        expression = re.sub(r'\+\+', '+', expression)
        
        # Split into tokens
        tokens = self._tokenize(expression)
        
        # Convert to postfix notation and evaluate
        return self._evaluate_postfix(self._infix_to_postfix(tokens))
    
    def _tokenize(self, expression: str) -> list:
        """Tokenize the expression into numbers and operators."""
        # Pattern to match numbers (including decimals) and operators
        pattern = r'(\d+\.?\d*|[+\-*/()])'
        tokens = re.findall(pattern, expression)
        
        # Convert number tokens to floats
        result = []
        for token in tokens:
            if token in '+-*/()':
                result.append(token)
            else:
                try:
                    result.append(float(token))
                except ValueError:
                    raise ValueError(f"Invalid number: {token}")
        
        return result
    
    def _infix_to_postfix(self, tokens: list) -> list:
        """Convert infix notation to postfix (RPN) notation."""
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
        output = []
        operators = []
        
        for token in tokens:
            if isinstance(token, (int, float)):
                output.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                if operators:
                    operators.pop()  # Remove '('
                else:
                    raise ValueError("Unbalanced parentheses")
            elif token in precedence:
                while (operators and operators[-1] != '(' and 
                       precedence.get(operators[-1], 0) >= precedence[token]):
                    output.append(operators.pop())
                operators.append(token)
        
        while operators:
            if operators[-1] == '(':
                raise ValueError("Unbalanced parentheses")
            output.append(operators.pop())
        
        return output
    
    def _evaluate_postfix(self, tokens: list) -> float:
        """Evaluate postfix notation expression."""
        operations = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv
        }
        
        stack = []
        
        for token in tokens:
            if isinstance(token, (int, float)):
                stack.append(token)
            elif token in operations:
                if len(stack) < 2:
                    raise ValueError("Invalid expression: insufficient operands")
                
                b = stack.pop()
                a = stack.pop()
                
                if token == '/' and b == 0:
                    raise ZeroDivisionError("Division by zero")
                
                result = operations[token](a, b)
                stack.append(result)
            else:
                raise ValueError(f"Invalid token: {token}")
        
        if len(stack) != 1:
            raise ValueError("Invalid expression: too many operands")
        
        return stack[0]

# Initialize calculator
calculator = SafeCalculator()

# Enhanced SRE tools are not needed since we have direct API integrations
ENHANCED_TOOLS_AVAILABLE = False

# Initialize NeMo LLM Provider (OpenAI by default, Anthropic as alternative)
try:
    from nemo_llm_provider import SRELLMProvider, NeMoEnhancedSRE
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "config"))
    from openai_config import get_openai_config, validate_openai_config, get_recommended_model
    
    # Check for Anthropic configuration first
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    use_anthropic = bool(anthropic_api_key)
    
    if use_anthropic:
        # Use Anthropic Claude
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        nemo_llm = SRELLMProvider(model_name, use_openai=False, use_anthropic=True)
        logger.info(f"NeMo LLM Provider configured for Anthropic Claude model: {model_name}")
    else:
        # Get OpenAI configuration
        openai_config = get_openai_config()
        is_valid, message = validate_openai_config()
        
        if is_valid:
            # Use OpenAI with configured model
            model_name = openai_config["model"]
            nemo_llm = SRELLMProvider(model_name, use_openai=True, use_anthropic=False)
            logger.info(f"NeMo LLM Provider configured for OpenAI model: {model_name}")
        else:
            # Fall back to local model
            logger.warning(f"OpenAI not configured: {message}. Falling back to local model.")
            nemo_llm = SRELLMProvider("microsoft/DialoGPT-medium", use_openai=False, use_anthropic=False)
    
    nemo_enhanced_sre = None
    NEMO_LLM_AVAILABLE = False
    logger.info("NeMo LLM Provider imported successfully")
except ImportError as e:
    logger.warning(f"NeMo LLM Provider not available: {e}")
    nemo_llm = None
    nemo_enhanced_sre = None
    NEMO_LLM_AVAILABLE = False

@app.on_event("startup")
async def startup_event():
    """Initialize NeMo LLM on startup"""
    global nemo_llm, nemo_enhanced_sre, NEMO_LLM_AVAILABLE
    
    if nemo_llm:
        try:
            success = nemo_llm.initialize()
            if success:
                nemo_enhanced_sre = NeMoEnhancedSRE(nemo_llm)
                NEMO_LLM_AVAILABLE = True
                logger.info("✅ NeMo LLM Provider initialized successfully")
            else:
                logger.error("❌ Failed to initialize NeMo LLM Provider")
                NEMO_LLM_AVAILABLE = False
        except Exception as e:
            logger.error(f"❌ Error initializing NeMo LLM Provider: {e}")
            NEMO_LLM_AVAILABLE = False

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "NeMo Agent Toolkit API is running", "status": "healthy"}

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "nemo-agent-toolkit"}


@app.get("/api/v1/bestegg/events")
async def get_bestegg_events():
    """Proxy endpoint to fetch BestEgg SRE events"""
    try:
        import requests
        
        url = "https://sre-api-service-ext.bestegg.com/event_interactions/events"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'NeMo-Agent-Toolkit/1.0'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch BestEgg events: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests."""
    try:
        message = request.message.lower().strip()
        
        # Check for NeMo LLM requests
        if message.startswith("nemo:") or "llm" in message or "ai" in message:
            if NEMO_LLM_AVAILABLE and nemo_enhanced_sre:
                try:
                    # Extract the actual prompt
                    prompt = message.replace("nemo:", "").replace("llm", "").replace("ai", "").strip()
                    
                    # Get SRE context if available
                    sre_context = ""
                    if ENHANCED_TOOLS_AVAILABLE:
                        try:
                            tool = create_sre_tool("enhanced")
                            events = tool.fetch_events()
                            if events:
                                sre_context = f"Current SRE Status: {len(events)} events. Recent: {events[0].summary[:100]}..." if events else ""
                        except:
                            pass
                    
                    # Generate intelligent response using NeMo LLM
                    llm_response = nemo_enhanced_sre.intelligent_sre_analysis(prompt, sre_context)
                    
                    return ChatResponse(response=llm_response)
                except Exception as e:
                    logger.error(f"Error in NeMo LLM processing: {e}")
                    return ChatResponse(response=f"❌ Error processing NeMo LLM request: {str(e)}")
            else:
                return ChatResponse(response="❌ NeMo LLM Provider is not available. Please ensure the LLM is properly initialized.")
        
        # Check for single SRE event requests (e.g., "show event evt_001", "get event evt_002")
        if any(phrase in message for phrase in ['show event', 'get event', 'event details', 'details for event']):
            try:
                # Extract event ID from the message
                import re
                event_id_match = re.search(r'evt_\d+', request.message)
                if event_id_match:
                    event_id = event_id_match.group()
                    # Get single event directly using the internal function
                    event_data = await get_sre_event(event_id)
                    
                    if not event_data:
                        return ChatResponse(response=f"Event {event_id} not found.")
                    
                    # Format the response
                    response_text = f"Event {event_data['id']}:\n  Summary: {event_data['summary']}\n  Slack ID: {event_data['slack_id']}\n  Status: {event_data.get('status', 'unknown')}"
                    
                    return ChatResponse(response=response_text)
                else:
                    return ChatResponse(response="Please specify an event ID (e.g., 'show event evt_001')")
            except Exception as e:
                logger.error(f"Error fetching single SRE event: {e}")
                return ChatResponse(response=f"Sorry, I couldn't fetch that event right now. Error: {str(e)}")
        
        # Check for enhanced SRE summary requests
        elif any(phrase in message for phrase in ['enhanced summary', 'sre summary', 'priority breakdown', 'event breakdown', 'dashboard', 'sre dashboard']):
            if ENHANCED_TOOLS_AVAILABLE:
                try:
                    tool = create_sre_tool("enhanced")
                    result = tool.get_events_summary_enhanced()
                    return ChatResponse(response=result)
                except Exception as e:
                    logger.error(f"Error getting enhanced SRE summary: {e}")
                    return ChatResponse(response=f"Sorry, I couldn't get the enhanced summary right now. Error: {str(e)}")
            else:
                return ChatResponse(response="Enhanced SRE tools are not available. Please use basic SRE events commands.")
        
        # Check for priority filtering requests
        elif any(phrase in message for phrase in ['p1 events', 'critical events', 'p2 events', 'high priority', 'p3 events', 'medium priority']):
            if ENHANCED_TOOLS_AVAILABLE:
                try:
                    # Extract priority from message
                    priority = "P3"  # Default
                    if any(word in message for word in ['p1', 'critical']):
                        priority = "P1"
                    elif any(word in message for word in ['p2', 'high']):
                        priority = "P2"
                    
                    tool = create_sre_tool("enhanced")
                    events = tool.get_events_by_priority(priority)
                    
                    if not events:
                        return ChatResponse(response=f"No {priority} events found.")
                    
                    # Create beautiful priority-specific formatting
                    priority_info = {
                        "P1": {"emoji": "🚨", "title": "CRITICAL", "color": "RED", "action": "🚨 IMMEDIATE ACTION REQUIRED"},
                        "P2": {"emoji": "⚠️", "title": "HIGH", "color": "ORANGE", "action": "⚠️  MONITOR CLOSELY"},
                        "P3": {"emoji": "ℹ️", "title": "MEDIUM", "color": "BLUE", "action": "📋 STANDARD MONITORING"}
                    }
                    
                    info = priority_info.get(priority, {"emoji": "⚪", "title": "UNKNOWN", "color": "GRAY", "action": "📋 REVIEW"})
                    
                    summary_lines = [
                        f"{info['emoji']} {priority} EVENTS ({info['title']})",
                        f"📊 {len(events)} events | {info['action']}",
                        ""
                    ]
                    
                    # Show events with compact formatting
                    for i, event in enumerate(events[:5], 1):
                        summary = event.summary[:40] + "..." if len(event.summary) > 40 else event.summary
                        summary_lines.append(f"{i}. {info['emoji']} {summary}")
                    
                    if len(events) > 5:
                        summary_lines.append(f"... and {len(events) - 5} more {priority} events")
                    
                    # Add footer with actions
                    summary_lines.extend([
                        "",
                        "💡 Try: 'create jira ticket'"
                    ])
                    
                    return ChatResponse(response="\n".join(summary_lines))
                except Exception as e:
                    logger.error(f"Error getting events by priority: {e}")
                    return ChatResponse(response=f"Sorry, I couldn't filter events by priority right now. Error: {str(e)}")
            else:
                return ChatResponse(response="Enhanced SRE tools are not available. Please use basic SRE events commands.")
        
        # Check for source filtering requests
        elif any(phrase in message for phrase in ['jira events', 'datadog events', 'jams events', 'jira tickets', 'datadog alerts']):
            if ENHANCED_TOOLS_AVAILABLE:
                try:
                    # Extract source from message
                    source = "jira"  # Default
                    if any(word in message for word in ['datadog']):
                        source = "datadog"
                    elif any(word in message for word in ['jams']):
                        source = "jams"
                    
                    tool = create_sre_tool("enhanced")
                    events = tool.get_events_by_source(source)
                    
                    if not events:
                        return ChatResponse(response=f"No {source} events found.")
                    
                    # Create beautiful source-specific formatting
                    source_info = {
                        "jira": {"emoji": "🎫", "title": "JIRA TICKETS", "description": "📝 ACTIVE TICKETS & INCIDENTS"},
                        "datadog": {"emoji": "📈", "title": "DATADOG ALERTS", "description": "📊 SYSTEM MONITORING & METRICS"},
                        "jams": {"emoji": "⚙️", "title": "JAMS JOBS", "description": "🔄 SCHEDULED JOB FAILURES"}
                    }
                    
                    info = source_info.get(source, {"emoji": "📋", "title": "UNKNOWN", "description": "📋 GENERAL EVENTS"})
                    
                    summary_lines = [
                        f"{info['emoji']} {info['title']}",
                        f"📊 {len(events)} events | {info['description']}",
                        ""
                    ]
                    
                    # Show events with compact formatting
                    for i, event in enumerate(events[:5], 1):
                        priority_emoji = {"P1": "🚨", "P2": "⚠️", "P3": "ℹ️"}.get(event.priority, "⚪")
                        summary = event.summary[:40] + "..." if len(event.summary) > 40 else event.summary
                        summary_lines.append(f"{i}. {priority_emoji} {summary}")
                    
                    if len(events) > 5:
                        summary_lines.append(f"... and {len(events) - 5} more {source} events")
                    
                    # Add footer with actions
                    summary_lines.extend([
                        "",
                        "💡 Try: 'create jira ticket'"
                    ])
                    
                    return ChatResponse(response="\n".join(summary_lines))
                except Exception as e:
                    logger.error(f"Error getting events by source: {e}")
                    return ChatResponse(response=f"Sorry, I couldn't filter events by source right now. Error: {str(e)}")
            else:
                return ChatResponse(response="Enhanced SRE tools are not available. Please use basic SRE events commands.")
        
        # Check for general SRE commands (catch-all for SRE-related queries)
        elif any(phrase in message.lower() for phrase in ['sre', 'incident', 'alert', 'monitoring', 'status']):
            if ENHANCED_TOOLS_AVAILABLE:
                try:
                    tool = create_sre_tool("enhanced")
                    result = tool.answer_event_question(message)
                    return ChatResponse(response=result)
                except Exception as e:
                    logger.error(f"Error processing SRE command: {e}")
                    return ChatResponse(response=f"Sorry, I couldn't process that SRE command. Error: {str(e)}")
            else:
                return ChatResponse(response="Enhanced SRE tools are not available.")
        
        # Check for intelligent event queries (prioritize real SRE data)
        elif any(phrase in message.lower() for phrase in ['how many', 'what events', 'show events', 'list events', 'search', 'find', 'analytics', 'events', 'ticket']):
            if ENHANCED_TOOLS_AVAILABLE:
                try:
                    tool = create_sre_tool("enhanced")
                    result = tool.answer_event_question(message)
                    return ChatResponse(response=result)
                except Exception as e:
                    logger.error(f"Error processing event query: {e}")
                    return ChatResponse(response=f"Sorry, I couldn't process that event query. Error: {str(e)}")
            else:
                return ChatResponse(response="Enhanced SRE tools are not available for event queries.")
        
        # Check for JIRA ticket creation requests
        elif any(phrase in message for phrase in ['create jira', 'create ticket', 'jira ticket', 'new ticket']):
            if ENHANCED_TOOLS_AVAILABLE:
                try:
                    # Extract ticket details from message
                    summary = "SRE Incident Ticket"
                    description = "Created via SRE chat interface"
                    priority = "Medium"

                    # Try to extract more details from the message
                    if "critical" in message or "urgent" in message:
                        priority = "High"
                    elif "low" in message:
                        priority = "Low"

                    tool = create_sre_tool("enhanced")
                    result = tool.create_jira_ticket(summary, description, priority)
                    return ChatResponse(response=result)
                except Exception as e:
                    logger.error(f"Error creating JIRA ticket: {e}")
                    return ChatResponse(response=f"Sorry, I couldn't create a JIRA ticket right now. Error: {str(e)}")
            else:
                return ChatResponse(response="Enhanced SRE tools are not available. JIRA integration is not enabled.")
        
        # Check for Datadog query requests
        elif any(phrase in message for phrase in ['datadog query', 'query datadog', 'datadog metrics', 'system metrics']):
            if ENHANCED_TOOLS_AVAILABLE:
                try:
                    # Default query for system metrics
                    query = "system.cpu.user{*}"
                    if "memory" in message:
                        query = "system.memory.used{*}"
                    elif "disk" in message:
                        query = "system.disk.used{*}"
                    
                    tool = create_sre_tool("enhanced")
                    result = tool.query_datadog_metrics(query)
                    return ChatResponse(response=result)
                except Exception as e:
                    logger.error(f"Error querying Datadog: {e}")
                    return ChatResponse(response=f"Sorry, I couldn't query Datadog right now. Error: {str(e)}")
            else:
                return ChatResponse(response="Enhanced SRE tools are not available. Datadog integration is not enabled.")
        
        # Check for Slack alert requests
        elif any(phrase in message for phrase in ['send alert', 'slack alert', 'notify team', 'send notification']):
            if ENHANCED_TOOLS_AVAILABLE:
                try:
                    # Extract alert message and priority
                    alert_message = "SRE Alert from chat interface"
                    priority = "P3"
                    
                    if "critical" in message or "urgent" in message:
                        priority = "P1"
                    elif "high" in message:
                        priority = "P2"
                    
                    tool = create_sre_tool("enhanced")
                    result = tool.send_slack_alert(alert_message, priority=priority)
                    return ChatResponse(response=result)
                except Exception as e:
                    logger.error(f"Error sending Slack alert: {e}")
                    return ChatResponse(response=f"Sorry, I couldn't send a Slack alert right now. Error: {str(e)}")
            else:
                return ChatResponse(response="Enhanced SRE tools are not available. Slack integration is not enabled.")
        
        # Check for SRE events requests (all events)
        elif any(word in message for word in ['sre events', 'sre event', 'events', 'incidents', 'alerts', 'show events', 'get events', 'list events']):
            try:
                # Get SRE events directly using the internal function
                events_data = await get_sre_events()
                
                if not events_data:
                    return ChatResponse(response="No SRE events found.")
                
                # Format the response
                summary_lines = [f"Found {len(events_data)} SRE events:"]
                for event in events_data:
                    summary_lines.append(f"  • {event['id']}: {event['summary']} (Slack: {event['slack_id']})")
                
                return ChatResponse(response="\n".join(summary_lines))
            except Exception as e:
                logger.error(f"Error fetching SRE events: {e}")
                return ChatResponse(response=f"Sorry, I couldn't fetch SRE events right now. Error: {str(e)}")
        
        # Check for calculator requests
        elif any(word in message for word in ['calculate', 'compute', 'math', '+', '-', '*', '/', 'plus', 'minus', 'times', 'divided']):
            # Extract mathematical expression
            # Simple extraction - look for numbers and operators
            math_pattern = r'[\d+\-*/().,\s]+'
            math_matches = re.findall(math_pattern, request.message)
            if math_matches:
                expression = ''.join(math_matches).strip()
                result = calculator.calculate(expression)
                return ChatResponse(response=result)
        
        # Default response for other queries
        
        # Build response message
        response_parts = [
            "🚨 **SRE Command Center** - Real-time monitoring of 82+ events",
            "",
            "📊 **Quick SRE Commands**:",
            "• 'enhanced summary' - Get comprehensive dashboard",
            "• 'P1 events' - View critical issues", 
            "• 'analytics' - Get detailed analytics",
            "• 'search [term]' - Find specific events",
            "• 'how many [type]' - Count events",
            "",
            "🔧 **SRE Actions**:",
            "• 'create jira ticket' - Create incident tickets",
            "• 'query datadog' - Get system metrics",
            "• 'send slack alert' - Notify team"
        ]
        
        # Add NeMo LLM commands if available
        if NEMO_LLM_AVAILABLE:
            response_parts.extend([
                "",
                "🤖 **NeMo AI Assistant**:",
                "• 'nemo: [question]' - Ask AI for SRE guidance",
                "• 'llm: [query]' - Get intelligent analysis",
                "• 'ai: [request]' - AI-powered recommendations"
            ])
        
        response_parts.extend([
            "",
            "🧮 **Other**: Math calculations, single event lookup",
            "",
            "What SRE operation would you like to perform?"
        ])
        
        return ChatResponse(response="\n".join(response_parts))
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tools")
async def get_tools():
    """Get available tools."""
    tools = [
            {
                "name": "calculator",
                "description": "Perform mathematical calculations",
                "example": "Calculate 2 + 3"
        },
        {
            "name": "sre_events",
            "description": "Fetch SRE events and interactions",
            "example": "Get SRE events"
        }
    ]
    
    if ENHANCED_TOOLS_AVAILABLE:
        tools.extend([
            {
                "name": "enhanced_sre_summary",
                "description": "Get enhanced SRE events summary with priority breakdown",
                "example": "Get enhanced SRE summary"
            },
            {
                "name": "jira_ticket",
                "description": "Create JIRA tickets for incident tracking",
                "example": "Create JIRA ticket for database issue"
            },
            {
                "name": "datadog_metrics",
                "description": "Query Datadog metrics and logs",
                "example": "Query Datadog for CPU metrics"
            },
            {
                "name": "slack_alert",
                "description": "Send Slack alerts and notifications",
                "example": "Send Slack alert for critical issue"
            }
        ])
    
    # Add NeMo LLM tools if available
    if NEMO_LLM_AVAILABLE:
        tools.extend([
            {
                "name": "nemo_llm",
                "description": "Generate intelligent responses using NVIDIA NeMo LLM",
                "example": "nemo: Analyze the current SRE situation"
            },
            {
                "name": "nemo_sre_analysis",
                "description": "Perform intelligent SRE analysis with AI assistance",
                "example": "llm: What should I do about this database issue?"
            },
            {
                "name": "nemo_incident_response",
                "description": "Generate AI-powered incident response recommendations",
                "example": "ai: Help me respond to this P1 incident"
            }
        ])
    
        return {"tools": tools}


@app.get("/event_interactions/events")
async def get_sre_events():
    """Get SRE events from real SRE API."""
    logger.info("🔍 Starting SRE events fetch...")
    try:
        # Use synchronous requests in thread pool for better compatibility
        import requests
        import asyncio
        
        def fetch_sre_data():
            logger.info("📡 Attempting to fetch from real SRE API...")
            sre_api_url = "https://sre-api-service-ext.bestegg.com/event_interactions/events"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'NeMo-Agent-Toolkit/1.0'
            }
            
            logger.info(f"🌐 Making request to: {sre_api_url}")
            response = requests.get(sre_api_url, headers=headers, timeout=15, verify=False)
            logger.info(f"📊 SRE API response status: {response.status_code}")
            return response
        
        # Execute in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, fetch_sre_data)
        
        if response.status_code == 200:
            data = response.json()
            events_raw = data.get("result", [])
            
            # Transform to match expected format
            events_data = []
            for event in events_raw:
                # Extract priority from subject or use P3 as default
                subject = event.get("subject", "")
                priority = "P3"  # default
                if "[P1]" in subject or "Critical" in subject or "critical" in subject.lower():
                    priority = "P1"
                elif "[P2]" in subject or "High" in subject or "high" in subject.lower():
                    priority = "P2"
                elif "Triggered" in subject or "Alert" in subject:
                    priority = "P2"  # Most alerts are P2 unless specified
                
                events_data.append({
                    "id": event.get("event_id"),
                    "event_id": event.get("event_id"),
                    "slack_id": event.get("slack_channel_id", ""),
                    "summary": event.get("subject", ""),
                    "subject": event.get("subject", ""),
                    "status": event.get("current_status", "Open"),
                    "current_status": event.get("current_status", "Open"),
                    "priority": priority,
                    "source": event.get("event_source", "sre_api"),
                    "event_source": event.get("event_source", "sre_api"),
                    "timestamp": event.get("create_ts"),
                    "create_ts": event.get("create_ts")
                })
            
            logger.info(f"📊 Fetched {len(events_data)} real SRE events from API")
            return {"result": events_data}
        else:
            logger.warning(f"SRE API returned {response.status_code}, using empty result")
            return {"result": [], "error": f"SRE API returned {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"SRE API request error: {e}")
        return {"result": [], "error": f"SRE API connection failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error fetching SRE events: {e}")
        return {"result": [], "error": str(e)}

@app.get("/event_interactions/events/{event_id}")
async def get_sre_event(event_id: str):
    """Get a specific SRE event by ID from real SRE API."""
    try:
        if ENHANCED_TOOLS_AVAILABLE:
            # Use real SRE API data
            tool = create_sre_tool("enhanced")
            events = tool.fetch_events()
            
            # Find the specific event by ID
            for event in events:
                if event.id == event_id:
                    return {
                        "id": event.id,
                        "identifier": event.id,
                        "slack_id": event.slack_id,
                        "summary": event.summary,
                        "status": event.status,
                        "priority": event.priority,
                        "source": event.source,
                        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                        "created_at": event.timestamp.isoformat() if event.timestamp else None,
                        "updated_at": event.timestamp.isoformat() if event.timestamp else None,
                        "details": {
                            "severity": event.priority.lower(),
                            "affected_services": [event.source] if event.source else [],
                            "assigned_to": "sre-team"
                        }
                    }
            
            # Event not found
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        else:
            # Fallback to mock data
            mock_event = {
                "id": event_id,
                "identifier": event_id,
                "slack_id": "C1234567890",
                "summary": f"Event {event_id} details",
                "status": "active",
                "priority": "P2",
                "source": "datadog",
                "timestamp": "2024-01-15T12:00:00Z",
                "created_at": "2024-01-15T12:00:00Z",
                "updated_at": "2024-01-15T12:00:00Z",
                "details": {
                    "severity": "medium",
                    "affected_services": ["api", "database"],
                    "assigned_to": "sre-team"
                }
            }
            return mock_event
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SRE event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mock endpoints for enterprise workflow testing

# Enhanced SRE Tools API Endpoints
@app.get("/api/v1/sre/enhanced-summary")
async def get_enhanced_sre_summary_endpoint(profile: str = "json", request: Request = None):
    """Get enhanced SRE events summary with quota controls and caching."""
    if not ENHANCED_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced SRE tools not available")
    
    try:
        # Get events data
        tool = create_sre_tool("enhanced")
        events = tool.fetch_events()
        
        # Convert SREEvent objects to dict format
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "source": event.source,
                "priority": event.priority,
                "status": event.status,
                "summary": event.summary,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None
            })
        
        # Check if quota controls are available
        if QUOTA_CONTROLS_AVAILABLE:
            # Generate context hash for caching
            context_hash = context_compactor.get_context_hash(events_data)
            card_version = "event_analysis_v1"  # Version of the prompt card
            # Check budget limits first
            budget_exceeded, budget_reason = llm_usage_meter.is_budget_exceeded()
            if budget_exceeded:
                logger.warning(f"💰 Budget exceeded: {budget_reason}")
                # Use fallback summarizer
                result = fallback_summarizer.generate_enhanced_summary(events_data)
                return result
            
            # Check circuit breaker
            if llm_circuit_breaker.is_open():
                logger.warning("🔌 Circuit breaker is OPEN - using fallback")
                # Try cache first, then fallback
                cached_result = llm_cache.get(card_version, context_hash)
                if cached_result:
                    logger.info("📋 Returning cached result (circuit breaker open)")
                    return cached_result
                else:
                    result = fallback_summarizer.generate_enhanced_summary(events_data)
                    return result
            
            # Use cache with singleflight
            def llm_analysis():
                """LLM analysis function for singleflight"""
                try:
                    # Check if we should skip LLM based on policy
                    if _should_skip_llm(events_data):
                        logger.info("📊 Policy: skipping LLM for low-priority events")
                        return fallback_summarizer.generate_enhanced_summary(events_data)
                    
                    # Execute LLM analysis with circuit breaker protection
                    def llm_call():
                        if not nemo_llm:
                            raise Exception("LLM provider not available")
                        
                        payload, summary = nemo_llm.run_event_analysis(events_data, profile=profile)
                        
                        # Record usage if available
                        if hasattr(nemo_llm, 'last_usage'):
                            usage = nemo_llm.last_usage
                            llm_usage_meter.record_usage(
                                usage.get('prompt_tokens', 0),
                                usage.get('completion_tokens', 0),
                                usage.get('cost_usd', 0.0)
                            )
                        
                        return payload
                    
                    return llm_circuit_breaker.call(llm_call)
                    
                except CircuitBreakerOpenError:
                    logger.warning("🔌 Circuit breaker opened during analysis")
                    return fallback_summarizer.generate_enhanced_summary(events_data)
                except Exception as e:
                    logger.error(f"LLM analysis failed: {e}")
                    return fallback_summarizer.generate_enhanced_summary(events_data)
            
            # Execute with singleflight caching
            result = llm_cache.singleflight(card_version, context_hash, llm_analysis)
            
        else:
            # Fallback to legacy implementation
            logger.warning("Quota controls not available, using legacy implementation")
            result = _legacy_enhanced_summary(events_data, profile)
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced summary error: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced summary failed: {str(e)}")

def _should_skip_llm(events_data: List[Dict[str, Any]]) -> bool:
    """Determine if LLM should be skipped based on policy"""
    # Count priorities
    p1_count = sum(1 for e in events_data if e.get('priority') == 'P1')
    p2_count = sum(1 for e in events_data if e.get('priority') == 'P2')
    p3_count = sum(1 for e in events_data if e.get('priority') == 'P3')
    
    # Skip LLM if no P1s and <= 2 P2s
    if p1_count == 0 and p2_count <= 2:
        return True
    
    # Skip LLM if all events are P3
    if p1_count == 0 and p2_count == 0 and p3_count > 0:
        return True
    
    return False

@app.get("/api/v1/sre/usage")
async def get_llm_usage():
    """Get LLM usage statistics and budget status"""
    if not QUOTA_CONTROLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Usage tracking not available")
    
    try:
        usage_summary = llm_usage_meter.get_usage_summary()
        circuit_state = llm_circuit_breaker.get_state()
        
        return {
            "usage": usage_summary,
            "circuit_breaker": circuit_state,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Usage endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Usage tracking failed: {str(e)}")

def _legacy_enhanced_summary(events_data: List[Dict[str, Any]], profile: str) -> Dict[str, Any]:
    """Legacy enhanced summary implementation"""
    # Check cache first
    cache_key = f"enhanced_summary_{profile}"
    current_time = time.time()
    
    if cache_key in ENHANCED_SUMMARY_CACHE:
        cached_data, cache_time = ENHANCED_SUMMARY_CACHE[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            logger.info(f"📋 Returning cached enhanced summary (age: {int(current_time - cache_time)}s)")
            return cached_data
    
    try:
        tool = create_sre_tool("enhanced")
        events = tool.fetch_events()
        
        # Convert SREEvent objects to dict format for analysis
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "source": event.source,
                "priority": event.priority,
                "status": event.status,
                "summary": event.summary,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None
            })
        
        # Use the new deterministic AI analysis
        if not nemo_llm:
            logger.warning("LLM provider not available, using fallback analysis")
            # Fallback analysis without LLM
            from collections import Counter
            
            by_priority = Counter(event["priority"] for event in events_data)
            by_source = Counter(event["source"] for event in events_data)
            
            # Find top events (simple heuristic)
            top_events = []
            for event in events_data[:5]:  # Top 5 events
                priority = event.get("priority", "P3")
                source = event.get("source", "unknown")
                summary_text = event.get("summary", "")[:100]
                top_events.append({
                    "id": event.get("id", "unknown"),
                    "priority": priority,
                    "source": source,
                    "why_top": f"High priority {priority} event from {source}: {summary_text}"
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
                    "idempotency_key": "fallback-" + str(len(events_data))
                })
            
            payload = {
                "window": "last_24h",
                "totals": len(events_data),
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
            
            summary = f"Fallback analysis: {len(events_data)} events, {by_priority.get('P1', 0)} P1, {by_priority.get('P2', 0)} P2, {by_priority.get('P3', 0)} P3"
        else:
            payload, summary = nemo_llm.run_event_analysis(events_data, window="last_24h", profile=profile)
        
        result = {"json": payload, "summary": summary if profile == "chat" else ""}
        
        # Cache the result
        ENHANCED_SUMMARY_CACHE[cache_key] = (result, current_time)
        logger.info(f"💾 Cached enhanced summary for {CACHE_DURATION}s")
        
        return result
    except Exception as e:
        logger.error(f"Error getting enhanced SRE summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sre/events/priority/{priority}")
async def get_events_by_priority(priority: str):
    """Get SRE events filtered by priority (P1, P2, P3)."""
    if not ENHANCED_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced SRE tools not available")
    
    try:
        tool = create_sre_tool("enhanced")
        events = tool.get_events_by_priority(priority.upper())
        
        # Convert to dict format for JSON response
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "slack_id": event.slack_id,
                "summary": event.summary,
                "priority": event.priority,
                "status": event.status,
                "source": event.source
            })
        
        return {"events": events_data, "count": len(events_data), "priority": priority.upper()}
    except Exception as e:
        logger.error(f"Error getting events by priority: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sre/events/source/{source}")
async def get_events_by_source(source: str):
    """Get SRE events filtered by source (jira, datadog, jams)."""
    if not ENHANCED_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced SRE tools not available")
    
    try:
        tool = create_sre_tool("enhanced")
        events = tool.get_events_by_source(source.lower())
        
        # Convert to dict format for JSON response
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "slack_id": event.slack_id,
                "summary": event.summary,
                "priority": event.priority,
                "status": event.status,
                "source": event.source
            })
        
        return {"events": events_data, "count": len(events_data), "source": source.lower()}
    except Exception as e:
        logger.error(f"Error getting events by source: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/sre/jira/create")
async def create_jira_ticket_endpoint(request: dict):
    """Create a new JIRA ticket."""
    if not ENHANCED_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced SRE tools not available")
    
    try:
        summary = request.get("summary", "")
        description = request.get("description", "")
        priority = request.get("priority", "Medium")
        
        if not summary:
            raise HTTPException(status_code=400, detail="Summary is required")
        
        tool = create_sre_tool("enhanced")
        result = tool.create_jira_ticket(summary, description, priority)
        return {"result": result, "status": "success"}
    except Exception as e:
        logger.error(f"Error creating JIRA ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/sre/datadog/query")
async def query_datadog_metrics_endpoint(request: dict):
    """Query Datadog metrics."""
    if not ENHANCED_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced SRE tools not available")
    
    try:
        query = request.get("query", "")
        time_range = request.get("time_range", "1h")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        tool = create_sre_tool("enhanced")
        result = tool.query_datadog_metrics(query)
        return {"result": result, "status": "success"}
    except Exception as e:
        logger.error(f"Error querying Datadog metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/sre/slack/alert")
async def send_slack_alert_endpoint(request: dict):
    """Send Slack alert."""
    if not ENHANCED_TOOLS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced SRE tools not available")
    
    try:
        message = request.get("message", "")
        priority = request.get("priority", "P3")
        channel = request.get("channel", "#sre-alerts")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        tool = create_sre_tool("enhanced")
        result = tool.send_slack_alert(message, priority=priority)
        return {"result": result, "status": "success"}
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# NeMo LLM API Endpoints
@app.get("/api/v1/nemo/info")
async def get_nemo_info():
    """Get NeMo LLM information and status."""
    if not NEMO_LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="NeMo LLM Provider not available")
    
    try:
        info = nemo_llm.get_model_info()
        return {"info": info, "status": "success"}
    except Exception as e:
        logger.error(f"Error getting NeMo info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/nemo/health")
async def nemo_health_check():
    """Perform health check on NeMo LLM provider."""
    if not NEMO_LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="NeMo LLM Provider not available")
    
    try:
        health = nemo_llm.health_check()
        return {"health": health, "status": "success"}
    except Exception as e:
        logger.error(f"Error in NeMo health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/nemo/generate")
async def nemo_generate(request: dict):
    """Generate response using NeMo LLM."""
    if not NEMO_LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="NeMo LLM Provider not available")
    
    try:
        prompt = request.get("prompt", "")
        max_length = request.get("max_length", 300)
        temperature = request.get("temperature", 0.7)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        response = nemo_llm.generate_response(prompt, max_length, temperature)
        return {"response": response, "status": "success"}
    except Exception as e:
        logger.error(f"Error generating NeMo response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/nemo/sre-analysis")
async def nemo_sre_analysis(request: dict):
    """Perform intelligent SRE analysis using NeMo LLM."""
    if not NEMO_LLM_AVAILABLE or not nemo_enhanced_sre:
        raise HTTPException(status_code=503, detail="NeMo Enhanced SRE not available")
    
    try:
        query = request.get("query", "")
        events_context = request.get("events_context", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        response = nemo_enhanced_sre.intelligent_sre_analysis(query, events_context)
        return {"response": response, "status": "success"}
    except Exception as e:
        logger.error(f"Error in NeMo SRE analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze")
async def analyze_event(request: dict):
    """Analyze a specific event using AI."""
    try:
        event = request.get("event", {})
        if not event:
            raise HTTPException(status_code=400, detail="No event data provided")
        
        # Use the NeMo LLM for analysis if available
        if NEMO_LLM_AVAILABLE and nemo_enhanced_sre:
            try:
                # Create a comprehensive prompt for event analysis
                event_details = f"""
                Event Analysis Request:
                - ID: {event.get('event_id', event.get('id', 'Unknown'))}
                - Summary: {event.get('subject', event.get('summary', 'No summary'))}
                - Priority: {event.get('priority', 'Unknown')}
                - Source: {event.get('event_source', event.get('source', 'Unknown'))}
                - Status: {event.get('current_status', event.get('status', 'Unknown'))}
                - Monitor: {event.get('monitor_name', 'Unknown')}
                - Title: {event.get('original_title', 'Unknown')}
                - Timestamp: {event.get('create_ts', event.get('timestamp', 'Unknown'))}
                
                Provide SRE analysis with root cause, impact, and recommended actions.
                """
                
                # Use the enhanced SRE analysis
                analysis_result = nemo_enhanced_sre.intelligent_sre_analysis(
                    "Analyze this SRE event for root cause and recommended actions",
                    event_details
                )
                
                return {
                    "success": True,
                    "analysis": analysis_result,
                    "event_id": event.get('event_id', event.get('id')),
                    "timestamp": time.time(),
                    "ai_powered": True
                }
                
            except Exception as llm_error:
                logger.warning(f"AI analysis failed, using fallback: {llm_error}")
                # Fallback to structured analysis
                priority = event.get('priority', 'Unknown')
                source = event.get('event_source', event.get('source', 'Unknown'))
                status = event.get('current_status', event.get('status', 'Unknown'))
                
                fallback_analysis = f"""
📊 **Event Analysis Summary**

**Event Details:**
• Priority: {priority}
• Source: {source} 
• Status: {status}
• Monitor: {event.get('monitor_name', 'Unknown')}

**Quick Assessment:**
• This is a {priority} priority event from {source}
• Current status: {status}
• Requires manual review for detailed analysis

**Recommended Actions:**
1. Check source system for additional context
2. Review related events in the same timeframe
3. Escalate if priority is P1 or P2
4. Document resolution steps for future reference

*Note: AI analysis temporarily unavailable*
                """
                
                return {
                    "success": True,
                    "analysis": fallback_analysis,
                    "event_id": event.get('event_id', event.get('id')),
                    "timestamp": time.time(),
                    "ai_powered": False
                }
        else:
            # Structured fallback when AI is not available
            priority = event.get('priority', 'Unknown')
            source = event.get('event_source', event.get('source', 'Unknown'))
            status = event.get('current_status', event.get('status', 'Unknown'))
            
            fallback_analysis = f"""
📋 **Manual Event Analysis**

**Event Overview:**
• Summary: {event.get('subject', event.get('summary', 'No summary available'))}
• Priority: {priority}
• Source: {source}
• Status: {status}

**Analysis Notes:**
• Event requires manual investigation
• Check source system for additional details
• Review monitoring dashboards for context
• Consider impact on dependent systems

**Next Steps:**
1. Investigate root cause in {source}
2. Check for related incidents
3. Update status as investigation progresses
4. Document findings and resolution

*Connect AI for enhanced analysis capabilities*
            """
            
            return {
                "success": True,
                "analysis": fallback_analysis,
                "event_id": event.get('event_id', event.get('id')),
                "timestamp": time.time(),
                "ai_powered": False
            }
            
    except Exception as e:
        logger.error(f"Error analyzing event: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/v1/nemo/analyze-event")
async def nemo_analyze_event(request: dict):
    """Enhanced event analysis using NeMo AI with context awareness."""
    if not NEMO_LLM_AVAILABLE:
        return {"analysis": "AI analysis unavailable - NeMo not connected", "ai_powered": False}
    
    try:
        event = request.get("event", {})
        context_events = request.get("context_events", [])
        
        if not event:
            raise HTTPException(status_code=400, detail="Event data required")
        
        # Build context from related events
        context_info = ""
        if context_events:
            context_info = f"\nRelated Events Context:\n"
            for ctx_event in context_events[:3]:  # Limit context to avoid token overflow
                context_info += f"- {ctx_event.get('priority', 'Unknown')}: {ctx_event.get('subject', 'No summary')[:100]}...\n"
        
        # Enhanced analysis prompt
        analysis_query = f"""
        Analyze this SRE event with pattern recognition and correlation:
        
        Primary Event:
        - Priority: {event.get('priority', 'Unknown')}
        - Summary: {event.get('subject', event.get('summary', 'No summary'))}
        - Source: {event.get('event_source', event.get('source', 'Unknown'))}
        - Monitor: {event.get('monitor_name', 'Unknown')}
        {context_info}
        
        Provide structured analysis focusing on actionable insights.
        """
        
        # Use enhanced SRE analysis
        if nemo_enhanced_sre:
            analysis_result = nemo_enhanced_sre.intelligent_sre_analysis(
                analysis_query,
                f"SRE Event Analysis for {event.get('event_id', 'unknown')}"
            )
        else:
            analysis_result = "Enhanced analysis temporarily unavailable"
        
        return {
            "analysis": analysis_result,
            "event_id": event.get('event_id', event.get('id')),
            "ai_powered": True,
            "context_used": len(context_events) > 0,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Enhanced event analysis error: {e}")
        return {
            "analysis": f"Analysis error: {str(e)}",
            "ai_powered": False,
            "timestamp": time.time()
        }

@app.post("/api/v1/nemo/dashboard-insights")
async def generate_dashboard_insights(request: dict):
    """Generate AI-powered dashboard insights based on current events and trends."""
    try:
        events = request.get("events", [])
        historical_data = request.get("historical_data", {})
        
        if not events:
            return {
                "insights": [],
                "ai_powered": False,
                "message": "No events data provided"
            }
        
        # Analyze current event patterns
        total_events = len(events)
        critical_count = len([e for e in events if e.get('priority') == 'P1'])
        high_count = len([e for e in events if e.get('priority') == 'P2'])
        medium_count = len([e for e in events if e.get('priority') == 'P3'])
        
        # Group by source for analysis
        source_breakdown = {}
        for event in events:
            source = event.get('event_source', event.get('source', 'unknown'))
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
        
        # Generate insights based on patterns
        insights = []
        
        if NEMO_LLM_AVAILABLE and nemo_enhanced_sre:
            try:
                # Create comprehensive analysis prompt
                analysis_prompt = f"""
                Analyze the current SRE dashboard data and provide 3-4 key insights:
                
                Current Status:
                - Total Events: {total_events}
                - Critical (P1): {critical_count}
                - High (P2): {high_count}  
                - Medium (P3): {medium_count}
                
                Source Breakdown: {source_breakdown}
                
                Provide insights in this JSON format:
                [
                  {{
                    "type": "trend|alert|recommendation|status",
                    "title": "Brief title",
                    "message": "Clear, actionable insight",
                    "severity": "info|warning|critical",
                    "icon": "📈|🚨|💡|✅"
                  }}
                ]
                
                Focus on actionable insights, trends, and recommendations.
                """
                
                ai_response = nemo_enhanced_sre.intelligent_sre_analysis(
                    "Generate dashboard insights",
                    analysis_prompt
                )
                
                # Try to extract JSON from AI response
                import json
                import re
                
                # Look for JSON array in the response
                json_match = re.search(r'\[(.*?)\]', ai_response, re.DOTALL)
                if json_match:
                    try:
                        ai_insights = json.loads(json_match.group(0))
                        insights.extend(ai_insights)
                    except json.JSONDecodeError:
                        pass
                
                # If AI parsing failed, create structured insights from AI text
                if not insights and ai_response:
                    insights.append({
                        "type": "status",
                        "title": "AI Analysis",
                        "message": ai_response.replace("🤖 **NeMo SRE Analysis**:\n", "")[:200] + "...",
                        "severity": "info",
                        "icon": "🤖"
                    })
                        
            except Exception as ai_error:
                logger.warning(f"AI insights generation failed: {ai_error}")
        
        # Generate fallback insights based on data patterns
        if not insights:
            # Critical events insight
            if critical_count > 0:
                insights.append({
                    "type": "alert",
                    "title": "Critical Events Active",
                    "message": f"{critical_count} P1 incidents require immediate attention. Check database and API services.",
                    "severity": "critical",
                    "icon": "🚨"
                })
            
            # System health insight  
            health_score = max(10, 100 - (critical_count * 20) - (high_count * 10) - (medium_count * 5))
            if health_score < 70:
                insights.append({
                    "type": "status",
                    "title": "System Health Degraded",
                    "message": f"Current health score: {health_score}%. Multiple incidents affecting system stability.",
                    "severity": "warning",
                    "icon": "⚠️"
                })
            else:
                insights.append({
                    "type": "status", 
                    "title": "System Health Good",
                    "message": f"Health score: {health_score}%. {total_events} events being monitored across all services.",
                    "severity": "info",
                    "icon": "✅"
                })
            
            # Source analysis insight
            top_source = max(source_breakdown.items(), key=lambda x: x[1]) if source_breakdown else None
            if top_source and top_source[1] > total_events * 0.4:
                insights.append({
                    "type": "trend",
                    "title": f"{top_source[0].title()} High Activity",
                    "message": f"{top_source[1]} events from {top_source[0]} ({int(top_source[1]/total_events*100)}% of total). Monitor for patterns.",
                    "severity": "info",
                    "icon": "📈"
                })
            
            # Recommendation based on event distribution
            if critical_count > 5:
                insights.append({
                    "type": "recommendation",
                    "title": "Scale Response Team",
                    "message": f"With {critical_count} P1 incidents, consider activating additional on-call engineers.",
                    "severity": "warning", 
                    "icon": "💡"
                })
            elif total_events > 100:
                insights.append({
                    "type": "recommendation",
                    "title": "Review Alert Thresholds",
                    "message": f"{total_events} active events may indicate overly sensitive monitoring. Consider tuning thresholds.",
                    "severity": "info",
                    "icon": "💡"
                })
        
        # Limit to 4 insights max
        insights = insights[:4]
        
        return {
            "insights": insights,
            "ai_powered": NEMO_LLM_AVAILABLE,
            "timestamp": time.time(),
            "events_analyzed": total_events
        }
        
    except Exception as e:
        logger.error(f"Dashboard insights generation error: {e}")
        return {
            "insights": [
                {
                    "type": "status",
                    "title": "Insights Unavailable", 
                    "message": "Unable to generate dashboard insights at this time. Check system status.",
                    "severity": "info",
                    "icon": "ℹ️"
                }
            ],
            "ai_powered": False,
            "timestamp": time.time()
        }

@app.post("/api/v1/nemo/predictive-analysis")
async def predictive_incident_analysis(request: dict):
    """AI-powered predictive incident detection with pattern recognition and anomaly detection."""
    try:
        events = request.get("events", [])
        historical_data = request.get("historical_data", {})
        time_window_hours = request.get("time_window_hours", 24)
        
        if not events:
            return {
                "predictions": [],
                "anomalies": [],
                "risk_score": 0,
                "ai_powered": False,
                "message": "No events data provided for analysis"
            }
        
        # Basic pattern analysis
        total_events = len(events)
        critical_count = len([e for e in events if e.get('priority') == 'P1'])
        high_count = len([e for e in events if e.get('priority') == 'P2'])
        
        # Source pattern analysis
        source_patterns = {}
        priority_trends = {'P1': 0, 'P2': 0, 'P3': 0}
        
        for event in events:
            source = event.get('event_source', event.get('source', 'unknown'))
            priority = event.get('priority', 'P3')
            
            if source not in source_patterns:
                source_patterns[source] = {'total': 0, 'critical': 0, 'high': 0}
            
            source_patterns[source]['total'] += 1
            if priority == 'P1':
                source_patterns[source]['critical'] += 1
                priority_trends['P1'] += 1
            elif priority == 'P2':
                source_patterns[source]['high'] += 1
                priority_trends['P2'] += 1
            else:
                priority_trends['P3'] += 1
        
        predictions = []
        anomalies = []
        risk_score = 0
        
        if NEMO_LLM_AVAILABLE and nemo_enhanced_sre:
            try:
                # AI-powered predictive analysis
                analysis_prompt = f"""
                Analyze the following SRE event patterns and predict potential incidents:
                
                Current State:
                - Total Events: {total_events}
                - Critical (P1): {critical_count} 
                - High (P2): {high_count}
                - Time Window: {time_window_hours} hours
                
                Source Breakdown: {source_patterns}
                Priority Trends: {priority_trends}
                
                Based on these patterns, provide predictions in JSON format:
                {{
                  "predictions": [
                    {{
                      "type": "incident_prediction|capacity_warning|service_degradation",
                      "title": "Brief prediction title",
                      "description": "Detailed prediction with reasoning",
                      "confidence": 0.85,
                      "severity": "low|medium|high|critical",
                      "estimated_time": "2-4 hours|1-2 days|next week",
                      "affected_services": ["service1", "service2"],
                      "recommended_actions": ["action1", "action2"]
                    }}
                  ],
                  "anomalies": [
                    {{
                      "type": "frequency_spike|unusual_pattern|correlation_break",
                      "source": "datadog|jira|sre_api",
                      "description": "What's unusual",
                      "severity": "low|medium|high",
                      "confidence": 0.75
                    }}
                  ],
                  "risk_score": 65
                }}
                
                Focus on actionable predictions with high confidence scores.
                """
                
                ai_response = nemo_enhanced_sre.intelligent_sre_analysis(
                    "Predictive incident analysis",
                    analysis_prompt
                )
                
                import json
                import re
                
                # Try to extract JSON from AI response
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    try:
                        ai_analysis = json.loads(json_match.group(0))
                        predictions = ai_analysis.get("predictions", [])
                        anomalies = ai_analysis.get("anomalies", [])
                        risk_score = ai_analysis.get("risk_score", 0)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse AI prediction JSON")
                
            except Exception as ai_error:
                logger.warning(f"AI predictive analysis failed: {ai_error}")
        
        # Fallback rule-based predictions if AI unavailable or failed
        if not predictions:
            # Pattern-based incident prediction
            if critical_count >= 3:
                predictions.append({
                    "type": "incident_prediction",
                    "title": "Cascading Incident Risk",
                    "description": f"Multiple P1 incidents ({critical_count}) detected. Pattern suggests potential cascading failures in dependent services.",
                    "confidence": min(0.9, 0.6 + (critical_count * 0.1)),
                    "severity": "critical" if critical_count >= 5 else "high",
                    "estimated_time": "30 minutes - 2 hours",
                    "affected_services": list(source_patterns.keys()),
                    "recommended_actions": [
                        "Activate incident commander",
                        "Check service dependencies", 
                        "Prepare rollback plans"
                    ]
                })
            
            # Source-based predictions
            for source, data in source_patterns.items():
                if data['total'] > total_events * 0.5:  # One source > 50% of events
                    predictions.append({
                        "type": "service_degradation",
                        "title": f"{source.title()} Service Stress",
                        "description": f"{source} showing high event volume ({data['total']} events, {int(data['total']/total_events*100)}%). May indicate service degradation or monitoring sensitivity.",
                        "confidence": 0.7,
                        "severity": "medium" if data['critical'] == 0 else "high",
                        "estimated_time": "1-4 hours",
                        "affected_services": [source],
                        "recommended_actions": [
                            f"Review {source} service health",
                            "Check monitoring thresholds",
                            "Validate service capacity"
                        ]
                    })
            
            # Volume-based predictions
            if total_events > 200:
                predictions.append({
                    "type": "capacity_warning", 
                    "title": "High Event Volume Alert",
                    "description": f"Unusually high event volume ({total_events} events). This may indicate system-wide stress or alert storm conditions.",
                    "confidence": 0.65,
                    "severity": "medium",
                    "estimated_time": "2-6 hours",
                    "affected_services": ["monitoring", "alerting"],
                    "recommended_actions": [
                        "Review alert thresholds",
                        "Check for alert storms", 
                        "Validate monitoring health"
                    ]
                })
        
        # Generate anomalies if not provided by AI
        if not anomalies:
            for source, data in source_patterns.items():
                critical_ratio = data['critical'] / max(data['total'], 1)
                if critical_ratio > 0.3:  # >30% critical events from one source
                    anomalies.append({
                        "type": "frequency_spike",
                        "source": source,
                        "description": f"High critical event ratio from {source}: {int(critical_ratio*100)}% of events are P1",
                        "severity": "high" if critical_ratio > 0.5 else "medium",
                        "confidence": 0.8
                    })
        
        # Calculate risk score if not provided by AI
        if not risk_score:
            base_risk = min(50, total_events * 0.1)  # Base risk from volume
            critical_risk = critical_count * 15  # 15 points per P1
            high_risk = high_count * 5  # 5 points per P2
            concentration_risk = max(0, (max(source_patterns.values(), key=lambda x: x['total'])['total'] / total_events - 0.3) * 100) if source_patterns else 0
            
            risk_score = min(100, int(base_risk + critical_risk + high_risk + concentration_risk))
        
        # Limit predictions and anomalies
        predictions = predictions[:5]
        anomalies = anomalies[:3]
        
        return {
            "predictions": predictions,
            "anomalies": anomalies, 
            "risk_score": risk_score,
            "confidence_level": "high" if risk_score > 70 else "medium" if risk_score > 40 else "low",
            "ai_powered": NEMO_LLM_AVAILABLE,
            "timestamp": time.time(),
            "events_analyzed": total_events,
            "time_window_hours": time_window_hours
        }
        
    except Exception as e:
        logger.error(f"Predictive analysis error: {e}")
        return {
            "predictions": [
                {
                    "type": "incident_prediction",
                    "title": "Predictive Analysis Unavailable",
                    "description": "Unable to perform predictive analysis at this time. Manual monitoring recommended.",
                    "confidence": 0.0,
                    "severity": "low", 
                    "estimated_time": "unknown",
                    "affected_services": [],
                    "recommended_actions": ["Check system health manually"]
                }
            ],
            "anomalies": [],
            "risk_score": 0,
            "ai_powered": False,
            "timestamp": time.time()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
