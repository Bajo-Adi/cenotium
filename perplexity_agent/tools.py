import requests
import os
from langchain.tools import Tool

# Define a function that calls the Perplexity API for a search query.
def perplexity_search(query: str) -> str:
    api_url = "https://api.perplexity.ai/chat/completions"
    api_key = os.getenv("PERPLEXITY_KEY")  # Replace with your actual API key

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar-pro",
        "messages": [{"role": "user", "content": query}]
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

# Create a LangChain Tool wrapping our search function.
perplexity_tool = Tool(
    name="PerplexitySearch",
    func=perplexity_search,
    description="Use this tool to search the internet via the Perplexity API. Input: a search query string. Output: search results in JSON format."
)
