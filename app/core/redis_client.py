"""
Redis Client Configuration
Handles Redis Cloud connections with backward compatibility
"""

import redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
from typing import Optional
import logging

from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis Cloud client wrapper with connection pooling"""
    
    def __init__(self):
        """Initialize Redis Cloud connection"""
        self._client = None
        self._initialize()
    
    def _initialize(self):
        """Create Redis Cloud connection"""
        try:
            # Use redis.from_url which handles SSL automatically based on URL scheme
            self._client = redis.from_url(
                settings.redis_url,
                decode_responses=settings.REDIS_DECODE_RESPONSES,
                max_connections=50,
                socket_connect_timeout=10,
                socket_timeout=10,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            # Test connection
            ping_response = self._client.ping()
            
            if ping_response:
                logger.info(
                    f"✓ Redis Cloud connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}"
                )
                logger.info(f"  SSL: {settings.REDIS_SSL}")
                logger.info(f"  Database: {settings.REDIS_DB}")
            
        except RedisConnectionError as e:
            logger.error(f"✗ Redis Cloud connection failed: {e}")
            logger.warning("Session management will be disabled")
            logger.error("Check your Redis Cloud credentials in .env file")
            self._client = None
        except Exception as e:
            logger.error(f"✗ Redis configuration error: {e}")
            logger.info("Retrying with basic configuration...")
            # Fallback to basic connection without advanced features
            try:
                self._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    username=settings.REDIS_USERNAME,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=settings.REDIS_DECODE_RESPONSES,
                )
                self._client.ping()
                logger.info("✓ Redis connected with basic configuration")
            except Exception as retry_error:
                logger.error(f"✗ Redis fallback failed: {retry_error}")
                self._client = None
    
    def get_client(self) -> Optional[redis.Redis]:
        """Get Redis client instance"""
        return self._client
    
    def is_available(self) -> bool:
        """Check if Redis Cloud is available"""
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except RedisError as e:
            logger.error(f"Redis Cloud health check failed: {e}")
            return False
    
    def close(self):
        """Close Redis Cloud connections"""
        if self._client:
            self._client.close()
            logger.info("Redis Cloud connections closed")
    
    def get_info(self) -> dict:
        """Get Redis Cloud server information"""
        if not self._client:
            return {"error": "Redis not connected"}
        
        try:
            info = self._client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_connections_received": info.get("total_connections_received"),
                "total_commands_processed": info.get("total_commands_processed"),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec"),
            }
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {"error": str(e)}


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> Optional[redis.Redis]:
    """Dependency to get Redis client"""
    return redis_client.get_client()