"""
Main LLMCompiler implementation for trip planning.
This module also provides a Flask server endpoint to stream the output
with a 2-minute timeout. The stream first yields step-by-step data,
and once complete, it aggregates and cleans all join messages, then calls
OpenAI to summarize the cleaned data into 4 bullet points (50–60 words max),
streaming that final summary as the last SSE event.
"""

# ----- Load Environment Variables Early -----
from dotenv import load_dotenv
import os
import getpass

# Load .env from the same directory as this file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def _get_pass(var: str):
    if var not in os.environ:
        os.environ[var] = getpass.getpass(f"{var}: ")

_get_pass("OPENAI_API_KEY")

# ----- Standard Imports -----
import asyncio
import itertools
from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict, Annotated

from langchain import hub
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableConfig
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

# ----- Local Imports (using relative paths) -----
from .output_parser import LLMCompilerPlanParser
from .task_fetching import schedule_tasks
from .executor import ExecutorPool
from .tools_wrappers import PerplexityAgentTool, TwilioAgentTool

# ----- State and Trip Planner Tool Definition -----
class State(TypedDict):
    """State definition for the graph."""
    messages: Annotated[List[BaseMessage], add_messages]

def plan_trip(info: Dict) -> str:
    """Plans a trip based on the provided requirements."""
    trip_info = {
        "destination": info.get("destination", ""),
        "budget_per_person": float(info.get("budget_per_person", 0)),
        "group_size": int(info.get("group_size", 0)),
        "duration_nights": int(info.get("duration_nights", 0)),
        "duration_days": int(info.get("duration_days", 0)),
        "activities": info.get("activities", [])
    }
    total_budget = trip_info["budget_per_person"] * trip_info["group_size"]
    plan = f"""
Trip Plan for {trip_info["destination"]}:

Group Details:
- Group Size: {trip_info["group_size"]} people
- Duration: {trip_info["duration_nights"]} nights, {trip_info["duration_days"]} days
- Budget: ${trip_info["budget_per_person"]:,.2f} per person (Total: ${total_budget:,.2f})

Budget Breakdown (per person):
- Flights & Transportation: ${trip_info["budget_per_person"] * 0.35:,.2f}
- Accommodation: ${trip_info["budget_per_person"] * 0.30:,.2f}
- Activities & Entertainment: ${trip_info["budget_per_person"] * 0.20:,.2f}
- Food & Dining: ${trip_info["budget_per_person"] * 0.15:,.2f}

Daily Itinerary:
Day 1 (Arrival): 
- Airport transfer to hotel
- Check-in and resort orientation
- Welcome dinner at hotel restaurant

Day 2 (Beach & Relaxation):
- Morning beach time
- Afternoon pool activities
- Evening sunset sail

Day 3 (Adventure):
- Morning snorkeling tour
- Afternoon water sports
- Evening dinner in town

Day 4 (Local Experience):
- Morning shopping at local markets
- Afternoon cooking class
- Evening entertainment

Day 5 (Flexibility):
- Optional activities based on group preferences
- Beach club day
- Farewell dinner

Day 6 (Departure):
- Breakfast
- Free time for last-minute shopping
- Airport transfer

Additional Notes:
- All activities and timings can be adjusted based on group preferences
- Early booking recommended for better rates
- Transportation includes airport transfers and local movement
"""
    return plan

trip_planner_tool = StructuredTool.from_function(
    name="trip_planner",
    func=plan_trip,
    description=(
        "trip_planner(info: dict) -> str: "
        "Plans a trip given details like destination, budget_per_person, group_size, etc. "
        "Returns a plan with budget breakdown and itinerary."
    )
)

# ----- Response Models -----
class FinalPlan(BaseModel):
    """Trip plan output."""
    plan: str = Field(description="The final trip plan")

class JoinOutputs(BaseModel):
    """Joiner output for deciding next steps."""
    thought: str = Field(description="Reasoning behind the selected action")
    should_replan: bool = Field(description="Whether to replan or provide final response")
    feedback: Optional[str] = Field(None, description="Feedback for replanning if should_replan is True")
    plan: Optional[str] = Field(None, description="Final plan if should_replan is False")

# ----- Main LLMCompiler Class -----
class LLMCompiler:
    """Main LLMCompiler implementation."""
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        """Initialize with trip planner plus external tools."""
        self.tools = [
            trip_planner_tool,
            PerplexityAgentTool(),
            TwilioAgentTool(),
        ]
        self.llm = ChatOpenAI(model=model, temperature=0)
        self.executor_pool = ExecutorPool()
        self.setup_components()

    def setup_components(self):
        """Set up planner prompt, joiner prompt, and parser."""
        self.planner_prompt = hub.pull("wfh/llm-compiler")
        self.joiner_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a trip planning assistant that analyzes execution results and decides whether to:
1. Replan with feedback if the plan needs improvement
2. Provide a final response if the plan is complete

Consider:
- Does the plan fulfill all requirements?
- Are there missing details or improvements needed?
- Is the plan practical and within budget?

Analyze the plan and provide:
1. Your thought process
2. Decision to replan (true/false)
3. If replanning, feedback
4. If not, final plan"""),
            ("user", "{input}")
        ])
        self.parser = LLMCompilerPlanParser(tools=self.tools)
        tool_descriptions = "\n".join(
            f"{i+1}. {tool.description}\n" for i, tool in enumerate(self.tools)
        )
        self.planner_prompt = self.planner_prompt.partial(
            replan="",
            num_tools=len(self.tools) + 1,
            tool_descriptions=tool_descriptions,
        )

    def _parse_joiner_output(self, decision: JoinOutputs) -> Dict:
        """Convert joiner output into messages for the next chain step."""
        response = [AIMessage(content=f"Thought: {decision.thought}")]
        if decision.should_replan:
            return {
                "messages": response + [
                    SystemMessage(content=f"Context from last attempt: {decision.feedback}")
                ]
            }
        else:
            return {
                "messages": response + [
                    AIMessage(content=decision.plan if decision.plan else "No plan provided")
                ]
            }

    def _select_recent_messages(self, state: Dict) -> Dict:
        """Select the most recent human message for the joiner."""
        messages = state["messages"]
        selected = []
        for msg in reversed(messages):
            selected.append(msg)
            if isinstance(msg, HumanMessage):
                break
        return {"input": str(selected[-1].content)}

    def plan_and_schedule(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tasks from the parser and schedule them."""
        messages = state["messages"]
        tasks_iter = self.parser.stream(messages)
        try:
            first_task = next(tasks_iter)
            tasks_iter = itertools.chain([first_task], tasks_iter)
        except StopIteration:
            tasks_iter = iter([])
        return {
            "messages": schedule_tasks(
                {"messages": messages, "tasks": tasks_iter},
                config=RunnableConfig(recursion_limit=100)
            )
        }

    def create_graph(self) -> StateGraph:
        """Create the execution graph for planning."""
        joiner = (
            RunnableLambda(self._select_recent_messages)
            | self.joiner_prompt
            | self.llm.with_structured_output(JoinOutputs, method="function_calling")
            | RunnableLambda(self._parse_joiner_output)
        )
        graph = StateGraph(State)
        graph.add_node("plan_and_schedule", RunnableLambda(self.plan_and_schedule))
        graph.add_node("join", joiner)
        graph.add_edge("plan_and_schedule", "join")
        def should_continue(state):
            messages = state["messages"]
            if isinstance(messages[-1], AIMessage):
                return END
            return "plan_and_schedule"
        graph.add_conditional_edges("join", should_continue)
        graph.add_edge(START, "plan_and_schedule")
        return graph.compile()

    async def stream_with_timeout(self, query: str, config: Optional[Dict] = None, timeout: int = 120):
        """
        Asynchronously stream steps from the compiled graph with a timeout.
        Wrap the synchronous generator in an asynchronous generator.
        """
        if config is None:
            config = {"recursion_limit": 100}
        chain = self.create_graph()
        # Wrap the synchronous generator in an async generator.
        async def async_gen_wrapper():
            for item in chain.stream({"messages": [HumanMessage(content=query)]}, config):
                yield item
        agen = async_gen_wrapper()
        while True:
            try:
                step = await asyncio.wait_for(agen.__anext__(), timeout=timeout)
                yield step
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                yield {"error": "Timeout reached. Returning the latest available output."}
                break

# ----- Helper Functions for Cleaning and Summarizing Output -----
def clean_output(data: dict) -> dict:
    """
    Extracts and cleans data from a plan output.
    Returns a dictionary with keys: THOUGHT, ACTION, and CONTENT.
    Aggregates all join messages.
    """
    result = {"THOUGHT": [], "ACTION": [], "CONTENT": []}
    # Expect data to be a dict with a "join" key
    join_data = data.get("join", {})
    messages = join_data.get("messages", [])
    for msg in messages:
        content = msg.get("content", "").strip()
        msg_type = msg.get("type", "").lower()
        if content.startswith("Thought:"):
            result["THOUGHT"].append(content[len("Thought:"):].strip())
        elif msg_type == "system":
            result["ACTION"].append(content)
        else:
            result["CONTENT"].append(content)
    # Combine lists into single strings
    result["THOUGHT"] = " ".join(result["THOUGHT"]) if result["THOUGHT"] else ""
    result["ACTION"] = " ".join(result["ACTION"]) if result["ACTION"] else ""
    result["CONTENT"] = " ".join(result["CONTENT"]) if result["CONTENT"] else ""
    return result

def summarize_cleaned_data(cleaned_data: dict) -> str:
    """
    Uses ChatOpenAI to summarize the cleaned data into 4 bullet points.
    The summary is 50-60 words maximum.
    """
    summary_prompt = (
        "Summarize the following trip planning output in 4 bullet points. "
        "The summary must be between 50 and 60 words maximum:\n\n"
        f"THOUGHT: {cleaned_data.get('THOUGHT', '')}\n"
        f"ACTION: {cleaned_data.get('ACTION', '')}\n"
        f"CONTENT: {cleaned_data.get('CONTENT', '')}\n\n"
        "Bullet Points:"
    )
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    summary = llm(summary_prompt)
    return summary

# ----- Flask Server to Stream and Finalize Output -----
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        from flask import Flask, Response, stream_with_context, request
        import json

        app = Flask(__name__)

        @app.after_request
        def add_cors_headers(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return response

        def default_serializer(o):
            if hasattr(o, "model_dump"):
                return o.model_dump()
            elif hasattr(o, "dict"):
                return o.dict()
            return str(o)

        def run_compiler_stream(query: str, timeout: int = 120):
            """
            Create an event loop, run the compiler's stream_with_timeout asynchronously,
            accumulate all join events, and finally yield a summary event.
            """
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            compiler = LLMCompiler()
            async def stream_steps():
                steps = []
                # Accumulate all join events.
                async for step in compiler.stream_with_timeout(query, timeout=timeout):
                    steps.append(step)
                    yield json.dumps(step, default=default_serializer)
                # Aggregate all join messages from the collected steps.
                join_msgs = []
                for s in steps:
                    if "join" in s and s["join"].get("messages"):
                        join_msgs.extend(s["join"]["messages"])
                if join_msgs:
                    aggregated = {"join": {"messages": join_msgs}}
                    cleaned = clean_output(aggregated)
                    summary = summarize_cleaned_data(cleaned)
                    final_event = {"summary": summary, "cleaned": cleaned}
                    yield json.dumps(final_event, default=default_serializer)
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
            query = request.args.get("query", "Plan a trip to Cabo for 8 people, under $1500 per person, 5 nights, 6 days.")
            return Response(stream_with_context(run_compiler_stream(query)), mimetype="text/event-stream")

        app.run(debug=True, port=5000)
    else:
        # CLI mode: run the stream, clean output, and display final summary.
        async def run_stream_and_summarize(query: str):
            compiler = LLMCompiler()
            collected_steps = []
            async for step in compiler.stream_with_timeout(query):
                collected_steps.append(step)
                print("\nStep output:")
                print(step)
                print("---")
            if collected_steps:
                join_msgs = []
                for s in collected_steps:
                    if "join" in s and s["join"].get("messages"):
                        join_msgs.extend(s["join"]["messages"])
                aggregated = {"join": {"messages": join_msgs}}
                cleaned = clean_output(aggregated)
                summary = summarize_cleaned_data(cleaned)
                print("\nFinal Summarized Output:")
                print(summary)
            else:
                print("No output collected.")
        query = """
Plan a pleasurable Spring Break trip to Cabo for 8 people, under $1500 per person,
5 nights, 6 days. Possibly call me at +15551234567 using Twilio to confirm flights.
Or if needed, use Perplexity to see flight deals.
"""
        asyncio.run(run_stream_and_summarize(query))
