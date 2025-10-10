"""
Simple Local LLM Provider for Corporate Environments
This provides a basic local AI capability without requiring model downloads
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SimpleResponse:
    content: str
    provider: str = "simple_local"
    model: str = "rule-based"
    tokens_used: int = 0
    response_time: float = 0.0
    cost_estimate: float = 0.0
    success: bool = True
    error: Optional[str] = None

class SimpleLocalLLM:
    """Simple rule-based local LLM that works without internet"""
    
    def __init__(self):
        self.initialized = False
        self.model_name = "simple-local-llm"
        
        # SRE-specific response templates
        self.sre_responses = {
            "incident_analysis": [
                "Based on the incident details, this appears to be a {priority} priority issue.",
                "Recommended immediate actions: 1) Verify system status 2) Check logs 3) Notify team",
                "Root cause analysis suggests this may be related to {source} infrastructure.",
                "Next steps: Monitor metrics, update status page, document resolution"
            ],
            "dashboard_insights": [
                "Current system status shows {event_count} active events.",
                "Priority breakdown: P1: {p1_count}, P2: {p2_count}, P3: {p3_count}",
                "Recent trends indicate {trend} in system stability.",
                "Recommendations: Focus on {focus_area} for improved reliability"
            ],
            "general": [
                "Site Reliability Engineering focuses on system stability and incident response.",
                "Key SRE principles include monitoring, alerting, and rapid incident resolution.",
                "Best practices include runbooks, post-mortems, and continuous improvement.",
                "Tools like monitoring dashboards and alerting systems are essential for SRE teams."
            ]
        }
    
    def initialize(self) -> bool:
        """Initialize the simple local LLM"""
        try:
            logger.info("🔄 Initializing Simple Local LLM...")
            self.initialized = True
            logger.info("✅ Simple Local LLM initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Simple Local LLM: {e}")
            return False
    
    async def generate(self, prompt: str, max_tokens: int = 600, temperature: float = 0.0, 
                      request_type: str = "general", context: Dict[str, Any] = None) -> SimpleResponse:
        """Generate a response using rule-based logic"""
        
        if not self.initialized:
            return SimpleResponse(
                content="Simple Local LLM not initialized",
                success=False,
                error="Not initialized"
            )
        
        start_time = time.time()
        
        try:
            # Analyze the prompt to determine response type
            prompt_lower = prompt.lower()
            
            # Determine response category
            if any(word in prompt_lower for word in ['incident', 'alert', 'error', 'failure', 'down']):
                response_type = "incident_analysis"
            elif any(word in prompt_lower for word in ['dashboard', 'summary', 'overview', 'status']):
                response_type = "dashboard_insights"
            else:
                response_type = "general"
            
            # Generate contextual response
            content = self._generate_contextual_response(prompt, response_type, context or {})
            
            # Limit to max_tokens (approximate)
            words = content.split()
            if len(words) > max_tokens:
                content = " ".join(words[:max_tokens]) + "..."
            
            response_time = time.time() - start_time
            
            return SimpleResponse(
                content=content,
                provider="simple_local",
                model=self.model_name,
                tokens_used=len(content.split()),
                response_time=response_time,
                cost_estimate=0.0,  # No cost for local processing
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in simple local generation: {e}")
            return SimpleResponse(
                content="",
                provider="simple_local",
                model=self.model_name,
                tokens_used=0,
                response_time=time.time() - start_time,
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    def _generate_contextual_response(self, prompt: str, response_type: str, context: Dict[str, Any]) -> str:
        """Generate a contextual response based on the prompt and context"""
        
        # Extract key information from context
        event_count = context.get('event_count', 0)
        p1_count = context.get('p1_count', 0)
        p2_count = context.get('p2_count', 0)
        p3_count = context.get('p3_count', 0)
        priority = context.get('priority', 'P3')
        source = context.get('source', 'unknown')
        
        # Build response based on type
        if response_type == "incident_analysis":
            response = f"""
**SRE Incident Analysis**

Based on the incident details provided, this appears to be a {priority} priority issue requiring immediate attention.

**Immediate Actions:**
1. Verify system status and check critical metrics
2. Review recent deployments and configuration changes
3. Check logs for error patterns and root cause indicators
4. Notify relevant team members and stakeholders

**Analysis:**
- Priority Level: {priority}
- Source: {source}
- Impact: Assessing system stability and user experience

**Next Steps:**
- Monitor system recovery and stability
- Document incident timeline and resolution steps
- Schedule post-incident review for process improvement
- Update monitoring and alerting based on lessons learned

**Prevention:**
- Review monitoring coverage for early detection
- Update runbooks with this scenario
- Consider additional redundancy or failover mechanisms
"""
        
        elif response_type == "dashboard_insights":
            response = f"""
**SRE Dashboard Insights**

**Current Status:**
- Active Events: {event_count}
- Priority Breakdown: P1: {p1_count}, P2: {p2_count}, P3: {p3_count}

**System Health:**
- Overall system stability appears {'good' if p1_count == 0 else 'requires attention'}
- Focus areas: {'Critical issues need immediate resolution' if p1_count > 0 else 'Monitor trends and optimize performance'}

**Recommendations:**
- {'Address P1 issues immediately' if p1_count > 0 else 'Continue monitoring and optimization'}
- Review alerting thresholds and notification processes
- Update documentation and runbooks as needed
- Schedule regular system health reviews

**Trends:**
- Monitor for patterns in event sources and timing
- Track resolution times and team response efficiency
- Identify opportunities for proactive improvements
"""
        
        else:
            response = f"""
**SRE Guidance**

Site Reliability Engineering focuses on maintaining system stability and rapid incident response.

**Key Principles:**
- Proactive monitoring and alerting
- Rapid incident detection and response
- Post-incident analysis and learning
- Continuous improvement of system reliability

**Best Practices:**
- Implement comprehensive monitoring across all system components
- Create clear escalation procedures and runbooks
- Conduct regular post-mortems to learn from incidents
- Focus on automation to reduce manual toil

**Tools and Processes:**
- Monitoring dashboards for real-time visibility
- Alerting systems for immediate notification
- Incident management for tracking and resolution
- Documentation for knowledge sharing and training

**Current Context:**
- Active events: {event_count}
- Priority focus: {'Critical issues' if p1_count > 0 else 'System optimization'}
"""
        
        return response.strip()

# Global instance
simple_local_llm = SimpleLocalLLM()
