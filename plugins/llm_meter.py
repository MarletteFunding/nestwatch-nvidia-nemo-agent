"""
LLM Usage Metering and Budget Guards
Tracks token usage and enforces budget limits
"""
import logging
import time
import json
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)

# Try to import Redis for usage tracking
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available for usage metering, using in-memory tracking")

class LLMUsageMeter:
    """Tracks LLM usage and enforces budget limits"""
    
    def __init__(self):
        # Configuration
        self.daily_budget_tokens = int(os.getenv("LLM_DAILY_BUDGET_TOKENS", "200000"))
        self.hourly_budget_tokens = int(os.getenv("LLM_HOURLY_BUDGET_TOKENS", "40000"))
        self.daily_budget_usd = float(os.getenv("LLM_DAILY_BUDGET_USD", "0"))  # 0 = disabled
        self.slack_webhook = os.getenv("LLM_SPEND_ALERT_SLACK_WEBHOOK")
        
        # Redis client for usage tracking
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Redis connected for usage metering")
            except Exception as e:
                logger.warning(f"Redis connection failed for usage metering: {e}")
                self.redis_client = None
        
        # In-memory fallback
        self.memory_usage = {}
        
        # Alert tracking (prevent spam)
        self.last_alert_time = {}
        
        logger.info(f"Usage meter initialized: daily={self.daily_budget_tokens}, hourly={self.hourly_budget_tokens}")
    
    def _get_date_key(self, date: datetime = None) -> str:
        """Get Redis key for daily usage"""
        if date is None:
            date = datetime.utcnow()
        return f"llm:usage:{date.strftime('%Y%m%d')}"
    
    def _get_hour_key(self, hour: datetime = None) -> str:
        """Get Redis key for hourly usage"""
        if hour is None:
            hour = datetime.utcnow()
        return f"llm:usage:hourly:{hour.strftime('%Y%m%d%H')}"
    
    def _get_memory_key(self, key: str) -> str:
        """Get in-memory usage key"""
        return f"usage:{key}"
    
    def _get_usage(self, key: str) -> Dict[str, int]:
        """Get usage data from Redis or memory"""
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # Fallback to memory
        memory_key = self._get_memory_key(key)
        return self.memory_usage.get(memory_key, {"tokens": 0, "requests": 0, "cost_usd": 0.0})
    
    def _set_usage(self, key: str, usage: Dict[str, Any]) -> None:
        """Set usage data in Redis or memory"""
        if self.redis_client:
            try:
                # Set with 7-day expiration for daily keys, 25-hour for hourly
                ttl = 7 * 24 * 3600 if "hourly" not in key else 25 * 3600
                self.redis_client.setex(key, ttl, json.dumps(usage))
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # Always update memory as backup
        memory_key = self._get_memory_key(key)
        self.memory_usage[memory_key] = usage
    
    def _increment_usage(self, key: str, tokens: int, cost_usd: float = 0.0) -> Dict[str, Any]:
        """Increment usage counters"""
        usage = self._get_usage(key)
        usage["tokens"] = usage.get("tokens", 0) + tokens
        usage["requests"] = usage.get("requests", 0) + 1
        usage["cost_usd"] = usage.get("cost_usd", 0.0) + cost_usd
        usage["last_updated"] = time.time()
        
        self._set_usage(key, usage)
        return usage
    
    def record_usage(self, prompt_tokens: int, completion_tokens: int, cost_usd: float = 0.0) -> None:
        """
        Record LLM usage
        
        Args:
            prompt_tokens: Number of prompt tokens used
            completion_tokens: Number of completion tokens used
            cost_usd: Cost in USD (optional)
        """
        total_tokens = prompt_tokens + completion_tokens
        now = datetime.utcnow()
        
        # Record daily usage
        daily_key = self._get_date_key(now)
        daily_usage = self._increment_usage(daily_key, total_tokens, cost_usd)
        
        # Record hourly usage
        hourly_key = self._get_hour_key(now)
        hourly_usage = self._increment_usage(hourly_key, total_tokens, cost_usd)
        
        logger.debug(f"Usage recorded: {total_tokens} tokens, ${cost_usd:.4f}")
        
        # Check budget limits and send alerts
        self._check_budget_limits(daily_usage, hourly_usage)
    
    def _check_budget_limits(self, daily_usage: Dict[str, Any], hourly_usage: Dict[str, Any]) -> None:
        """Check budget limits and send alerts if needed"""
        daily_tokens = daily_usage.get("tokens", 0)
        hourly_tokens = hourly_usage.get("tokens", 0)
        daily_cost = daily_usage.get("cost_usd", 0.0)
        
        # Check daily token budget
        if daily_tokens >= self.daily_budget_tokens * 0.9:  # 90% threshold
            self._send_alert("daily_tokens_90", f"Daily token budget 90% reached: {daily_tokens}/{self.daily_budget_tokens}")
        
        if daily_tokens >= self.daily_budget_tokens:  # 100% threshold
            self._send_alert("daily_tokens_100", f"Daily token budget exceeded: {daily_tokens}/{self.daily_budget_tokens}")
        
        # Check hourly token budget
        if hourly_tokens >= self.hourly_budget_tokens * 0.9:  # 90% threshold
            self._send_alert("hourly_tokens_90", f"Hourly token budget 90% reached: {hourly_tokens}/{self.hourly_budget_tokens}")
        
        if hourly_tokens >= self.hourly_budget_tokens:  # 100% threshold
            self._send_alert("hourly_tokens_100", f"Hourly token budget exceeded: {hourly_tokens}/{self.hourly_budget_tokens}")
        
        # Check daily cost budget (if enabled)
        if self.daily_budget_usd > 0:
            if daily_cost >= self.daily_budget_usd * 0.9:  # 90% threshold
                self._send_alert("daily_cost_90", f"Daily cost budget 90% reached: ${daily_cost:.2f}/${self.daily_budget_usd:.2f}")
            
            if daily_cost >= self.daily_budget_usd:  # 100% threshold
                self._send_alert("daily_cost_100", f"Daily cost budget exceeded: ${daily_cost:.2f}/${self.daily_budget_usd:.2f}")
    
    def _send_alert(self, alert_type: str, message: str) -> None:
        """Send alert to Slack (if configured)"""
        # Prevent spam - only send one alert per type per hour
        now = time.time()
        last_alert = self.last_alert_time.get(alert_type, 0)
        if now - last_alert < 3600:  # 1 hour cooldown
            return
        
        self.last_alert_time[alert_type] = now
        
        if self.slack_webhook:
            try:
                payload = {
                    "text": f"🚨 LLM Budget Alert: {message}",
                    "username": "SRE Dashboard",
                    "icon_emoji": ":warning:"
                }
                
                response = requests.post(self.slack_webhook, json=payload, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Budget alert sent: {message}")
                else:
                    logger.warning(f"Failed to send budget alert: {response.status_code}")
            except Exception as e:
                logger.warning(f"Error sending budget alert: {e}")
        else:
            logger.warning(f"Budget alert (no webhook): {message}")
    
    def is_budget_exceeded(self) -> Tuple[bool, str]:
        """
        Check if any budget limits are exceeded
        
        Returns:
            Tuple of (is_exceeded, reason)
        """
        now = datetime.utcnow()
        
        # Check daily usage
        daily_key = self._get_date_key(now)
        daily_usage = self._get_usage(daily_key)
        daily_tokens = daily_usage.get("tokens", 0)
        daily_cost = daily_usage.get("cost_usd", 0.0)
        
        if daily_tokens >= self.daily_budget_tokens:
            return True, f"Daily token budget exceeded: {daily_tokens}/{self.daily_budget_tokens}"
        
        if self.daily_budget_usd > 0 and daily_cost >= self.daily_budget_usd:
            return True, f"Daily cost budget exceeded: ${daily_cost:.2f}/${self.daily_budget_usd:.2f}"
        
        # Check hourly usage
        hourly_key = self._get_hour_key(now)
        hourly_usage = self._get_usage(hourly_key)
        hourly_tokens = hourly_usage.get("tokens", 0)
        
        if hourly_tokens >= self.hourly_budget_tokens:
            return True, f"Hourly token budget exceeded: {hourly_tokens}/{self.hourly_budget_tokens}"
        
        return False, ""
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary"""
        now = datetime.utcnow()
        
        # Get daily usage
        daily_key = self._get_date_key(now)
        daily_usage = self._get_usage(daily_key)
        
        # Get hourly usage
        hourly_key = self._get_hour_key(now)
        hourly_usage = self._get_usage(hourly_key)
        
        # Calculate percentages
        daily_token_pct = (daily_usage.get("tokens", 0) / self.daily_budget_tokens) * 100
        hourly_token_pct = (hourly_usage.get("tokens", 0) / self.hourly_budget_tokens) * 100
        
        daily_cost_pct = 0.0
        if self.daily_budget_usd > 0:
            daily_cost_pct = (daily_usage.get("cost_usd", 0.0) / self.daily_budget_usd) * 100
        
        return {
            "daily": {
                "tokens": daily_usage.get("tokens", 0),
                "budget": self.daily_budget_tokens,
                "percentage": daily_token_pct,
                "cost_usd": daily_usage.get("cost_usd", 0.0),
                "cost_budget": self.daily_budget_usd,
                "cost_percentage": daily_cost_pct,
                "requests": daily_usage.get("requests", 0)
            },
            "hourly": {
                "tokens": hourly_usage.get("tokens", 0),
                "budget": self.hourly_budget_tokens,
                "percentage": hourly_token_pct,
                "requests": hourly_usage.get("requests", 0)
            },
            "budget_exceeded": daily_token_pct >= 100 or hourly_token_pct >= 100 or daily_cost_pct >= 100
        }


# Global usage meter instance
llm_usage_meter = LLMUsageMeter()
