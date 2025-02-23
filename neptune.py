import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from gremlin_python.driver import client, serializer
import nest_asyncio

# Allow nested event loops (if needed)
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)

# AWS Neptune connection configuration
NEPTUNE_ENDPOINT = "your-neptune-endpoint"  # e.g., "neptune-cluster.xxxxxxxx.us-east-1.neptune.amazonaws.com"
NEPTUNE_PORT = "8182"
NEPTUNE_URL = f"wss://{NEPTUNE_ENDPOINT}:{NEPTUNE_PORT}/gremlin"

# Initialize the Gremlin client for AWS Neptune
neptune_client = client.Client(
    NEPTUNE_URL,
    'g',
    message_serializer=serializer.GraphSONSerializersV2d0()
)

def run_query(user_prompt: str):
    """
    Construct a Gremlin query using the user prompt and a fixed suffix.
    Note: This is an example query. You should update the query below to match
    your graph's schema and the desired query logic.
    """
    # Append fixed instructions (similar to your Neo4j version)
    prompt_suffix = """
Based on the user's memory and the prompt; Summarize the Objective:
Clearly restate the main goal and constraints.
Identify Key Details:
Extract critical information such as group size, budget, duration, and destination.
Break Down Tasks:
Outline clear, actionable steps for the team (e.g., budgeting, itinerary planning, activity suggestions, and logistics).
Deliver a Plan:
Present a concise, step-by-step plan with measurable outcomes.
Keep it minimally objective, and the response short in 5-6 bullet points.
    """
    final_prompt = user_prompt + prompt_suffix

    # Example Gremlin query: search for vertices where a property 'description' contains the final prompt.
    # You will likely need to adjust this query to suit your graph schema.
    gremlin_query = f"g.V().has('description', textContains('{final_prompt}')).valueMap()"
    
    # Submit the query asynchronously
    callback = neptune_client.submitAsync(gremlin_query)
    if callback.result() is not None:
        result = callback.result().all().result()
        return result
    else:
        return "No results found."

# Create the Flask app
app = Flask(__name__)
CORS(app)

@app.route("/query", methods=["POST"])
def query_endpoint():
    """
    Expects a JSON payload with a "prompt" key.
    Returns the query result as JSON.
    """
    data = request.get_json()
    if not data or "prompt" not in data:
        return jsonify({"error": "Missing 'prompt' in request body."}), 400
    prompt = data["prompt"]
    try:
        result = run_query(prompt)
        return jsonify({"response": result})
    except Exception as e:
        logging.exception("Error processing query")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logging.info("Starting Flask server on port 8080")
    app.run(host="0.0.0.0", port=8080)
