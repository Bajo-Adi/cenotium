from react_agent import *
from react_agent import run_agent


QUERY_TEMPLATE = """
You are a web automation agent. Your task is to visit the given URL and extract all interactive elements on the page, returning them in JSON format.

## Instructions:
1. Navigate to the URL: {url}
2. Identify all interactive elements on the page, including:
   - Buttons (`<button>`)
   - Links (`<a>`)
   - Input fields (`<input>`)
   - Select dropdowns (`<select>`)
   - Textareas (`<textarea>`)
   - Any other elements that users can interact with
3. Extract:
   - **Element name**: The best available identifier (from `name`, `id`, `aria-label`, `title`, or inner text).
   - **Bounding box area**: The coordinates of the element (x, y, width, height).

You can only extract them if YOU CLICK ON THEM!! AND YOU MUST!!   

## Expected JSON Output:
Return a dictionary where:
- **Keys** are element names (strings).
- **Values** are lists representing the bounding box `[x, y, width, height]`.

Example output:
```json
{
    "Search Button": [100, 200, 80, 40],
    "Email Input": [150, 250, 300, 50],
    "Sign Up Link": [50, 400, 120, 30]
}
"""
import json
import os
import asyncio

LOG_FILE = "click_logs.json"
PERSISTENT_FILE = "interactive_elements.json"


async def extract_interactive_elements(urls):
    results = {}

    # Read existing click logs (temporary data)
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                click_logs = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error reading {LOG_FILE}: {e}")
                click_logs = []
    else:
        click_logs = []

    # Clear the temporary log file after reading
    with open(LOG_FILE, "w") as f:
        json.dump([], f, indent=4)

    # Read existing persistent data for interactive elements
    if os.path.exists(PERSISTENT_FILE):
        with open(PERSISTENT_FILE, "r") as f:
            try:
                stored_elements = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error reading {PERSISTENT_FILE}: {e}")
                stored_elements = {}
    else:
        stored_elements = {}

    # Process URLs and fetch new interactive elements
    for url in urls:
        try:
            query = QUERY_TEMPLATE.format(
                url=url
            )  # Fill the template with the actual URL
            interactive_elements = await format_and_run_query(query, "")
            print(interactive_elements)
            # Update persistent storage
            stored_elements[url] = interactive_elements

            # Save the updated interactive elements persistently
            with open(PERSISTENT_FILE, "w") as f:
                json.dump(stored_elements, f, indent=4)
        except Exception as e:
            print(f"Error processing {url}: {e}")
            stored_elements[url] = None

    return {"click_logs": click_logs, "interactive_elements": stored_elements}


if __name__ == "__main__":
    urls = [
        "https://example.com",
        # "https://anotherexample.com",
        # Add more URLs as needed
    ]
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(extract_interactive_elements(urls))
    for url, elements in results.items():
        if elements:
            print(f"Interactive elements in {url}:")
            for element in elements:
                print(f"- {element}")
        else:
            print(f"No interactive elements found or error processing {url}.")
