# Security-Trust Modules

Core security and trust management system for the agent orchestration platform. This module handles encryption, message security, trust scoring, and secure data persistence.

## Components

### security_protocol.py
Handles cryptographic operations and message security:
- Fernet symmetric encryption/decryption
- HMAC-SHA256 message signing
- Key rotation and management
- Signature verification

### secure_message_broker.py
Manages secure inter-agent communication:
- Priority-based message queuing
- Rate limiting
- Message expiration handling
- Publish/subscribe system
- Error handling and alerts

### global_trust_core.py
Implements trust scoring and ranking system:
- Modified EigenTrust algorithm
- Temporal decay for trust scores
- Performance-based ranking
- Network-wide trust updates

### persistent_storage.py
Handles secure data persistence using Redis:
- Agent data storage
- Trust score management
- Transaction history
- Performance metrics
- Time-series data management

### Security Protocol
python
from security_protocol import SecurityProtocol
Initialize security protocol
security = SecurityProtocol()
Encrypt and sign a message
encrypted = security.encrypt_message({"data": "sensitive"})
signature = security.sign_message({"data": "sensitive"})
Verify and decrypt
if security.verify_signature(message, signature):
decrypted = security.decrypt_message(encrypted)
Broker
python
from secure_message_broker import MessageBroker, SecureMessage
Initialize broker
broker = MessageBroker(security, storage)
Subscribe to messages
async def handle_message(message):
print(f"Received: {message}")
unsubscribe = broker.subscribe("trust_update", handle_message)
Publish message
await broker.publish("trust_update", secure_message)
Management
python
from global_trust_core import GlobalTrustCore
trust_core = GlobalTrustCore()
Calculate trust score
score = trust_core.calculate_trust_score(
agent_id="agent1",
transaction_history=[...]
)
Update network trust
updated_scores = trust_core.update_trust_network(current_scores)
Storage
python
from persistent_storage import PersistentStorage
storage = PersistentStorage(host='localhost', port=6379)
Store agent data
storage.store_agent_data("agent1", {"trust_score": 0.95})
Retrieve data
agent_data = storage.get_agent_data("agent1")

## Configuration

Key configuration parameters:

- Trust calculation:
  - `alpha`: PageRank damping factor (default: 0.85)
  - `trust_threshold`: Minimum trust score (default: 0.1)
  - `max_iterations`: Maximum power iterations (default: 100)
  - `time_decay_factor`: Trust score decay rate (default: 0.95)

- Message broker:
  - `max_rate`: Maximum messages per second (default: 100)
  - `ttl`: Default message time-to-live (default: 600 seconds)

- Storage:
  - Redis connection parameters (host, port, db)
  - Data retention periods
  - Key expiration times

## Security Considerations

- All sensitive data is encrypted at rest and in transit
- Messages are signed and verified to prevent tampering
- Regular key rotation is implemented
- Rate limiting prevents DoS attacks
- Trust scores include temporal decay
- Secure storage with TTL enforcement
- Error handling with secure logging

## Dependencies

- cryptography
- redis
- numpy
- asyncio
- json
- dataclasses