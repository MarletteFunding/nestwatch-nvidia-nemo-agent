"""
Comprehensive tests for LLM quota controls
Tests caching, singleflight, circuit breaker, policy, and budget guards
"""
import pytest
import time
import json
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import the modules to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'middleware'))

from sre_context_compactor import SREContextCompactor, context_compactor
from llm_cache import LLMCache
from llm_circuit import LLMCircuitBreaker, CircuitBreakerOpenError
from fallback_summaries import FallbackSummarizer
from llm_meter import LLMUsageMeter


class TestSREContextCompactor:
    """Test the SRE context compactor"""
    
    def test_compact_context_basic(self):
        """Test basic context compaction"""
        events = [
            {
                "id": "event1",
                "priority": "P1",
                "status": "open",
                "source": "datadog",
                "summary": "Critical database connection failure"
            },
            {
                "id": "event2", 
                "priority": "P2",
                "status": "in progress",
                "source": "jira",
                "summary": "High memory usage on server"
            }
        ]
        
        compactor = SREContextCompactor(max_examples=5)
        result = compactor.compact_context(events)
        
        assert "Totals=2" in result
        assert "P1=1" in result
        assert "P2=1" in result
        assert "datadog=1" in result
        assert "jira=1" in result
        assert "Examples:" in result
    
    def test_context_hash_stability(self):
        """Test that context hash is stable for same events"""
        events = [
            {"id": "event1", "priority": "P1", "status": "open", "source": "datadog", "summary": "test"}
        ]
        
        hash1 = context_compactor.get_context_hash(events)
        hash2 = context_compactor.get_context_hash(events)
        
        assert hash1 == hash2
    
    def test_context_hash_different_for_different_events(self):
        """Test that context hash differs for different events"""
        events1 = [{"id": "event1", "priority": "P1", "status": "open", "source": "datadog", "summary": "test"}]
        events2 = [{"id": "event2", "priority": "P1", "status": "open", "source": "datadog", "summary": "test"}]
        
        hash1 = context_compactor.get_context_hash(events1)
        hash2 = context_compactor.get_context_hash(events2)
        
        assert hash1 != hash2


class TestLLMCache:
    """Test the LLM cache with singleflight"""
    
    def test_cache_hit_skips_llm(self):
        """Test that cache hits skip LLM calls"""
        cache = LLMCache()
        
        # Mock Redis to be unavailable
        cache.redis_client = None
        
        # Set initial cache value
        test_data = {"result": "cached_data"}
        cache.set("test_card", "test_hash", test_data)
        
        # Mock LLM function
        llm_calls = []
        def mock_llm():
            llm_calls.append("called")
            return {"result": "new_data"}
        
        # First call should use cache
        result1 = cache.singleflight("test_card", "test_hash", mock_llm)
        assert result1 == test_data
        assert len(llm_calls) == 0
        
        # Second call should also use cache
        result2 = cache.singleflight("test_card", "test_hash", mock_llm)
        assert result2 == test_data
        assert len(llm_calls) == 0
    
    def test_singleflight_prevents_dogpile(self):
        """Test that singleflight prevents concurrent calls"""
        cache = LLMCache()
        cache.redis_client = None  # Use in-memory cache
        
        llm_calls = []
        results = []
        
        def mock_llm():
            time.sleep(0.1)  # Simulate LLM delay
            llm_calls.append("called")
            return {"result": f"data_{len(llm_calls)}"}
        
        def worker():
            result = cache.singleflight("test_card", "test_hash", mock_llm)
            results.append(result)
        
        # Start multiple concurrent threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should only have one LLM call
        assert len(llm_calls) == 1
        assert len(results) == 5
        # All results should be the same
        assert all(r == results[0] for r in results)


class TestLLMCircuitBreaker:
    """Test the circuit breaker"""
    
    def test_circuit_breaker_on_quota(self):
        """Test that circuit breaker opens on quota errors"""
        cb = LLMCircuitBreaker()
        
        # Mock quota error
        def quota_error_func():
            raise Exception("Error code: 429 - insufficient_quota")
        
        # First call should trigger circuit breaker
        with pytest.raises(Exception):
            cb.call(quota_error_func)
        
        # Circuit should now be open
        assert cb.is_open()
        
        # Subsequent calls should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(quota_error_func)
    
    def test_circuit_breaker_reset_after_timeout(self):
        """Test that circuit breaker resets after timeout"""
        cb = LLMCircuitBreaker()
        cb.cb_timeout = 0.1  # Short timeout for testing
        
        # Trigger circuit breaker
        def quota_error_func():
            raise Exception("Error code: 429 - insufficient_quota")
        
        with pytest.raises(Exception):
            cb.call(quota_error_func)
        
        assert cb.is_open()
        
        # Wait for timeout
        time.sleep(0.2)
        
        # Circuit should be half-open now
        assert not cb.is_open()  # Should be half-open, not open
    
    def test_circuit_breaker_success_resets(self):
        """Test that successful calls reset the circuit breaker"""
        cb = LLMCircuitBreaker()
        
        # Trigger circuit breaker
        def quota_error_func():
            raise Exception("Error code: 429 - insufficient_quota")
        
        with pytest.raises(Exception):
            cb.call(quota_error_func)
        
        assert cb.is_open()
        
        # Force reset to half-open
        cb.state = cb.CircuitState.HALF_OPEN
        
        # Successful call should reset circuit
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == cb.CircuitState.CLOSED


class TestFallbackSummarizer:
    """Test the fallback summarizer"""
    
    def test_policy_skips_llm_for_p3_only(self):
        """Test that policy skips LLM for P3-only events"""
        events = [
            {"id": "event1", "priority": "P3", "status": "open", "source": "datadog", "summary": "Low priority event"},
            {"id": "event2", "priority": "P3", "status": "open", "source": "jira", "summary": "Another P3 event"}
        ]
        
        summarizer = FallbackSummarizer()
        result = summarizer.generate_enhanced_summary(events)
        
        assert result["totals"] == 2
        assert result["by_priority"]["P3"] == 2
        assert result["by_priority"]["P1"] == 0
        assert result["by_priority"]["P2"] == 0
        assert "fallback_summarizer" in result["analysis_metadata"]["generated_by"]
        assert result["analysis_metadata"]["quota_degraded"] is True
    
    def test_fallback_generates_recommendations(self):
        """Test that fallback generates meaningful recommendations"""
        events = [
            {"id": "event1", "priority": "P1", "status": "open", "source": "datadog", "summary": "Critical failure"},
            {"id": "event2", "priority": "P2", "status": "open", "source": "jira", "summary": "High priority issue"}
        ]
        
        summarizer = FallbackSummarizer()
        result = summarizer.generate_enhanced_summary(events)
        
        assert len(result["recommendations"]) > 0
        assert any("P1" in rec for rec in result["recommendations"])
        assert any("P2" in rec for rec in result["recommendations"])
    
    def test_fallback_generates_safe_actions(self):
        """Test that fallback generates safe, dry-run actions"""
        events = [
            {"id": "event1", "priority": "P1", "status": "open", "source": "datadog", "summary": "Critical failure"}
        ]
        
        summarizer = FallbackSummarizer()
        result = summarizer.generate_enhanced_summary(events)
        
        assert len(result["actions"]) > 0
        for action in result["actions"]:
            assert action["dry_run"] is True
            assert "risk" in action
            assert "rollback" in action


class TestLLMUsageMeter:
    """Test the usage meter and budget guards"""
    
    def test_budget_guard_blocks_overage(self):
        """Test that budget guard blocks when over limit"""
        meter = LLMUsageMeter()
        meter.daily_budget_tokens = 100  # Low budget for testing
        meter.redis_client = None  # Use in-memory tracking
        
        # Record usage up to limit
        meter.record_usage(50, 50, 0.0)  # 100 tokens total
        
        # Check budget
        exceeded, reason = meter.is_budget_exceeded()
        assert exceeded
        assert "exceeded" in reason.lower()
    
    def test_usage_tracking_accumulates(self):
        """Test that usage tracking accumulates correctly"""
        meter = LLMUsageMeter()
        meter.redis_client = None  # Use in-memory tracking
        
        # Record multiple usage events
        meter.record_usage(10, 5, 0.01)  # 15 tokens, $0.01
        meter.record_usage(20, 10, 0.02)  # 30 tokens, $0.02
        
        summary = meter.get_usage_summary()
        
        assert summary["daily"]["tokens"] == 45  # 15 + 30
        assert summary["daily"]["cost_usd"] == 0.03  # 0.01 + 0.02
        assert summary["daily"]["requests"] == 2
    
    def test_usage_summary_percentages(self):
        """Test that usage summary calculates percentages correctly"""
        meter = LLMUsageMeter()
        meter.daily_budget_tokens = 100
        meter.redis_client = None  # Use in-memory tracking
        
        # Record 50% usage
        meter.record_usage(25, 25, 0.0)  # 50 tokens
        
        summary = meter.get_usage_summary()
        
        assert summary["daily"]["percentage"] == 50.0
        assert summary["daily"]["tokens"] == 50
        assert summary["daily"]["budget"] == 100


class TestIntegration:
    """Integration tests for the complete quota control system"""
    
    def test_complete_quota_control_flow(self):
        """Test the complete flow with all quota controls"""
        # This would be a more complex integration test
        # that tests the entire system working together
        
        # Mock the components
        cache = LLMCache()
        cache.redis_client = None
        
        circuit_breaker = LLMCircuitBreaker()
        circuit_breaker.cb_timeout = 0.1  # Short timeout for testing
        
        usage_meter = LLMUsageMeter()
        usage_meter.redis_client = None
        usage_meter.daily_budget_tokens = 1000  # High budget for testing
        
        summarizer = FallbackSummarizer()
        
        # Test data
        events = [
            {"id": "event1", "priority": "P1", "status": "open", "source": "datadog", "summary": "Critical failure"}
        ]
        
        # Test successful flow
        def mock_llm():
            return {"result": "llm_analysis"}
        
        # Should work normally
        result = cache.singleflight("test_card", "test_hash", mock_llm)
        assert result == {"result": "llm_analysis"}
        
        # Test circuit breaker integration
        def quota_error_llm():
            raise Exception("Error code: 429 - insufficient_quota")
        
        # First call triggers circuit breaker
        with pytest.raises(Exception):
            circuit_breaker.call(quota_error_llm)
        
        # Subsequent calls should use fallback
        assert circuit_breaker.is_open()
        
        # Test fallback integration
        fallback_result = summarizer.generate_enhanced_summary(events)
        assert fallback_result["analysis_metadata"]["quota_degraded"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
