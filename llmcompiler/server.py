# server.py
from flask import Flask, Response, stream_with_context, request
import asyncio
import json
import threading


# Import your LLMCompiler from your package (use absolute import if necessary)
from llmcompiler.llm_compiler import LLMCompiler

app = Flask(__name__)

def run_compiler_stream(query: str, timeout: int = 120):
    """
    Creates an event loop, runs the compiler stream asynchronously with a timeout,
    and yields output as Server-Sent Event (SSE) messages.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    compiler = LLMCompiler()
    
    async def stream_steps():
        try:
            # Using our chain's stream wrapped in wait_for; alternatively, you can directly use chain.stream here.
            async for step in asyncio.wait_for(compiler.create_graph().stream({"messages": [{"content": query, "role": "human"}]}, {"recursion_limit": 100}), timeout=timeout):
                # Convert the step to JSON for streaming
                yield json.dumps(step)
        except asyncio.TimeoutError:
            yield json.dumps({"error": "Timeout reached. Returning latest available output."})
        except StopAsyncIteration:
            return

    # Run the async generator and yield its items synchronously
    try:
        gen = stream_steps()
        while True:
            # Fetch next item from the async generator
            step = loop.run_until_complete(gen.__anext__())
            yield f"data: {step}\n\n"
    except StopAsyncIteration:
        pass
    finally:
        loop.close()

@app.route('/stream', methods=['GET'])
def stream():
    # Get the query from the URL query string (e.g. ?query=Plan+trip+to+Cabo)
    query = request.args.get("query", "Plan a trip to Cabo for 8 people, under $1500/person, 5 nights, 6 days.")
    # Create a streaming response using the generator
    return Response(stream_with_context(run_compiler_stream(query)), mimetype="text/event-stream")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
