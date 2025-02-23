from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from tools import perplexity_tool  # Import from the module
import os

# Initialize an LLM
llm = OpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))

# Set up an agent with the imported tool
agent = initialize_agent(
    tools=[perplexity_tool],
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

# Example usage
if __name__ == "__main__":
    query = "What are the latest breakthroughs in AI research?"
    result = agent.run(query)
    print("Search Result:", result)
