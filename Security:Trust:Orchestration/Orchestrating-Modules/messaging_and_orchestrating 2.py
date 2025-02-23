"""
Enhanced Agent Communication Demo with Inter-Agent Messaging and Global Context
"""

import asyncio
from datetime import datetime
import json
import random
from typing import Dict, Any, List, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from cryptography.fernet import Fernet
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class MessageType(Enum):
    CHAT = "chat"  # Agent to agent chat
    QUERY = "query"  # Information request
    RESPONSE = "response"  # Information response
    UPDATE = "update"  # Status update
    HEARTBEAT = "heartbeat"  # System heartbeat

@dataclass
class SecureMessage:
    message_id: str
    sender_id: str
    recipient_id: str
    message_type: MessageType
    payload: Any
    timestamp: datetime
    conversation_id: str = None  # For tracking message threads

class Topic:
    """Topics that agents can discuss or know about"""
    WEATHER = "weather"
    TRAFFIC = "traffic"
    NEWS = "news"
    EVENTS = "events"
    SYSTEM = "system"

class Agent:
    def __init__(self, agent_id: str, topics: List[str]):
        self.agent_id = agent_id
        self.knowledge = {topic: [] for topic in topics}  # What the agent knows about each topic
        self.connections: Set[str] = set()  # Other agents this agent knows
        self.status = "active"
        self.last_update = datetime.now()
        
        # Initialize random knowledge
        for topic in topics:
            self._generate_knowledge(topic)
    
    def _generate_knowledge(self, topic: str):
        """Generate some random knowledge about a topic"""
        if topic == Topic.WEATHER:
            self.knowledge[topic] = [
                f"Temperature is {random.randint(60, 80)}°F",
                f"Humidity is {random.randint(30, 70)}%",
                random.choice(["Sunny", "Cloudy", "Rainy", "Partly cloudy"])
            ]
        elif topic == Topic.TRAFFIC:
            self.knowledge[topic] = [
                f"Highway congestion: {random.randint(0, 100)}%",
                f"Average speed: {random.randint(30, 70)} mph",
                random.choice(["Accident reported", "Construction ahead", "Clear roads", "Heavy traffic"])
            ]
        elif topic == Topic.NEWS:
            self.knowledge[topic] = [
                "Breaking news story",
                "Local event coverage",
                "Technology update"
            ]
        elif topic == Topic.EVENTS:
            self.knowledge[topic] = [
                "Conference scheduled",
                "Meeting planned",
                "System maintenance"
            ]
            
    async def chat_with_agent(self, other_id: str, broker, topic: str):
        """Initiate a conversation with another agent about a topic"""
        if topic in self.knowledge:
            conversation_id = str(uuid.uuid4())
            message = SecureMessage(
                message_id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                recipient_id=other_id,
                message_type=MessageType.CHAT,
                payload={
                    "topic": topic,
                    "content": f"What do you know about {topic}?",
                    "known_info": self.knowledge[topic][0]  # Share one piece of knowledge
                },
                timestamp=datetime.now(),
                conversation_id=conversation_id
            )
            logger.info(f"\n🗣️ {self.agent_id} asks {other_id} about {topic}")
            await broker.publish("chat", message)

    async def handle_message(self, message: SecureMessage, broker):
        """Handle incoming messages from other agents"""
        if message.message_type == MessageType.CHAT:
            # Respond to chat with own knowledge
            topic = message.payload["topic"]
            if topic in self.knowledge:
                response = SecureMessage(
                    message_id=str(uuid.uuid4()),
                    sender_id=self.agent_id,
                    recipient_id=message.sender_id,
                    message_type=MessageType.RESPONSE,
                    payload={
                        "topic": topic,
                        "content": f"Here's what I know about {topic}",
                        "knowledge": self.knowledge[topic],
                        "original_info": message.payload["known_info"]
                    },
                    timestamp=datetime.now(),
                    conversation_id=message.conversation_id
                )
                logger.info(f"\n💭 {self.agent_id} responds to {message.sender_id} about {topic}")
                await broker.publish("chat", response)

    async def update_knowledge(self, topic: str, new_info: str):
        """Update agent's knowledge about a topic"""
        if topic in self.knowledge:
            self.knowledge[topic].append(new_info)
            self.last_update = datetime.now()

    async def run(self, broker):
        """Main agent loop"""
        while True:
            # Randomly chat with other agents
            if self.connections:
                other_agent = random.choice(list(self.connections))
                topic = random.choice(list(self.knowledge.keys()))
                await self.chat_with_agent(other_agent, broker, topic)
            
            # Update orchestrator with status
            status_update = SecureMessage(
                message_id=str(uuid.uuid4()),
                sender_id=self.agent_id,
                recipient_id="orchestrator",
                message_type=MessageType.UPDATE,
                payload={
                    "status": self.status,
                    "knowledge_size": {k: len(v) for k, v in self.knowledge.items()},
                    "connections": list(self.connections),
                    "last_update": self.last_update.isoformat()
                },
                timestamp=datetime.now()
            )
            await broker.publish("status", status_update)
            
            await asyncio.sleep(random.uniform(2, 5))

class Orchestrator:
    def __init__(self):
        self.global_context = {
            "agents": {},
            "topics": defaultdict(list),
            "conversations": defaultdict(list),
            "network_stats": {
                "total_messages": 0,
                "active_conversations": 0
            }
        }
    
    def update_global_context(self, message: SecureMessage):
        """Update global context based on agent messages"""
        # Update agent status
        if message.message_type == MessageType.UPDATE:
            self.global_context["agents"][message.sender_id] = message.payload
        
        # Track conversations
        elif message.message_type in [MessageType.CHAT, MessageType.RESPONSE]:
            topic = message.payload["topic"]
            self.global_context["topics"][topic].append({
                "agent": message.sender_id,
                "knowledge": message.payload.get("knowledge", [message.payload["known_info"]])
            })
            
            if message.conversation_id:
                self.global_context["conversations"][message.conversation_id].append({
                    "from": message.sender_id,
                    "to": message.recipient_id,
                    "type": message.message_type.value,
                    "timestamp": message.timestamp
                })
        
        self.global_context["network_stats"]["total_messages"] += 1
        self.global_context["network_stats"]["active_conversations"] = len(
            [c for c in self.global_context["conversations"].values() 
             if (datetime.now() - c[-1]["timestamp"]).seconds < 10]
        )
        
        # Log global context updates
        self._log_context_update(message)
    
    def _log_context_update(self, message: SecureMessage):
        """Log interesting context updates"""
        logger.info("\n📊 Global Context Update:")
        logger.info(f"Active Agents: {len(self.global_context['agents'])}")
        logger.info(f"Topics being discussed: {list(self.global_context['topics'].keys())}")
        logger.info(f"Total messages: {self.global_context['network_stats']['total_messages']}")
        logger.info(f"Active conversations: {self.global_context['network_stats']['active_conversations']}")

class MessageBroker:
    def __init__(self):
        self.subscribers = defaultdict(list)
        self.message_queue = asyncio.Queue()
    
    async def publish(self, topic: str, message: SecureMessage):
        await self.message_queue.put((topic, message))
    
    def subscribe(self, topic: str, callback):
        self.subscribers[topic].append(callback)
    
    async def start(self):
        while True:
            topic, message = await self.message_queue.get()
            for callback in self.subscribers[topic]:
                await callback(message)
            self.message_queue.task_done()

async def main():
    # Initialize components
    broker = MessageBroker()
    orchestrator = Orchestrator()
    
    # Create agents with different knowledge domains
    agents = [
        Agent(f"WeatherAgent_{i}", [Topic.WEATHER, Topic.NEWS]) for i in range(2)
    ] + [
        Agent(f"TrafficAgent_{i}", [Topic.TRAFFIC, Topic.EVENTS]) for i in range(2)
    ]
    
    # Connect agents to each other
    for agent in agents:
        agent.connections = {a.agent_id for a in agents if a.agent_id != agent.agent_id}
    
    # Set up message handling
    for agent in agents:
        broker.subscribe("chat", agent.handle_message)
    broker.subscribe("chat", orchestrator.update_global_context)
    broker.subscribe("status", orchestrator.update_global_context)
    
    # Start the broker
    broker_task = asyncio.create_task(broker.start())
    
    # Start agent tasks
    agent_tasks = [asyncio.create_task(agent.run(broker)) for agent in agents]
    
    # Run for 60 seconds
    try:
        await asyncio.sleep(60)
    finally:
        broker_task.cancel()
        for task in agent_tasks:
            task.cancel()
        
        try:
            await broker_task
            await asyncio.gather(*agent_tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    print("Starting Enhanced Agent Communication Demo...")
    print("Running for 60 seconds...")
    asyncio.run(main())