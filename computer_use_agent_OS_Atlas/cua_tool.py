# Kicks off an API call
from langchain.tools import RequestsPostTool

# Define the API endpoint
API_ENDPOINT = "http://0.0.0.0:8000/run-task/"

# Create the LangChain tool
browser_task_tool = RequestsPostTool(
    name="browser_task",
    description=(
        "This tool sends a prompt and optional context to the browser automation API. "
        "Use this tool to perform browser-based tasks such as fetching data from websites, "
        "interacting with web pages, or any task that requires browser automation."
    ),
    url=API_ENDPOINT,
    headers={"Content-Type": "application/json"},
)
