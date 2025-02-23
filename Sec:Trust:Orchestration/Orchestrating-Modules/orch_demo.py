"""
Orchestrator Demo Script

This script demonstrates the agent orchestrator functionality by simulating
multiple agent activities and streaming their data through various endpoints.

Features:
    - Chain of thought processing
    - Browser action simulation
    - Agent metrics and security events
    - Inter-agent communications
    - Real-time data streaming
"""

import logging
import random
import threading
import time
from datetime import datetime

from agent_orchestrator import (
    SecurityProtocol, 
    cognitive_stream_queue,
    browser_stream_queue,
    security_events_queue,
    agent_metrics_queue,
    inter_agent_queue,
    run_server,
    log_security_event,
    log_agent_metrics
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class OrchestratorDemo:
    """Demonstration of agent orchestration and real-time streaming.

    This class simulates various agent activities (cognitive processing,
    browser actions, agent metrics, security events, and inter-agent
    communications) and sends them to the orchestrator's queues.
    """

    def __init__(self, num_agents: int = 3):
        """Initialize the OrchestratorDemo.

        Args:
            num_agents (int): Number of simulated agents to create.
        """
        self.security = SecurityProtocol()  # A single SecurityProtocol instance for encryption/decryption
        self.agent_ids = [f"agent_{i}" for i in range(num_agents)]
        self.running = True
        logger.info(f"Initialized demo with {num_agents} agents")
        
    def generate_cognitive_stream(self):
        """Simulate cognitive processing steps.

        This method runs in a loop to put "thought" dictionaries into
        the `cognitive_stream_queue`. Each dictionary includes an agent ID,
        a random step name, and a timestamp. The loop ends when `self.running`
        is set to False.
        """
        steps = [
            "Analyzing input parameters...",
            "Evaluating context...",
            "Processing decision tree...",
            "Generating response...",
        ]
        while self.running:
            thought = {
                "type": "THOUGHT",
                "content": random.choice(steps),
                "timestamp": datetime.now().isoformat(),
                "agent_id": random.choice(self.agent_ids)
            }
            cognitive_stream_queue.put(thought)
            time.sleep(random.uniform(1.0, 2.0))

    def simulate_browser_actions(self):
        """Simulate UI/browser actions.

        This method runs in a loop to put "action" dictionaries into
        the `browser_stream_queue`. Each action has a random type (e.g.
        button click, scrolling) and a timestamp. Loop ends when
        `self.running` is False.
        """
        actions = [
            "Clicking search button",
            "Entering text in input field",
            "Scrolling page",
        ]
        while self.running:
            action = {
                "type": "ACTION",
                "content": random.choice(actions),
                "timestamp": datetime.now().isoformat(),
                "agent_id": random.choice(self.agent_ids)
            }
            browser_stream_queue.put(action)
            time.sleep(random.uniform(1.5, 3.0))

    def generate_agent_metrics(self):
        """Generate and log agent metrics and security events.

        This method creates performance metrics (e.g. response time,
        success rate) for each agent, encrypts them via `log_agent_metrics`,
        and occasionally creates security events via `log_security_event`.
        It loops until `self.running` is False.
        """
        while self.running:
            for agent_id in self.agent_ids:
                log_agent_metrics(self.security, {
                    "agent_id": agent_id,
                    "trust_score": round(random.random(), 2),
                    "performance_metrics": {
                        "response_time": random.randint(50, 200),
                        "success_rate": round(random.random(), 2),
                    }
                })
                # 30% chance to log a security event
                if random.random() < 0.3:
                    log_security_event(self.security, {
                        "event_type": "access_attempt",
                        "agent_id": agent_id,
                        "severity": random.choice(["low", "medium", "high"]),
                        "details": "Simulated security event",
                    })
            time.sleep(random.uniform(2, 5))

    def simulate_agent_conversations(self):
        """Simulate inter-agent communications.

        This method runs in a loop to randomly pick two agents (sender,
        receiver) and generate a communication message about a topic
        (e.g. task delegation). Each message is placed into the
        `inter_agent_queue`.
        """
        topics = ["task_delegation", "status_update", "error_report"]
        while self.running:
            sender, receiver = random.sample(self.agent_ids, 2)
            message = {
                "type": "AGENT_COMMUNICATION",
                "sender": sender,
                "receiver": receiver,
                "topic": random.choice(topics),
                "content": "Hello from " + sender,
                "timestamp": datetime.now().isoformat()
            }
            inter_agent_queue.put(message)
            time.sleep(random.uniform(1, 3))

    def run_demo(self, port: int = 8080):
        """Start all simulation threads and run the orchestrator server.

        This method creates and starts threads for:
          - generate_cognitive_stream
          - simulate_browser_actions
          - generate_agent_metrics
          - simulate_agent_conversations

        Then it calls `run_server` with the same SecurityProtocol instance
        to ensure encryption/decryption consistency.

        Args:
            port (int): The port on which to run the Flask server.
        """
        threads = [
            threading.Thread(target=self.generate_cognitive_stream),
            threading.Thread(target=self.simulate_browser_actions),
            threading.Thread(target=self.generate_agent_metrics),
            threading.Thread(target=self.simulate_agent_conversations),
        ]
        for t in threads:
            t.daemon = True
            t.start()

        run_server(port, self.security)

def main():
    """Entry point for the Orchestrator Demo.

    Prints information about available endpoints, starts the OrchestratorDemo,
    and then runs the event simulation + Flask server on the specified port.
    """
    print("\n=== Agent Orchestrator Demo ===")
    print("Starting all endpoints and simulations...")
    print("SSE endpoints:")
    print("  /stream/cognitive, /stream/browser, /stream/security-events, /stream/agent-metrics, /stream/inter-agent")
    print("Decoded endpoints:")
    print("  /decoded/security-events, /decoded/agent-metrics")
    print("Press Ctrl+C to stop.\n")

    demo = OrchestratorDemo(num_agents=3)
    demo.run_demo(port=8080)

if __name__ == "__main__":
    main()
