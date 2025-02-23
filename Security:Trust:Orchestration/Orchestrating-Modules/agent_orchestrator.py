"""
Agent Orchestrator with Security and Metrics Streaming

This module provides a Flask-based orchestrator for monitoring and managing agent communications.
It handles secure message exchange, metrics tracking, and real-time visualization of agent activities,
including:
    - Real-time stream monitoring via SSE (Server-Sent Events)
    - Secure message encryption and signing
    - Agent metrics and trust score tracking
    - Security event monitoring
    - Web-based visualization dashboard

Components:
    - SecurityProtocol: Handles encryption and signing
    - Stream Endpoints: Multiple SSE streams for different data types
    - Event Simulation: Test data generation
    - Decoding Helpers: Tools to decrypt and verify signatures
    - Web Dashboard: Real-time visualization
"""

import base64
import json
import logging
import queue
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, Response, jsonify
from flask_cors import CORS
from cryptography.fernet import Fernet, InvalidToken
import hmac
import hashlib
import requests
import sseclient
import cv2
from bs4 import BeautifulSoup
from flask import request

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_orchestrator.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app and enable CORS for all endpoints
app = Flask(__name__)
CORS(app)

# Queues for streaming data
cognitive_stream_queue = queue.Queue()   # For cognitive processing steps
browser_stream_queue = queue.Queue()     # For browser actions
security_events_queue = queue.Queue()    # For security events
agent_metrics_queue = queue.Queue()      # For agent metrics
inter_agent_queue = queue.Queue()        # For agent-to-agent communications

# Global reference to the SecurityProtocol (shared key used for encryption/decryption)
global_security_protocol: Optional["SecurityProtocol"] = None


class SecurityProtocol:
    """Handles encryption and message signing for secure communication.

    This class provides methods for:
        - Encrypting messages using Fernet (AES-128-CBC + HMAC)
        - Decrypting messages if valid
        - Signing and verifying message signatures with HMAC-SHA256

    Attributes:
        key (bytes): Current Fernet encryption key.
        cipher_suite (Fernet): Instance that manages encryption/decryption.
        trusted_keys (Dict[str, bytes]): Map of old keys used for historical messages.
        signing_key (bytes): Key used to generate/verify HMAC signatures.
    """

    def __init__(self):
        """Initializes a new SecurityProtocol with fresh encryption/signing keys."""
        self.key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
        self.trusted_keys = {}
        self.signing_key = b"demo-signing-key"

    def encrypt_message(self, message: dict) -> bytes:
        """Encrypts a dictionary message using Fernet.

        Args:
            message (dict): The message data to encrypt.

        Returns:
            bytes: The encrypted message bytes.

        Raises:
            ValueError: If the dictionary fails to serialize into JSON.
        """
        message_bytes = json.dumps(message).encode()
        return self.cipher_suite.encrypt(message_bytes)
    
    def decrypt_message(self, encrypted_message: bytes) -> dict:
        """Decrypts a Fernet-encrypted message back into a dictionary.

        Args:
            encrypted_message (bytes): The raw encrypted data.

        Returns:
            dict: The decrypted message fields.

        Raises:
            InvalidToken: If the message is invalid or has been tampered with.
        """
        decrypted_bytes = self.cipher_suite.decrypt(encrypted_message)
        return json.loads(decrypted_bytes)
    
    def sign_message(self, message: dict) -> str:
        """Generates an HMAC-SHA256 signature for a dictionary.

        Args:
            message (dict): The message to sign.

        Returns:
            str: Hexadecimal representation of the signature.
        """
        message_bytes = json.dumps(message, sort_keys=True).encode()
        signature = hmac.new(self.signing_key, message_bytes, hashlib.sha256)
        return signature.hexdigest()
    
    def verify_signature(self, message: dict, signature: str) -> bool:
        """Verifies an HMAC-SHA256 signature matches the given message.

        Args:
            message (dict): The original message data.
            signature (str): The provided signature in hex format.

        Returns:
            bool: True if the signature is valid, False otherwise.
        """
        expected = self.sign_message(message)
        return hmac.compare_digest(signature, expected)


def log_security_event(security_protocol: SecurityProtocol, event: dict):
    """Encrypts and logs a security event to the security_events_queue.

    Args:
        security_protocol (SecurityProtocol): The SecurityProtocol instance for encryption.
        event (dict): The security event details, e.g.:
            {
                "event_type": "access_attempt",
                "agent_id": "agent_42",
                "severity": "medium",
                "details": "Unauthorized file access"
            }

    Notes:
        - A timestamp is added before encryption.
        - The event is signed and placed on the queue with the structure:
          {
            "encrypted_data": <bytes>,
            "signature": <str>,
            "timestamp": <str>
          }
    """
    event_with_timestamp = {
        **event,
        "timestamp": datetime.now().isoformat()
    }
    encrypted = security_protocol.encrypt_message(event_with_timestamp)
    signature = security_protocol.sign_message(event_with_timestamp)
    
    security_events_queue.put({
        "encrypted_data": encrypted,
        "signature": signature,
        "timestamp": datetime.now().isoformat()
    })


def log_agent_metrics(security_protocol: SecurityProtocol, metrics: dict):
    """Encrypts and logs agent metrics to the agent_metrics_queue.

    Args:
        security_protocol (SecurityProtocol): The SecurityProtocol instance for encryption.
        metrics (dict): The agent metrics data, e.g.:
            {
                "agent_id": "agent_42",
                "trust_score": 0.8,
                "performance_metrics": {...}
            }

    Notes:
        - A timestamp is added before encryption.
        - The metrics are signed and placed on the queue with the structure:
          {
            "encrypted_data": <bytes>,
            "signature": <str>,
            "timestamp": <str>
          }
    """
    metrics_with_timestamp = {
        **metrics,
        "timestamp": datetime.now().isoformat()
    }
    encrypted = security_protocol.encrypt_message(metrics_with_timestamp)
    signature = security_protocol.sign_message(metrics_with_timestamp)
    
    agent_metrics_queue.put({
        "encrypted_data": encrypted,
        "signature": signature,
        "timestamp": datetime.now().isoformat()
    })

# ---------------------------------------------------------------------
# SSE (Server-Sent Events) Endpoints
# ---------------------------------------------------------------------
@app.route('/stream/cognitive')
def cognitive_stream():
    """
    Connects to the /text_feed endpoint and streams the raw HTML content
    via SSE.
    """
    def generate():
        url = 'http://localhost:5001/text_feed'
        try:
            response = requests.get(url, stream=True)
            # Yield each line from the response as SSE data.
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    yield f"data: {line}\n\n"
        except Exception as e:
            yield f"data: Connection error: {e}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")
    
@app.route('/stream/browser')
def browser_stream():
    """
    Connects to the /video_feed endpoint and displays the video stream.
    """
    def generate():
        url = 'http://localhost:5001/video_feed'
        cap = cv2.VideoCapture(url)
        
        if not cap.isOpened():
            yield b"Error: Unable to open video stream."
            return
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue  # Skip if encoding fails
            
            frame_bytes = buffer.tobytes()
            
            # Yield the frame in the multipart format
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )
    
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route('/stream/security-events')
def security_events_stream():
    """Streams encrypted security events in real time (SSE).

    These events are placed on the queue via log_security_event.
    This endpoint transforms raw bytes into base64 for JSON serialization.
    """
    def generate():
        while True:
            event = security_events_queue.get()
            # Convert raw bytes to base64
            if "encrypted_data" in event and isinstance(event["encrypted_data"], bytes):
                event["encrypted_data"] = base64.b64encode(event["encrypted_data"]).decode("utf-8")
            yield f"data: {json.dumps(event)}\n\n"
    return Response(generate(), mimetype='text/event-stream')


@app.route('/stream/agent-metrics')
def agent_metrics_stream():
    """Streams encrypted agent metrics in real time (SSE).

    The metrics are placed on the queue via log_agent_metrics.
    This endpoint transforms raw bytes into base64 for JSON serialization.
    """
    def generate():
        while True:
            metrics = agent_metrics_queue.get()
            if "encrypted_data" in metrics and isinstance(metrics["encrypted_data"], bytes):
                metrics["encrypted_data"] = base64.b64encode(metrics["encrypted_data"]).decode("utf-8")
            yield f"data: {json.dumps(metrics)}\n\n"
    return Response(generate(), mimetype='text/event-stream')


@app.route('/stream/inter-agent')
def inter_agent_stream():
    """
    Streams inter-agent communication messages in real time (SSE),
    ensuring that each message is encrypted.
    """
    def generate():
        while True:
            message = inter_agent_queue.get()
            if "encrypted_data" in message:
                # If already encrypted, ensure the data is base64 encoded.
                if isinstance(message["encrypted_data"], bytes):
                    message["encrypted_data"] = base64.b64encode(message["encrypted_data"]).decode("utf-8")
                yield f"data: {json.dumps(message)}\n\n"
            else:
                # Encrypt the plain message.
                if global_security_protocol:
                    encrypted = global_security_protocol.encrypt_message(message)
                    signature = global_security_protocol.sign_message(message)
                    encrypted_message = {
                        "encrypted_data": base64.b64encode(encrypted).decode("utf-8"),
                        "signature": signature,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(encrypted_message)}\n\n"
                else:
                    yield f"data: {json.dumps(message)}\n\n"
    return Response(generate(), mimetype="text/event-stream")

# ---------------------------------------------------------------------
# Decoding Helpers
# ---------------------------------------------------------------------
def decode_security_event(event: Dict[str, Any], protocol: SecurityProtocol) -> Dict[str, Any]:
    """Decodes and decrypts a single security event.

    Args:
        event (Dict[str, Any]): An event dictionary with at least:
            {
              "encrypted_data": <base64-encoded string>,
              "signature": <str>,
              ...
            }
        protocol (SecurityProtocol): The SecurityProtocol for decryption/verifying signature.

    Returns:
        Dict[str, Any]: {
          "decrypted": <dict of original fields>,
          "signature_valid": <bool>
        }

    Raises:
        ValueError: If 'encrypted_data' is missing.
        TypeError: If 'encrypted_data' is not a base64 string.
        InvalidToken: If decryption fails due to tampering or wrong key.
    """
    if "encrypted_data" not in event:
        raise ValueError("Missing 'encrypted_data' in event")

    encoded_data = event["encrypted_data"]
    if not isinstance(encoded_data, str):
        raise TypeError("'encrypted_data' must be a base64-encoded string")

    raw_encrypted = base64.b64decode(encoded_data)
    decrypted_dict = protocol.decrypt_message(raw_encrypted)

    signature = event.get("signature", "")
    signature_valid = protocol.verify_signature(decrypted_dict, signature)

    return {
        "decrypted": decrypted_dict,
        "signature_valid": signature_valid
    }


def decode_agent_metrics(metrics: Dict[str, Any], protocol: SecurityProtocol) -> Dict[str, Any]:
    """Decodes and decrypts a single agent metrics event.

    Args:
        metrics (Dict[str, Any]): A metrics dictionary with at least:
            {
              "encrypted_data": <base64-encoded string>,
              "signature": <str>,
              ...
            }
        protocol (SecurityProtocol): The SecurityProtocol for decryption/verifying signature.

    Returns:
        Dict[str, Any]: {
          "decrypted": <dict of original metric fields>,
          "signature_valid": <bool>
        }

    Raises:
        ValueError: If 'encrypted_data' is missing.
        TypeError: If 'encrypted_data' is not a base64 string.
        InvalidToken: If decryption fails due to tampering or wrong key.
    """
    if "encrypted_data" not in metrics:
        raise ValueError("Missing 'encrypted_data' in metrics")

    encoded_data = metrics["encrypted_data"]
    if not isinstance(encoded_data, str):
        raise TypeError("'encrypted_data' must be a base64-encoded string")

    raw_encrypted = base64.b64decode(encoded_data)
    decrypted_dict = protocol.decrypt_message(raw_encrypted)

    signature = metrics.get("signature", "")
    signature_valid = protocol.verify_signature(decrypted_dict, signature)

    return {
        "decrypted": decrypted_dict,
        "signature_valid": signature_valid
    }

# ---------------------------------------------------------------------
# Decoding Endpoints
# ---------------------------------------------------------------------
@app.route("/decoded/security-events", methods=["GET"])
def fetch_decoded_security_event():
    """Decodes and returns one security event from the queue.

    Grabs a single event from `security_events_queue`, base64-encodes any raw bytes,
    then calls `decode_security_event` with the global SecurityProtocol.

    Returns:
        JSON response containing:
            {
              "decrypted": { ...original fields... },
              "signature_valid": <bool>
            }

        Or a message if the queue is empty or the security protocol is not set.
    """
    global global_security_protocol
    if global_security_protocol is None:
        return jsonify({"error": "SecurityProtocol not set"}), 500

    if security_events_queue.empty():
        return jsonify({"message": "No security events available"}), 200

    raw_event = security_events_queue.get()
    if isinstance(raw_event.get("encrypted_data"), bytes):
        raw_event["encrypted_data"] = base64.b64encode(raw_event["encrypted_data"]).decode("utf-8")

    decoded = decode_security_event(raw_event, global_security_protocol)
    return jsonify(decoded), 200


@app.route("/decoded/agent-metrics", methods=["GET"])
def fetch_decoded_agent_metrics():
    """Decodes and returns one agent metrics item from the queue.

    Grabs a single metrics entry from `agent_metrics_queue`, base64-encodes any raw bytes,
    then calls `decode_agent_metrics` with the global SecurityProtocol.

    Returns:
        JSON response containing:
            {
              "decrypted": { ...original fields... },
              "signature_valid": <bool>
            }

        Or a message if the queue is empty or the security protocol is not set.
    """
    global global_security_protocol
    if global_security_protocol is None:
        return jsonify({"error": "SecurityProtocol not set"}), 500

    if agent_metrics_queue.empty():
        return jsonify({"message": "No agent metrics available"}), 200

    raw_metrics = agent_metrics_queue.get()
    if isinstance(raw_metrics.get("encrypted_data"), bytes):
        raw_metrics["encrypted_data"] = base64.b64encode(raw_metrics["encrypted_data"]).decode("utf-8")

    decoded = decode_agent_metrics(raw_metrics, global_security_protocol)
    return jsonify(decoded), 200

@app.route('/receive/inter-agent', methods=['GET'])
def receive_inter_agent():
    """
    Retrieves the next inter-agent message from the inter_agent_queue,
    encrypts it if necessary, then decrypts it and returns the decrypted message.
    This endpoint uses GET so you can simply navigate to 
    http://127.0.0.1:8080/receive/inter-agent in your browser.
    """
    if inter_agent_queue.empty():
        return jsonify({"error": "No inter-agent message available"}), 404

    # Retrieve the plain message from the queue.
    message = inter_agent_queue.get()

    # If the message is not already encrypted, encrypt it now.
    if "encrypted_data" not in message:
        if global_security_protocol:
            encrypted = global_security_protocol.encrypt_message(message)
            # Store the Base64-encoded encrypted data in the message.
            message["encrypted_data"] = base64.b64encode(encrypted).decode("utf-8")
        else:
            return jsonify({"error": "SecurityProtocol not set"}), 500

    try:
        # Decode the Base64 data back to bytes.
        raw_encrypted = base64.b64decode(message["encrypted_data"])
        # Decrypt the message using the global security protocol.
        decrypted = global_security_protocol.decrypt_message(raw_encrypted)
        return jsonify({"decrypted": decrypted})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def simulate_events(protocol: SecurityProtocol):
    """Generates sample events for testing the orchestrator.

    Args:
        protocol (SecurityProtocol): The shared SecurityProtocol for encryption.

    This function runs in a background thread. It periodically logs:
      - A security event (e.g. unauthorized access)
      - A metrics event (e.g. agent performance)
      - Additional cognitive/browser events
    """
    while True:
        example_event = {
            "event_type": "access_attempt",
            "agent_id": "agent_42",
            "severity": "medium",
            "details": "Unauthorized file access"
        }
        log_security_event(protocol, example_event)

        example_metrics = {
            "agent_id": "agent_42",
            "trust_score": 0.85,
            "performance_metrics": {
                "response_time": 150,
                "success_rate": 0.95
            }
        }
        log_agent_metrics(protocol, example_metrics)

        # Additional sample data for SSE
        cognitive_stream_queue.put({
            "type": "THOUGHT",
            "content": "Simulating thought process",
            "timestamp": datetime.now().isoformat()
        })
        browser_stream_queue.put({
            "type": "ACTION",
            "content": "Clicking button",
            "timestamp": datetime.now().isoformat()
        })

        time.sleep(4)


def run_server(port: int, security_protocol: SecurityProtocol):
    """Starts the Flask server and the simulation thread.

    Args:
        port (int): The port on which to run the Flask server.
        security_protocol (SecurityProtocol): The shared protocol to use for encrypt/decrypt.

    This function sets a global `global_security_protocol`, spawns a background thread
    for `simulate_events()`, and then runs the Flask app.
    """
    global global_security_protocol
    global_security_protocol = security_protocol  # store the same instance for decode endpoints

    simulator = threading.Thread(
        target=simulate_events,
        args=(global_security_protocol,),
        daemon=True
    )
    simulator.start()
    
    logger.info(f"Starting Agent Orchestrator on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


# # Import the required components from LLMCompiler-Pro:
# from llmcompiler_pro.llmcompiler_pro.llmcompiler_pro import LLMCompilerPro
# from llmcompiler_pro.schema.common import LLMCompilerProRequest, Language
# from llmcompiler_pro.tools import get_tools
# import asyncio

# def run_llm_compiler_for_graph(context: str, prompt: str) -> str:
#     # Create a request configuration for the LLMCompilerPro
#     configuration = LLMCompilerProRequest(
#         model_name="gpt-4o",   # or whichever model you want to use
#         max_replan=1,
#         session_id="graph-session",
#         language=Language.English  # adjust if needed
#     )
#     # Get the tools your compiler should use
#     tools = get_tools()
#     # Create an instance of the compiler
#     compiler = LLMCompilerPro(configuration, tools, callbacks=[])
#     # Combine context and prompt (if context is provided)
#     full_query = f"{context}\n{prompt}" if context else prompt

#     # Call the compiler (blocking until complete)
#     compiled_html = asyncio.run(compiler.acall(full_query, []))
#     return compiled_html

# # Then, in your /compile-graph endpoint, you can do:
# @app.route("/compile-graph", methods=["POST"])
# def compile_graph():
#     data = request.get_json(force=True)
#     prompt = data.get("prompt", "")
#     context = data.get("context", "")
#     try:
#         compiled_html = run_llm_compiler_for_graph(context, prompt)
#         logger.info(f"Compiled HTML for prompt: {prompt}")
#         return render_template_string(compiled_html), 200
#     except Exception as e:
#         logger.error(f"Error compiling graph: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# # And for this specific prompt, the exact call would be:
# compiled_html = run_llm_compiler_for_graph("", "We are a group of 8 going to Cabo for Spring Break. Our budget is $1500 per person and we're going for 5N, 6D")
