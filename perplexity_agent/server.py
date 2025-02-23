# perplexity_agent/server.py
from flask import Flask, Response, stream_with_context, request
from flask_cors import CORS
import asyncio
import json
import os

# Import the perplexity agent function; adjust the import as needed.
from perplexity_agent.agent import run_agent  # run_agent should accept (query, user_context)

app = Flask(__name__)
CORS(app)  # Enables CORS for all domains on all routes

def run_perplexity_stream(query: str, timeout: int = 120):
    """
    Creates an event loop, runs the perplexity agent call asynchronously (wrapped in a thread),
    and yields the result as Server-Sent Event (SSE) messages.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def stream_steps():
        # Here we run the perplexity call in a thread to simulate asynchronous behavior.
        result = await asyncio.to_thread(run_agent, query, "")  # Pass an empty context or modify as needed.
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
    query = request.args.get("query", "Default perplexity query")
    return Response(stream_with_context(run_perplexity_stream(query)), mimetype="text/event-stream")

if __name__ == '__main__':
    # Run on port 7000 (for example)
    app.run(debug=True, port=7000)
