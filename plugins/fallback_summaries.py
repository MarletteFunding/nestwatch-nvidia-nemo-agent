"""
Deterministic Fallback Summaries
Provides SRE analysis without LLM when quota is exhausted
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .sre_context_compactor import context_compactor

logger = logging.getLogger(__name__)

class FallbackSummarizer:
    """Generates deterministic SRE summaries without LLM"""
    
    def __init__(self):
        self.high_impact_keywords = {
            'payment', 'checkout', 'auth', 'login', 'api', 'gateway', 
            'db', 'cache', 'kafka', 'timeout', '5xx', 'error', 'latency',
            'critical', 'down', 'outage', 'fail', 'exception', 'crash'
        }
    
    def generate_enhanced_summary(self, events: List[Dict[str, Any]], window: str = "last_24h") -> Dict[str, Any]:
        """
        Generate enhanced summary without LLM
        
        Args:
            events: List of SRE events
            window: Time window for analysis
            
        Returns:
            Enhanced summary in the same format as LLM response
        """
        if not events:
            return self._empty_summary()
        
        # Calculate totals
        totals = self._calculate_totals(events)
        
        # Analyze events
        priority_breakdown = self._analyze_by_priority(events)
        source_breakdown = self._analyze_by_source(events)
        top_events = self._identify_top_events(events)
        recommendations = self._generate_recommendations(events, totals)
        actions = self._generate_actions(events, totals)
        
        return {
            "totals": totals['total'],
            "by_priority": priority_breakdown,
            "by_source": source_breakdown,
            "top_events": top_events,
            "recommendations": recommendations,
            "actions": actions,
            "analysis_metadata": {
                "generated_by": "fallback_summarizer",
                "window": window,
                "timestamp": datetime.utcnow().isoformat(),
                "quota_degraded": True
            }
        }
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure"""
        return {
            "totals": 0,
            "by_priority": {"P1": 0, "P2": 0, "P3": 0},
            "by_source": {},
            "top_events": [],
            "recommendations": [],
            "actions": [],
            "analysis_metadata": {
                "generated_by": "fallback_summarizer",
                "window": "last_24h",
                "timestamp": datetime.utcnow().isoformat(),
                "quota_degraded": True
            }
        }
    
    def _calculate_totals(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate event totals and breakdowns"""
        totals = {
            'total': len(events),
            'P1': 0,
            'P2': 0,
            'P3': 0,
            'sources': {}
        }
        
        for event in events:
            # Count priorities
            priority = event.get('priority', 'P3')
            if priority in totals:
                totals[priority] += 1
            
            # Count sources
            source = event.get('source', 'unknown')
            totals['sources'][source] = totals['sources'].get(source, 0) + 1
        
        return totals
    
    def _analyze_by_priority(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze events by priority"""
        breakdown = {"P1": 0, "P2": 0, "P3": 0}
        
        for event in events:
            priority = event.get('priority', 'P3')
            if priority in breakdown:
                breakdown[priority] += 1
        
        return breakdown
    
    def _analyze_by_source(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze events by source"""
        breakdown = {}
        
        for event in events:
            source = event.get('source', 'unknown')
            breakdown[source] = breakdown.get(source, 0) + 1
        
        return breakdown
    
    def _identify_top_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify top priority events"""
        # Score events by importance
        scored_events = []
        
        for event in events:
            score = self._calculate_event_importance(event)
            scored_events.append((score, event))
        
        # Sort by score and take top 5
        scored_events.sort(key=lambda x: x[0], reverse=True)
        top_events = scored_events[:5]
        
        result = []
        for i, (score, event) in enumerate(top_events):
            result.append({
                "id": event.get('id', f'event_{i}'),
                "priority": event.get('priority', 'P3'),
                "source": event.get('source', 'unknown'),
                "why_top": self._generate_why_top(event, score),
                "summary": event.get('summary', '')[:100]  # Truncate
            })
        
        return result
    
    def _calculate_event_importance(self, event: Dict[str, Any]) -> float:
        """Calculate importance score for an event"""
        score = 0.0
        
        # Priority scoring
        priority = event.get('priority', 'P3')
        if priority == 'P1':
            score += 100
        elif priority == 'P2':
            score += 50
        elif priority == 'P3':
            score += 10
        
        # Status scoring
        status = event.get('status', '').lower()
        if status in ['open', 'in progress', 'investigating']:
            score += 30
        elif status in ['resolved', 'closed']:
            score += 5
        
        # Keyword scoring
        summary = event.get('summary', '').lower()
        keyword_matches = sum(1 for keyword in self.high_impact_keywords if keyword in summary)
        score += keyword_matches * 15
        
        return score
    
    def _generate_why_top(self, event: Dict[str, Any], score: float) -> str:
        """Generate explanation for why event is top priority"""
        reasons = []
        
        priority = event.get('priority', 'P3')
        if priority in ['P1', 'P2']:
            reasons.append(f"High priority ({priority})")
        
        status = event.get('status', '').lower()
        if status in ['open', 'in progress']:
            reasons.append("Active status")
        
        summary = event.get('summary', '').lower()
        keyword_matches = [kw for kw in self.high_impact_keywords if kw in summary]
        if keyword_matches:
            reasons.append(f"Contains critical keywords: {', '.join(keyword_matches[:3])}")
        
        if not reasons:
            reasons.append("Recent event requiring attention")
        
        return "; ".join(reasons)
    
    def _generate_recommendations(self, events: List[Dict[str, Any]], totals: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Priority-based recommendations
        if totals['P1'] > 0:
            recommendations.append("🚨 CRITICAL: Address P1 events immediately - these require urgent attention")
        
        if totals['P2'] > 3:
            recommendations.append("⚠️ HIGH: Multiple P2 events detected - consider increasing monitoring sensitivity")
        
        # Source-based recommendations
        sources = totals['sources']
        if sources.get('datadog', 0) > 20:
            recommendations.append("📈 Datadog: High alert volume - review alert thresholds and reduce noise")
        
        if sources.get('jams', 0) > 5:
            recommendations.append("⚙️ JAMS: Multiple job failures - investigate job dependencies and retry logic")
        
        if sources.get('jira', 0) > 3:
            recommendations.append("🎫 JIRA: Several tickets created - ensure proper triage and assignment")
        
        # Status-based recommendations
        open_events = [e for e in events if e.get('status', '').lower() in ['open', 'in progress']]
        if len(open_events) > 10:
            recommendations.append("📋 Status: Many open events - consider implementing automated resolution workflows")
        
        # Keyword-based recommendations
        high_impact_events = [e for e in events if any(kw in e.get('summary', '').lower() for kw in self.high_impact_keywords)]
        if len(high_impact_events) > 5:
            recommendations.append("🔍 Impact: Multiple high-impact events - review system architecture for single points of failure")
        
        # Default recommendation if none generated
        if not recommendations:
            recommendations.append("✅ System appears stable - continue monitoring for any emerging issues")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _generate_actions(self, events: List[Dict[str, Any]], totals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate safe, dry-run actions"""
        actions = []
        
        # Only generate actions for high-priority events
        high_priority_events = [e for e in events if e.get('priority') in ['P1', 'P2']]
        
        if high_priority_events:
            # Create a Slack notification action
            actions.append({
                "provider": "slack",
                "dry_run": True,
                "why": f"Notify team about {len(high_priority_events)} high-priority events requiring attention",
                "risk": "Low - informational notification only",
                "rollback": "No rollback needed for notifications"
            })
        
        # Create monitoring action if many events
        if totals['total'] > 20:
            actions.append({
                "provider": "datadog",
                "dry_run": True,
                "why": "Review and tune alert thresholds to reduce noise",
                "risk": "Low - read-only analysis",
                "rollback": "No changes made, analysis only"
            })
        
        return actions


# Global fallback summarizer instance
fallback_summarizer = FallbackSummarizer()
