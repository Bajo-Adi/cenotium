# Agent Orchestration System

A distributed system for orchestrating multiple AI agents with cognitive, browser, and metrics capabilities. The system provides real-time event streaming and secure inter-agent communication.

## Features

- Multi-agent orchestration
- Real-time event streaming
- Secure inter-agent communication
- Browser automation capabilities
- Cognitive processing pipeline
- Metrics collection and monitoring
- Security event logging

## Architecture

The system consists of three main modules:

- Orchestrating-Modules: Core orchestration and agent management
- Messaging: Inter-agent communication system
- Security: Event monitoring and security protocols

## Getting Started

1. Install dependencies:
bash
pip install -r requirements.txt

2. Start the orchestrator:
python Orchestrating-Modules/agent_orchestrator.py

3. Access the endpoints:
- Cognitive Stream: http://localhost:8080/stream/cognitive
- Browser Stream: http://localhost:8080/stream/browser
- Security Events: http://localhost:8080/stream/security-events
- Agent Metrics: http://localhost:8080/stream/agent-metrics
- Inter-agent Communication: http://localhost:8080/stream/inter-agent

## Documentation

See individual module READMEs for detailed documentation:

- [Orchestrating-Modules](Orchestrating-Modules/README.md)
- [Messaging](Messaging/README.md)
- [Security](Security/README.md)