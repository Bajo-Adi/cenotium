import redis
import json
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

'''class TransactionType(Enum):
    FLIGHT_BOOKING = "flight_booking"
    HOTEL_BOOKING = "hotel_booking"
    CAR_RENTAL = "car_rental"
    SCUBA_BOOKING = "scuba_booking"
    SEARCH_QUERY = "search_query"
    AGENT_COMMUNICATION = "agent_communication"

@dataclass
class Transaction:
    """Represents a single transaction in the system"""
    transaction_id: str
    agent_id: str
    transaction_type: TransactionType
    timestamp: datetime
    status: str  # 'pending', 'completed', 'failed'
    success: bool
    duration_ms: int
    details: Dict[str, Any]
    partner_agent_id: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class AgentMetrics:
    """Performance metrics for an agent"""
    agent_id: str
    timestamp: datetime
    metrics: Dict[str, float] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {
                # Response Time Metrics
                'avg_response_time_ms': 0.0,
                'p95_response_time_ms': 0.0,
                'p99_response_time_ms': 0.0,
                
                # Success Rate Metrics
                'success_rate': 0.0,
                'error_rate': 0.0,
                'timeout_rate': 0.0,
                
                # Throughput Metrics
                'transactions_per_second': 0.0,
                'requests_processed': 0.0,
                
                # Quality Metrics
                'accuracy_score': 0.0,
                'relevance_score': 0.0,
                
                # Resource Metrics
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                
                # Trust Metrics
                'trust_score': 0.0,
                'reliability_score': 0.0
            }
'''
class PersistentStorage:
    """
    Manages persistent storage of agent data, trust scores, and metrics using Redis.
    
    This class provides an interface for storing and retrieving various types of agent-related
    data with automatic serialization/deserialization and TTL management.
    
    Attributes:
        redis_client (Redis): Connection to Redis server
    """
    
    def __init__(self, host='localhost', port=6379, db=0):
        """
        Initializes Redis connection with specified parameters.
        
        Args:
            host (str): Redis host address
            port (int): Redis port number
            db (int): Redis database number
        """
        self.redis_client = redis.Redis(host=host, port=port, db=db)
        
    def store_agent_data(self, agent_id: str, data: dict):
        """
        Stores agent-specific data in Redis with JSON serialization.
        
        Args:
            agent_id (str): Unique identifier for the agent
            data (dict): Agent data to store
            
        Raises:
            RedisError: If storage operation fails
        """
        key = f"agent:{agent_id}"
        serialized_data = {k: json.dumps(v) for k, v in data.items()}
        self.redis_client.hset(key, mapping=serialized_data)
        
    def get_agent_data(self, agent_id: str) -> Dict[str, Any]:
        """
        Retrieves and deserializes agent data from Redis.
        
        Args:
            agent_id (str): Unique identifier for the agent
            
        Returns:
            Dict[str, Any]: Agent data dictionary, empty if not found
            
        Raises:
            RedisError: If retrieval operation fails
        """
        key = f"agent:{agent_id}"
        data = self.redis_client.hgetall(key)
        return {k.decode(): json.loads(v.decode()) for k, v in data.items()}
    
    def store_trust_score(self, agent_id: str, trust_score: float):
        """
        Stores agent trust score in Redis.
        
        Args:
            agent_id (str): Unique identifier for the agent
            trust_score (float): Trust score value between 0 and 1
            
        Raises:
            ValueError: If trust_score is not between 0 and 1
        """
        if not 0 <= trust_score <= 1:
            raise ValueError("Trust score must be between 0 and 1")
            
        key = f"trust:{agent_id}"
        self.redis_client.set(key, str(trust_score))
        
    def get_trust_score(self, agent_id: str) -> float:
        """
        Retrieves agent trust score from Redis.
        
        Args:
            agent_id (str): Unique identifier for the agent
            
        Returns:
            float: Trust score value, 0.0 if not found
        """
        key = f"trust:{agent_id}"
        score = self.redis_client.get(key)
        return float(score) if score else 0.0

    def store_transaction(self, transaction_id: str, data: dict):
        """
        Stores transaction data with automatic expiration (TTL).
        
        Args:
            transaction_id (str): Unique transaction identifier
            data (dict): Transaction data to store
            
        Notes:
            Data automatically expires after 10 minutes (600 seconds)
        """
        key = f"transaction:{transaction_id}"
        self.redis_client.setex(
            key,
            600,  # 10 mins TTL
            json.dumps(data)
        )

    def get_transaction(self, transaction_id: str) -> Optional[dict]:
        """
        Retrieves transaction data if not expired.
        
        Args:
            transaction_id (str): Unique transaction identifier
            
        Returns:
            Optional[dict]: Transaction data if found and not expired, None otherwise
        """
        key = f"transaction:{transaction_id}"
        data = self.redis_client.get(key)
        return json.loads(data) if data else None

    def store_agent_metrics(self, agent_id: str, metrics: dict):
        """
        Stores agent performance metrics with time-based scoring.
        
        Args:
            agent_id (str): Unique identifier for the agent
            metrics (dict): Performance metrics to store
            
        Notes:
            - Uses Redis sorted sets for time-series data
            - Automatically removes metrics older than 24 hours
        """
        key = f"metrics:{agent_id}"
        self.redis_client.zadd(
            key,
            {json.dumps(metrics): datetime.now().timestamp()}
        )
        # Keep only last 24 hours of metrics
        self.redis_client.zremrangebyscore(
            key,
            '-inf',
            datetime.now().timestamp() - 86400
        )