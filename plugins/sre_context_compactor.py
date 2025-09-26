"""
SRE Context Compactor - Reduces token usage by creating concise event summaries
"""
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class SREContextCompactor:
    """Compacts SRE events into token-efficient summaries"""
    
    # High-impact keywords that indicate critical issues
    HIGH_IMPACT_KEYWORDS = {
        'payment', 'checkout', 'auth', 'login', 'api', 'gateway', 
        'db', 'cache', 'kafka', 'timeout', '5xx', 'error', 'latency',
        'critical', 'down', 'outage', 'fail', 'exception', 'crash'
    }
    
    def __init__(self, max_examples: int = 12):
        self.max_examples = max_examples
    
    def compact_context(self, events: List[Dict[str, Any]]) -> str:
        """
        Create a compact context string from SRE events
        
        Args:
            events: List of SRE event dictionaries
            
        Returns:
            Compact string representation of events
        """
        if not events:
            return "No events"
        
        # Calculate totals and breakdowns
        totals = self._calculate_totals(events)
        
        # Score and select top events
        scored_events = self._score_events(events)
        top_events = scored_events[:self.max_examples]
        
        # Build compact summary
        summary_parts = []
        
        # Header with totals
        summary_parts.append(f"Totals={totals['total']}; P1={totals['P1']}; P2={totals['P2']}; P3={totals['P3']}")
        
        # Source breakdown
        source_breakdown = ", ".join([f"{k}={v}" for k, v in totals['sources'].items()])
        summary_parts.append(f"Sources: {source_breakdown}")
        
        # Top events examples
        if top_events:
            summary_parts.append("Examples:")
            for event in top_events:
                example = self._format_event_example(event)
                summary_parts.append(f"- {example}")
        
        return "\n".join(summary_parts)
    
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
    
    def _score_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score events by importance and return sorted list"""
        scored_events = []
        
        for event in events:
            score = self._calculate_event_score(event)
            scored_events.append((score, event))
        
        # Sort by score (highest first)
        scored_events.sort(key=lambda x: x[0], reverse=True)
        
        # Return just the events
        return [event for _, event in scored_events]
    
    def _calculate_event_score(self, event: Dict[str, Any]) -> float:
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
        
        # Status scoring (Open/In Progress events are more important)
        status = event.get('status', '').lower()
        if status in ['open', 'in progress', 'investigating']:
            score += 30
        elif status in ['resolved', 'closed']:
            score += 5
        
        # Recency scoring (events from last 10 hours get bonus)
        timestamp = event.get('timestamp')
        if timestamp:
            try:
                if isinstance(timestamp, str):
                    # Parse ISO format timestamp
                    event_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    event_time = timestamp
                
                now = datetime.now(event_time.tzinfo) if event_time.tzinfo else datetime.now()
                hours_ago = (now - event_time).total_seconds() / 3600
                
                if hours_ago <= 10:
                    score += 20
                elif hours_ago <= 24:
                    score += 10
            except (ValueError, TypeError):
                # If timestamp parsing fails, give default score
                score += 5
        
        # Keyword scoring
        summary = event.get('summary', '').lower()
        keyword_matches = sum(1 for keyword in self.HIGH_IMPACT_KEYWORDS if keyword in summary)
        score += keyword_matches * 15
        
        return score
    
    def _format_event_example(self, event: Dict[str, Any]) -> str:
        """Format a single event as a compact example"""
        parts = []
        
        # Event ID (truncated)
        event_id = event.get('id', 'unknown')
        if len(event_id) > 12:
            event_id = event_id[:12] + '...'
        parts.append(f"id={event_id}")
        
        # Source
        source = event.get('source', 'unknown')
        parts.append(f"src={source}")
        
        # Priority
        priority = event.get('priority', 'P3')
        parts.append(f"pri={priority}")
        
        # Status
        status = event.get('status', 'unknown')
        parts.append(f"status={status}")
        
        # Summary (truncated to 60 chars)
        summary = event.get('summary', '')
        if len(summary) > 60:
            summary = summary[:57] + '...'
        parts.append(f"sum={summary}")
        
        return " ".join(parts)
    
    def get_context_hash(self, events: List[Dict[str, Any]]) -> str:
        """Generate a hash of the event context for caching"""
        # Create a stable representation of the events
        context_data = []
        for event in sorted(events, key=lambda x: x.get('id', '')):
            # Include only the fields that matter for analysis
            context_data.append({
                'id': event.get('id'),
                'priority': event.get('priority'),
                'status': event.get('status'),
                'source': event.get('source'),
                'summary': event.get('summary', '')[:100]  # Truncate summary for hash
            })
        
        # Create hash
        context_str = str(context_data)
        return hashlib.sha256(context_str.encode()).hexdigest()[:16]


# Global instance
context_compactor = SREContextCompactor()