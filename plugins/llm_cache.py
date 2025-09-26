"""
LLM Cache with Redis and Singleflight
Provides caching and deduplication for LLM calls to reduce quota usage
"""
import logging
import json
import hashlib
import time
import threading
from typing import Dict, Any, Optional, Callable
import os

logger = logging.getLogger(__name__)

# Try to import Redis, fall back to in-memory cache
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")

class LLMCache:
    """Cache for LLM responses with singleflight deduplication"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}  # Fallback in-memory cache
        self.singleflight_locks = {}  # Thread locks for singleflight
        self.lock_cleanup_time = 0
        
        # Configuration
        self.cache_ttl = int(os.getenv("LLM_CACHE_TTL_SEC", "300"))  # 5 minutes default
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Initialize Redis if available
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info(f"✅ Redis cache connected: {self.redis_url}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using in-memory cache")
                self.redis_client = None
        else:
            logger.info("Using in-memory cache (Redis not available)")
    
    def _get_cache_key(self, card_version: str, context_hash: str) -> str:
        """Generate cache key from card version and context hash"""
        key_data = f"{card_version}:{context_hash}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def _get_singleflight_key(self, cache_key: str) -> str:
        """Generate singleflight lock key"""
        return f"sf:{cache_key}"
    
    def _cleanup_old_locks(self):
        """Clean up old singleflight locks"""
        current_time = time.time()
        if current_time - self.lock_cleanup_time < 60:  # Cleanup every minute
            return
        
        self.lock_cleanup_time = current_time
        expired_locks = []
        
        for lock_key, lock_data in self.singleflight_locks.items():
            if current_time - lock_data['created'] > 30:  # 30 second timeout
                expired_locks.append(lock_key)
        
        for lock_key in expired_locks:
            try:
                lock_data = self.singleflight_locks.get(lock_key)
                if lock_data:
                    lock = lock_data['lock']
                    # Only release if we can acquire it (meaning it's not being used)
                    if lock.acquire(blocking=False):
                        lock.release()
                    del self.singleflight_locks[lock_key]
            except Exception as e:
                # Log the error but don't fail the cleanup
                logger.debug(f"Error cleaning up lock {lock_key}: {e}")
                # Force remove the lock entry even if we can't clean it properly
                self.singleflight_locks.pop(lock_key, None)
    
    def get(self, card_version: str, context_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        cache_key = self._get_cache_key(card_version, context_hash)
        
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    result = json.loads(cached_data)
                    logger.debug(f"Cache hit (Redis): {cache_key[:8]}...")
                    return result
            else:
                # In-memory cache
                if cache_key in self.memory_cache:
                    cached_data = self.memory_cache[cache_key]
                    if time.time() - cached_data['timestamp'] < self.cache_ttl:
                        logger.debug(f"Cache hit (memory): {cache_key[:8]}...")
                        return cached_data['data']
                    else:
                        # Expired
                        del self.memory_cache[cache_key]
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        
        return None
    
    def set(self, card_version: str, context_hash: str, data: Dict[str, Any]) -> None:
        """Set cached result"""
        cache_key = self._get_cache_key(card_version, context_hash)
        
        try:
            if self.redis_client:
                self.redis_client.setex(
                    cache_key, 
                    self.cache_ttl, 
                    json.dumps(data)
                )
                logger.debug(f"Cache set (Redis): {cache_key[:8]}...")
            else:
                # In-memory cache
                self.memory_cache[cache_key] = {
                    'data': data,
                    'timestamp': time.time()
                }
                logger.debug(f"Cache set (memory): {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def singleflight(self, card_version: str, context_hash: str, func: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute function with singleflight deduplication
        Multiple concurrent calls with same key will only execute once
        """
        cache_key = self._get_cache_key(card_version, context_hash)
        sf_key = self._get_singleflight_key(cache_key)
        
        # Clean up old locks periodically
        self._cleanup_old_locks()
        
        # Check cache first
        cached_result = self.get(card_version, context_hash)
        if cached_result:
            return cached_result
        
        # Acquire singleflight lock
        lock_acquired = False
        try:
            if sf_key not in self.singleflight_locks:
                self.singleflight_locks[sf_key] = {
                    'lock': threading.Lock(),
                    'created': time.time()
                }
            
            lock = self.singleflight_locks[sf_key]['lock']
            lock_acquired = lock.acquire(blocking=False)
            
            if lock_acquired:
                # We got the lock, execute the function
                logger.debug(f"Singleflight executing: {cache_key[:8]}...")
                result = func()
                
                # Cache the result
                self.set(card_version, context_hash, result)
                
                # Release lock
                lock.release()
                del self.singleflight_locks[sf_key]
                
                return result
            else:
                # Someone else is executing, wait for result
                logger.debug(f"Singleflight waiting: {cache_key[:8]}...")
                
                # Wait for the other thread to finish
                max_wait = 30  # 30 second timeout
                wait_start = time.time()
                
                while time.time() - wait_start < max_wait:
                    # Check if result is now cached
                    cached_result = self.get(card_version, context_hash)
                    if cached_result:
                        return cached_result
                    
                    time.sleep(0.1)  # Wait 100ms
                
                # Timeout - execute anyway
                logger.warning(f"Singleflight timeout: {cache_key[:8]}...")
                result = func()
                self.set(card_version, context_hash, result)
                return result
                
        except Exception as e:
            logger.error(f"Singleflight error: {e}")
            # Fallback to direct execution
            result = func()
            self.set(card_version, context_hash, result)
            return result
        finally:
            if lock_acquired and sf_key in self.singleflight_locks:
                try:
                    self.singleflight_locks[sf_key]['lock'].release()
                    del self.singleflight_locks[sf_key]
                except:
                    pass
    
    def invalidate(self, card_version: str, context_hash: str) -> None:
        """Invalidate cached result"""
        cache_key = self._get_cache_key(card_version, context_hash)
        
        try:
            if self.redis_client:
                self.redis_client.delete(cache_key)
            else:
                self.memory_cache.pop(cache_key, None)
            logger.debug(f"Cache invalidated: {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
    
    def clear(self) -> None:
        """Clear all cached data"""
        try:
            if self.redis_client:
                # Clear all keys with our prefix (this is a simple approach)
                keys = self.redis_client.keys("llm_cache:*")
                if keys:
                    self.redis_client.delete(*keys)
            else:
                self.memory_cache.clear()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
    
    def cleanup(self):
        """Clean up all resources - call this when shutting down"""
        try:
            # Clean up all remaining locks
            for lock_key, lock_data in list(self.singleflight_locks.items()):
                try:
                    lock = lock_data['lock']
                    if lock.acquire(blocking=False):
                        lock.release()
                except:
                    pass
                del self.singleflight_locks[lock_key]
            
            # Clear the dictionary
            self.singleflight_locks.clear()
            logger.info("LLM Cache cleanup completed")
        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")


# Global cache instance
llm_cache = LLMCache()
