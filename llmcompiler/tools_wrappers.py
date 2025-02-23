from typing import Any, Optional, Dict
from langchain_core.tools import BaseTool
from perplexity_agent.agent import run_agent as run_perplexity
from twilio_agent.agent import run_agent as run_twilio

class PerplexityAgentTool(BaseTool):
    name: str = "PerplexityAgent"
    description: str = (
        "Use this tool to search the internet via the Perplexity API. "
        "Input should be a dict with keys: 'query' (string) and optionally 'user_context'. "
        "Output will be a JSON-like string of search results."
    )

    def invoke(self, args: Dict[str, Any], config: Optional[Any] = None) -> str:
        query = args.get("query", "")
        user_context = args.get("user_context", "")
        result = run_perplexity(query, user_context)
        return str(result)

    def _run(self, *args, **kwargs) -> Any:
        return self.invoke(*args, **kwargs)


class TwilioAgentTool(BaseTool):
    name: str = "TwilioAgent"
    description: str = (
        "Use this tool to place a call to a +1 number and provide the agent with a message. "
        "Input example: { 'to_number': '+19995550123', 'message': 'Hello!' }"
    )

    def invoke(self, args: Dict[str, Any], config: Optional[Any] = None) -> str:
        to_number = args.get("to_number", "")
        message = args.get("message", "")
        result = run_twilio(to_number, message)
        return str(result)

    def _run(self, *args, **kwargs) -> Any:
        return self.invoke(*args, **kwargs)
