"""
Unified SRE Tools Plugin
Combines simple and enhanced functionality with configurable modes
"""

import requests
import logging
import json
import os
import sys
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

logger = logging.getLogger(__name__)

class SREMode(Enum):
    """SRE Tool operation modes"""
    SIMPLE = "simple"
    ENHANCED = "enhanced"

@dataclass
class SREEvent:
    """Unified SRE event data structure"""
    id: str
    slack_id: str
    summary: str
    status: str = "Open"
    priority: str = "P3"
    source: str = "unknown"
    timestamp: Optional[datetime] = None
    
    def to_simple(self) -> Dict[str, str]:
        """Convert to simple format for backward compatibility"""
        return {
            "id": self.id,
            "slack_id": self.slack_id,
            "summary": self.summary
        }

@dataclass
class JIRATicket:
    """JIRA ticket data structure"""
    key: str
    summary: str
    status: str
    assignee: str
    priority: str
    created: str

@dataclass
class DatadogMetric:
    """Datadog metric data structure"""
    name: str
    value: float
    timestamp: str
    tags: Dict[str, str]

class UnifiedSRETool:
    """Unified SRE tool that combines simple and enhanced functionality"""
    
    def __init__(self, mode: SREMode = SREMode.ENHANCED, base_url: str = ""):
        self.mode = mode
        self.base_url = base_url.rstrip('/') if base_url else config.SRE_API_BASE_URL.rstrip('/')
        self.endpoint = "/event_interactions/events"
        self.headers = {"Content-Type": "application/json"}
        
        # Add BestEgg API authentication
        self._setup_authentication()
        
        # Initialize enhanced tools only if in enhanced mode
        if self.mode == SREMode.ENHANCED:
            self._init_enhanced_tools()
    
    def _setup_authentication(self):
        """Setup authentication headers for BestEgg SRE API"""
        if config.SRE_API_KEY:
            self.headers['X-API-Key'] = config.SRE_API_KEY
            logger.info("🔑 Using API Key authentication for BestEgg SRE API")
        elif config.SRE_API_TOKEN:
            self.headers['Authorization'] = f'Bearer {config.SRE_API_TOKEN}'
            logger.info("🎫 Using Bearer Token authentication for BestEgg SRE API")
        else:
            logger.warning("⚠️ No authentication configured for BestEgg SRE API")
        
        # Add BestEgg environment header if configured
        if config.BESTEGG_ENV:
            self.headers['X-BestEgg-Env'] = config.BESTEGG_ENV
            logger.info(f"🌍 BestEgg Environment: {config.BESTEGG_ENV}")
        
        # Add WAF ACL header if configured
        if config.BESTEGG_WAF_ACL:
            self.headers['X-WAF-ACL'] = config.BESTEGG_WAF_ACL
    
    def _init_enhanced_tools(self):
        """Initialize enhanced tools (JIRA, Slack, etc.)"""
        self.jira_tool = JIRATool()
        self.slack_tool = SlackTool()
        self.datadog_tool = DatadogTool()
        self.jams_tool = JAMSTool()
    
    def fetch_events(self) -> List[SREEvent]:
        """
        Fetch SRE events - behavior depends on mode
        Simple mode: Basic fetching like original simple tool
        Enhanced mode: Advanced fetching with priority scoring
        """
        try:
            url = f"{self.base_url}{self.endpoint}"
            logger.info(f"🔍 Fetching SRE events from: {url} (mode: {self.mode.value})")
            
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            
            response_data = response.json()
            events_data = response_data.get('result', [])
            logger.info(f"📊 Received {len(events_data)} events")
            
            events = []
            for event in events_data:
                if self.mode == SREMode.SIMPLE:
                    mapped_event = self._map_event_simple(event)
                else:
                    mapped_event = self._map_event_enhanced(event)
                    if mapped_event:
                        mapped_event = self._enhance_event_priority(mapped_event)
                
                if mapped_event:
                    events.append(mapped_event)
            
            # Sort by priority in enhanced mode
            if self.mode == SREMode.ENHANCED:
                events.sort(key=lambda x: (x.priority == "P1", x.priority == "P2", x.priority == "P3"), reverse=True)
            
            logger.info(f"✅ Processed {len(events)} events")
            return events
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to fetch SRE events: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching SRE events: {e}")
            return []

    def get_events_by_priority(self, priority: str) -> List[SREEvent]:
        """Get events filtered by priority (P1, P2, P3)."""
        all_events = self.fetch_events()
        return [event for event in all_events if event.priority == priority.upper()]

    def get_events_by_source(self, source: str) -> List[SREEvent]:
        """Get events filtered by source (jira, datadog, jams)."""
        all_events = self.fetch_events()
        return [event for event in all_events if event.source.lower() == source.lower()]

    def _map_event_simple(self, event: Dict[str, Any]) -> Optional[SREEvent]:
        """Map event to simple structure (backward compatibility)"""
        try:
            return SREEvent(
                id=str(event.get('event_id', event.get('id', ''))),
                slack_id=str(event.get('slack_channel_id', event.get('slack_id', ''))),
                summary=str(event.get('subject', event.get('summary', '')))
            )
        except Exception as e:
            logger.warning(f"Failed to map simple event: {e}")
            return None
    
    def _map_event_enhanced(self, event: Dict[str, Any]) -> Optional[SREEvent]:
        """Map event to enhanced structure"""
        try:
            # Extract priority from subject or metadata
            priority = 'P3'  # default
            subject = event.get('subject', '')
            if '[P1]' in subject:
                priority = 'P1'
            elif '[P2]' in subject:
                priority = 'P2'
            elif '[P3]' in subject:
                priority = 'P3'
            elif 'event_metadata' in event and event['event_metadata']:
                metadata = event['event_metadata']
                if 'alert_priority' in metadata:
                    priority = metadata['alert_priority']
            
            # Extract timestamp
            timestamp = None
            if 'create_ts' in event:
                from datetime import datetime
                try:
                    timestamp = datetime.fromisoformat(event['create_ts'].replace('Z', '+00:00'))
                except:
                    pass
            
            return SREEvent(
                id=str(event.get('event_id', event.get('id', ''))),
                slack_id=str(event.get('slack_channel_id', event.get('slack_id', ''))),
                summary=str(event.get('subject', event.get('summary', ''))),
                status=str(event.get('current_status', event.get('status', 'Open'))),
                priority=priority,
                source=str(event.get('event_source', event.get('source', 'unknown'))),
                timestamp=timestamp
            )
        except Exception as e:
            logger.warning(f"Failed to map enhanced event: {e}")
            return None
    
    def _enhance_event_priority(self, event: SREEvent) -> SREEvent:
        """Enhance event with priority scoring (enhanced mode only)"""
        if self.mode != SREMode.ENHANCED:
            return event
            
        # Priority scoring logic
        summary_lower = event.summary.lower()
        
        if any(keyword in summary_lower for keyword in ['critical', 'down', 'outage', 'p1']):
            event.priority = "P1"
        elif any(keyword in summary_lower for keyword in ['high', 'urgent', 'p2', 'degraded']):
            event.priority = "P2"
        else:
            event.priority = "P3"
        
        return event
    
    # Enhanced mode methods (only available in enhanced mode)
    def create_jira_ticket(self, summary: str, description: str, priority: str = "Medium") -> Optional[JIRATicket]:
        """Create JIRA ticket (enhanced mode only)"""
        if self.mode != SREMode.ENHANCED:
            logger.warning("JIRA functionality only available in enhanced mode")
            return None
        return self.jira_tool.create_ticket(summary, description, priority)
    
    def send_slack_alert(self, message: str, channel: str = "#sre-alerts", priority: str = "P3") -> bool:
        """Send Slack alert (enhanced mode only)"""
        if self.mode != SREMode.ENHANCED:
            logger.warning("Slack functionality only available in enhanced mode")
            return False
        return self.slack_tool.send_alert(message, channel, priority)
    
    def query_datadog_metrics(self, query: str, time_range: str = "1h") -> List[DatadogMetric]:
        """Query Datadog metrics (enhanced mode only)"""
        if self.mode != SREMode.ENHANCED:
            logger.warning("Datadog functionality only available in enhanced mode")
            return []
        return self.datadog_tool.query_metrics(query, time_range)
    
    def get_jams_job_status(self, job_name: str) -> Dict[str, Any]:
        """Get JAMS job status (enhanced mode only)"""
        if self.mode != SREMode.ENHANCED:
            logger.warning("JAMS functionality only available in enhanced mode")
            return {}
        return self.jams_tool.get_job_status(job_name)
    
    # BestEgg SRE API specific methods
    def get_health_status(self) -> Dict[str, Any]:
        """Get BestEgg SRE API health status"""
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get health status: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_jams_history(self) -> List[Dict[str, Any]]:
        """Get JAMS job history from BestEgg SRE API"""
        try:
            url = f"{self.base_url}/jams/history"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('result', [])
        except Exception as e:
            logger.error(f"❌ Failed to get JAMS history: {e}")
            return []
    
    def create_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new event in BestEgg SRE API"""
        try:
            url = f"{self.base_url}/event_interactions/create"
            response = requests.post(url, json=event_data, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to create event: {e}")
            return None
    
    def update_event(self, event_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing event in BestEgg SRE API"""
        try:
            url = f"{self.base_url}/event_interactions/update"
            payload = {"identifier": event_id, **update_data}
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to update event {event_id}: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """Delete/archive an event in BestEgg SRE API"""
        try:
            url = f"{self.base_url}/event_interactions/delete"
            payload = {"identifier": event_id}
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete event {event_id}: {e}")
            return False
    
    def get_datadog_alerts(self) -> List[Dict[str, Any]]:
        """Get filtered Datadog alerts from BestEgg SRE API"""
        try:
            url = f"{self.base_url}/datadog_alert_filter"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('result', [])
        except Exception as e:
            logger.error(f"❌ Failed to get Datadog alerts: {e}")
            return []
    
    def get_jams_alerts(self) -> List[Dict[str, Any]]:
        """Get filtered JAMS alerts from BestEgg SRE API"""
        try:
            url = f"{self.base_url}/jams_alert_filter"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('result', [])
        except Exception as e:
            logger.error(f"❌ Failed to get JAMS alerts: {e}")
            return []
    
    def trigger_xmatters_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Trigger xMatters alert through BestEgg SRE API"""
        try:
            url = f"{self.base_url}/xmatters_interactions"
            response = requests.post(url, json=alert_data, headers=self.headers, timeout=10)
            response.raise_for_status()
            logger.info("✅ xMatters alert triggered successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to trigger xMatters alert: {e}")
            return False

# Enhanced tool classes (copied from enhanced plugin)
class JIRATool:
    """JIRA integration tool"""
    
    def __init__(self):
        self.api_key = config.JIRA_API_KEY
        self.username = config.JIRA_USERNAME
        self.base_url = config.JIRA_BASE_URL
        
        if not all([self.api_key, self.username, self.base_url]):
            logger.warning("JIRA credentials not configured")
    
    def create_ticket(self, summary: str, description: str, priority: str = "Medium") -> Optional[JIRATicket]:
        """Create a JIRA ticket"""
        if not all([self.api_key, self.username, self.base_url]):
            logger.error("JIRA credentials not configured")
            return None
        
        try:
            url = f"{self.base_url}/rest/api/3/issue"
            auth = (self.username, self.api_key)
            
            # Map priority to JIRA priority
            priority_map = {
                "Low": "Lowest",
                "Medium": "Medium", 
                "High": "High",
                "P1": "Highest",
                "P2": "High",
                "P3": "Medium"
            }
            
            jira_priority = priority_map.get(priority, "Medium")
            
            payload = {
                "fields": {
                    "project": {"key": "SRE"},
                    "summary": summary,
                    "description": description,
                    "issuetype": {"name": "Task"},
                    "priority": {"name": jira_priority}
                }
            }
            
            response = requests.post(url, json=payload, auth=auth, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            ticket_key = result.get('key')
            
            logger.info(f"✅ Created JIRA ticket: {ticket_key}")
            
            return JIRATicket(
                key=ticket_key,
                summary=summary,
                status="Open",
                assignee="Unassigned",
                priority=jira_priority,
                created=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to create JIRA ticket: {e}")
            return None

class SlackTool:
    """Slack integration tool"""
    
    def __init__(self):
        self.token = config.SLACK_TOKEN
        self.webhook_url = config.SLACK_WEBHOOK_URL
        
        if not self.token and not self.webhook_url:
            logger.warning("Slack credentials not configured")
    
    def send_alert(self, message: str, channel: str = "#sre-alerts", priority: str = "P3") -> bool:
        """Send Slack alert"""
        if not self.webhook_url:
            logger.error("Slack webhook URL not configured")
            return False
        
        try:
            # Add priority emoji
            priority_emojis = {
                "P1": "🚨",
                "P2": "⚠️", 
                "P3": "ℹ️"
            }
            
            emoji = priority_emojis.get(priority, "🟢")
            formatted_message = f"{emoji} **{priority} Alert**\n{message}"
            
            payload = {
                "text": formatted_message,
                "channel": channel
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"✅ Sent Slack alert to {channel}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Slack alert: {e}")
            return False

class DatadogTool:
    """Datadog integration tool"""
    
    def __init__(self):
        self.api_key = config.DATADOG_API_KEY
        self.app_key = config.DATADOG_APP_KEY
        
        if not all([self.api_key, self.app_key]):
            logger.warning("Datadog credentials not configured")
    
    def query_metrics(self, query: str, time_range: str = "1h") -> List[DatadogMetric]:
        """Query Datadog metrics"""
        if not all([self.api_key, self.app_key]):
            logger.error("Datadog credentials not configured")
            return []
        
        try:
            url = "https://api.datadoghq.com/api/v1/query"
            headers = {
                "DD-API-KEY": self.api_key,
                "DD-APPLICATION-KEY": self.app_key
            }
            
            params = {
                "query": query,
                "from": f"-{time_range}"
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            metrics = []
            
            for series in data.get('series', []):
                metric = DatadogMetric(
                    name=series.get('metric', ''),
                    value=series.get('pointlist', [[0, 0]])[-1][1] if series.get('pointlist') else 0,
                    timestamp=datetime.now().isoformat(),
                    tags=series.get('tag_set', {})
                )
                metrics.append(metric)
            
            logger.info(f"✅ Queried {len(metrics)} Datadog metrics")
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to query Datadog metrics: {e}")
            return []

class JAMSTool:
    """JAMS integration tool"""
    
    def __init__(self):
        self.username = config.JAMS_USERNAME
        self.password = config.JAMS_PASSWORD
        self.base_url = config.JAMS_BASE_URL
        
        if not all([self.username, self.password, self.base_url]):
            logger.warning("JAMS credentials not configured")
    
    def get_job_status(self, job_name: str) -> Dict[str, Any]:
        """Get JAMS job status"""
        if not all([self.username, self.password, self.base_url]):
            logger.error("JAMS credentials not configured")
            return {}
        
        try:
            url = f"{self.base_url}/api/jobs/{job_name}"
            auth = (self.username, self.password)
            
            response = requests.get(url, auth=auth, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Retrieved JAMS job status for {job_name}")
            
            return {
                "job_name": job_name,
                "status": data.get('status', 'Unknown'),
                "last_run": data.get('last_run', ''),
                "next_run": data.get('next_run', ''),
                "success": data.get('success', False)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get JAMS job status: {e}")
            return {}

# Factory function for easy instantiation
def create_sre_tool(mode: Union[str, SREMode] = "enhanced", **kwargs) -> UnifiedSRETool:
    """
    Factory function to create SRE tool instances
    
    Args:
        mode: "simple" or "enhanced" (default: "enhanced")
        **kwargs: Additional arguments passed to UnifiedSRETool
    
    Returns:
        UnifiedSRETool instance
    """
    if isinstance(mode, str):
        mode = SREMode(mode.lower())
    
    return UnifiedSRETool(mode=mode, **kwargs)

# Backward compatibility aliases
SREEventsTool = lambda **kwargs: create_sre_tool("simple", **kwargs)
EnhancedSREEventsTool = lambda **kwargs: create_sre_tool("enhanced", **kwargs)
