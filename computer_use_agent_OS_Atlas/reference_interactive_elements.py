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


async def extract_interactive_elements(urls):
    results = {}
    for url in urls:
        try:
            query = QUERY_TEMPLATE.format(
                url=url
            )  # Fill the template with the actual URL
            interactive_elements = await run_agent(query, "")
            results[url] = interactive_elements
        except Exception as e:
            print(f"Error processing {url}: {e}")
            results[url] = None
    return results


if __name__ == "__main__":
    urls = [
        "https://example.com",
        "https://anotherexample.com",
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
