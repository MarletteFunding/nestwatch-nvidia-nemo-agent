"""
LLM Circuit Breaker
Prevents hammering the LLM provider when quota is exhausted
"""
import logging
import time
import os
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, no calls allowed
    HALF_OPEN = "half_open"  # Testing if service is back

class LLMCircuitBreaker:
    """Circuit breaker for LLM quota exhaustion"""
    
    def __init__(self):
        # Configuration
        self.cb_minutes = int(os.getenv("LLM_CB_MINUTES", "30"))  # 30 minutes default
        self.cb_timeout = self.cb_minutes * 60  # Convert to seconds
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.next_attempt_time = 0
        
        # Thresholds
        self.failure_threshold = 1  # Open circuit on first quota error
        self.success_threshold = 1  # Close circuit on first success
        
        logger.info(f"Circuit breaker initialized: timeout={self.cb_minutes}min")
    
    def _is_quota_error(self, error: Exception) -> bool:
        """Check if error indicates quota exhaustion"""
        error_str = str(error).lower()
        
        # Check for quota-related error messages
        quota_indicators = [
            "insufficient_quota",
            "quota exceeded",
            "billing details",
            "rate limit exceeded",
            "too many requests"
        ]
        
        return any(indicator in error_str for indicator in quota_indicators)
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return time.time() >= self.next_attempt_time
    
    def call(self, func, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or raises exception
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: attempting reset (half-open)")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. Next attempt in {int(self.next_attempt_time - time.time())} seconds"
                )
        
        # Execute the function
        try:
            result = func(*args, **kwargs)
            
            # Success - reset circuit if it was half-open
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker: reset to CLOSED (success)")
            
            return result
            
        except Exception as e:
            # Check if this is a quota error
            if self._is_quota_error(e):
                self._record_failure()
                logger.warning(f"Circuit breaker: quota error detected - {e}")
            else:
                # Non-quota error, don't affect circuit breaker
                logger.debug(f"Circuit breaker: non-quota error - {e}")
            
            raise
    
    def _record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.next_attempt_time = time.time() + self.cb_timeout
            logger.warning(f"Circuit breaker: OPENED for {self.cb_minutes} minutes due to quota exhaustion")
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open (read-only operation)"""
        return self.state == CircuitState.OPEN
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "next_attempt_time": self.next_attempt_time,
            "time_until_reset": max(0, self.next_attempt_time - time.time())
        }
    
    def force_reset(self):
        """Force reset the circuit breaker (for testing/admin)"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.next_attempt_time = 0
        logger.info("Circuit breaker: force reset to CLOSED")


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


# Global circuit breaker instance
llm_circuit_breaker = LLMCircuitBreaker()
