# twilio_agent/server.py
from flask import Flask, Response, stream_with_context, request
from flask_cors import CORS
import asyncio
import json
import os

# Import the twilio tool; it should be defined in twilio_agent/tools.py
from twilio_agent.tools import twilio_tool  # Ensure twilio_tool is a runnable StructuredTool

app = Flask(__name__)
CORS(app)  # Enables CORS

def run_twilio_stream(query: str, timeout: int = 120):
    """
    Creates an event loop, runs the twilio tool call asynchronously (wrapped in a thread),
    and yields the result as SSE messages.
    The query is expected to be a JSON string containing keys "to_number" and "message".
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def stream_steps():
        # Parse the query as JSON. If not valid, use defaults.
        try:
            data = json.loads(query)
        except Exception:
            data = {"to_number": "+14709977644", "message": "Test call message."}
        # Run the tool in a thread (assuming twilio_tool.run is synchronous)
        result = await asyncio.to_thread(twilio_tool.run, data)
        yield json.dumps(result)
    
    try:
        gen = stream_steps()
        while True:
            step = loop.run_until_complete(gen.__anext__())
            yield f"data: {step}\n\n"
    except StopAsyncIteration:
        pass
    finally:
        loop.close()

@app.route('/stream', methods=['GET'])
def stream():
    # Expect a query parameter with a JSON string.
    query = request.args.get("query", '{"to_number": "+14709977644", "message": "This is a test call."}')
    return Response(stream_with_context(run_twilio_stream(query)), mimetype="text/event-stream")

if __name__ == '__main__':
    # Run on port 6000 (for example)
    app.run(debug=True, port=6000)
