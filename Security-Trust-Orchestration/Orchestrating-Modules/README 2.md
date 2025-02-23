# Orchestrating Modules

Core orchestration system for managing multiple AI agents and their interactions.

## Components

### agent_orchestrator.py
Main orchestrator service that:
- Initializes and manages agent instances
- Handles real-time event streaming
- Manages inter-agent communication
- Provides REST API endpoints

### messaging_and_orchestrating.py
Handles:
- Message routing between agents
- Event stream processing
- Communication protocols

## API Endpoints

### Streaming Endpoints
- `/stream/cognitive`: Cognitive processing events
- `/stream/browser`: Browser automation events
- `/stream/security-events`: Security monitoring
- `/stream/agent-metrics`: Agent performance metrics
- `/stream/inter-agent`: Inter-agent communication

### Data Endpoints
- `/decoded/security-events`: Decoded security events
- `/decoded/agent-metrics`: Decoded agent metrics
- `/receive/inter-agent`: Inter-agent message receipt

## Usage

Start the orchestrator:
bash
python agent_orchestrator.py

Default port is 8080. Configure through environment variables.