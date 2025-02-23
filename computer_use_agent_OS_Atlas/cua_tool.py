from langchain_core.tools import tool
import requests

# Define the API endpoint
API_ENDPOINT = "http://127.0.0.1:8000/run-task/"


@tool
def browser_task_tool(prompt: str, context: str = "") -> str:
    """
    Tool to interact with web pages or perform tasks requiring browser automation.
    The input format is strictly a JSON string with two keys: 'prompt' and 'context'.
    Example: '{"prompt": "Fetch the current weather in SF", "context": "Use the browser tabs"}'
    """

    # Prepare the payload
    payload = {"prompt": prompt, "context": context}

    try:
        # Make a POST request
        response = requests.post(
            API_ENDPOINT,
            json=payload,  # Automatically converts to JSON format
            headers={"Content-Type": "application/json"},
        )

        # Raise an error if the request failed
        response.raise_for_status()

        # Return the response content
        return response.json()

    except requests.exceptions.RequestException as e:
        return f"Error: {e}"


# import json

# # Define the API endpoint and payload
# api_endpoint = "http://0.0.0.0:8000/run-task/"
# payload = {"prompt": "Your prompt here", "context": "Optional context here"}

# # Prepare the input for the tool
# tool_input = json.dumps({"url": api_endpoint, "data": payload})

# # Invoke the tool
# response = browser_task_tool(tool_input)
# print(response)
