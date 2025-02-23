from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Callable
from enum import Enum
import asyncio
import json
from collections import defaultdict

class MessageType(Enum):
    """
    Defines different types of messages that can be exchanged between agents.
    
    Attributes:
        TRUST_UPDATE: Updates to agent trust scores
        AGENT_RESULT: Results from agent operations
        SYSTEM_ALERT: System-level alerts and notifications
        AGENT_HEARTBEAT: Periodic agent health checks
        SCHEMA_UPDATE: Updates to interaction schemas
    """
    TRUST_UPDATE = "trust_update"
    AGENT_RESULT = "agent_result"
    SYSTEM_ALERT = "system_alert"
    AGENT_HEARTBEAT = "agent_heartbeat"
    SCHEMA_UPDATE = "schema_update"

@dataclass
class SecureMessage:
    """
    Represents a secure message exchanged between agents.
    
    Attributes:
        message_id (str): Unique identifier for the message
        sender_id (str): ID of the sending agent
        recipient_id (str): ID of the receiving agent
        message_type (MessageType): Type of message being sent
        payload (Any): Actual message content
        timestamp (datetime): When the message was created
        signature (str): Digital signature for message verification
        encryption_key_id (str): ID of the key used for encryption
        priority (int): Message priority (0 is lowest)
        ttl (int): Time-to-live in seconds (default 10 minutes)
    """
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    payload: Any
    timestamp: datetime
    signature: str
    encryption_key_id: str
    priority: int = 0
    ttl: int = 600  # Time-to-live in seconds

class MessageBroker:
    """
    Handles secure message exchange between agents with priority queuing and rate limiting.
    
    This broker ensures secure communication by:
    - Verifying message signatures
    - Encrypting message payloads
    - Implementing rate limiting
    - Managing message priorities
    - Handling message expiration
    
    Attributes:
        security: Security protocol instance for encryption/verification
        storage: Persistent storage instance
        subscribers (Dict[str, Set[Callable]]): Topic subscribers
        message_history (Dict[str, List[SecureMessage]]): Message history by type
        rate_limits (Dict[str, int]): Rate limiting counters
        max_rate (int): Maximum messages per second per sender
        message_queue (PriorityQueue): Priority-based message queue
    """
    
    def __init__(self, security, storage):
        """
        Initializes the message broker with security and storage handlers.
        
        Args:
            security: Security protocol instance
            storage: Persistent storage instance
        """
        self.security = security
        self.storage = storage
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self.message_history: Dict[str, List[SecureMessage]] = defaultdict(list)
        self.rate_limits: Dict[str, int] = defaultdict(int)
        self.max_rate = 100  # messages per second
        self.message_queue = asyncio.PriorityQueue()
        
    async def publish(self, topic: str, message: SecureMessage):
        """
        Publishes a message to a topic with security checks.
        
        Args:
            topic (str): Topic to publish to
            message (SecureMessage): Message to publish
            
        Raises:
            ValueError: If rate limit exceeded or invalid signature
            Exception: For other processing errors
            
        Notes:
            - Implements rate limiting per sender
            - Verifies message signatures
            - Encrypts message payload
            - Handles prioritized queueing
        """
        try:
            if not self._check_rate_limit(message.sender_id):
                raise ValueError("Rate limit exceeded")
            if not self.security.verify_signature(message.payload, message.signature):
                raise ValueError("Invalid message signature")
            encrypted_payload = self.security.encrypt_message(message.payload)
            await self.message_queue.put(
                (message.priority, encrypted_payload, message)
            )
            # Process message queue
            await self._process_message_queue()
        except Exception as e:
            await self._handle_error(e, message)

    async def _process_message_queue(self):
        """
        Processes messages in priority order from the queue.
        
        Notes:
            - Checks message TTL before processing
            - Stores messages in history
            - Notifies subscribers
            - Handles message completion
        """
        while not self.message_queue.empty():
            priority, encrypted_payload, message = await self.message_queue.get()
            if self._is_message_expired(message):
                continue
            self.message_history[message.message_type.value].append(message)
            await self._notify_subscribers(message)
            self.message_queue.task_done()

    def subscribe(self, topic: str, callback: Callable[[SecureMessage], None]):
        """
        Subscribes to a topic with unsubscribe capability.
        
        Args:
            topic (str): Topic to subscribe to
            callback (Callable): Function to call for messages
            
        Returns:
            Callable: Unsubscribe function
            
        Notes:
            Returns a function that can be called to unsubscribe
        """
        self.subscribers[topic].add(callback)
        
        def unsubscribe():
            self.subscribers[topic].discard(callback)
        return unsubscribe

    async def _notify_subscribers(self, message: SecureMessage):
        """
        Notifies all subscribers of a message.
        
        Args:
            message (SecureMessage): Message to notify about
            
        Notes:
            - Creates separate task for each subscriber
            - Handles subscriber errors independently
        """
        topic = message.message_type.value
        for subscriber in self.subscribers[topic]:
            try:
                await asyncio.create_task(subscriber(message))
            except Exception as e:
                print(f"Error delivering to subscriber: {e}")

    def _check_rate_limit(self, sender_id: str) -> bool:
        """
        Implements rate limiting for senders.
        Args:
            sender_id (str): ID of message sender
        Returns:
            bool: True if within rate limit, False otherwise
        Notes:
            Limits based on max_rate messages per second
        """
        current_rate = self.rate_limits[sender_id]
        if current_rate >= self.max_rate:
            return False
        self.rate_limits[sender_id] += 1
        return True

    def _is_message_expired(self, message: SecureMessage) -> bool:
        """
        Checks if a message has expired based on TTL.
        
        Args:
            message (SecureMessage): Message to check
            
        Returns:
            bool: True if message has expired, False otherwise
            
        Notes:
            Uses message timestamp and TTL for expiration check
        """
        age = (datetime.now() - message.timestamp).total_seconds()
        return age > message.ttl

    async def _handle_error(self, error: Exception, message: SecureMessage):
        """
        Handles errors in message processing.
        
        Args:
            error (Exception): Error that occurred
            message (SecureMessage): Message that caused error
            
        Notes:
            Creates system alert message for errors
        """
        error_msg = SecureMessage(
            message_id=f"error_{message.message_id}",
            sender_id="system",
            recipient_id=message.sender_id,
            message_type=MessageType.SYSTEM_ALERT,
            payload={"error": str(error), "original_message": message}
        )
        # Additional error handling logic here