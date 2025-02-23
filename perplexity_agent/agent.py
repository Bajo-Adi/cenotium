# Simple Plan-and-Execute Agent
# Place OpenAI API key and run script
"""
Update as of 02/10/2025:
- Prompt location changed for agent (DEPRECATED)
- Need an older langgraph (0.2.17)
"""


from .tools import perplexity_tool
from langchain.tools import Tool

tools = [perplexity_tool]  # Add tools as needed
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import CallbackManager, BaseCallbackHandler
import logging
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

# Configure the logger
logfile = "agent_activity.log"
logging.basicConfig(
    filename=logfile,
    filemode="a",  # Append mode
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)


# Define a custom callback handler
class LoggingCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        logging.info(f"LLM started with prompts: {prompts}")

    def on_llm_end(self, response, **kwargs):
        logging.info(f"LLM ended with response: {response}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        logging.info(f"Tool started with input: {input_str}")

    def on_tool_end(self, output, **kwargs):
        logging.info(f"Tool ended with output: {output}")

    def on_text(self, text, **kwargs):
        logging.info(f"Agent generated text: {text}")


# Initialize the callback manager with the custom handler
callback_handler = LoggingCallbackHandler()
callback_manager = CallbackManager(handlers=[callback_handler])

# Load environment variables
load_dotenv(override=True)

# Define the prompt for the agent
prompt = "You are a helpful assistant."

# Initialize the language model
llm = ChatOpenAI(model="gpt-4o")

# Create the agent executor with the callback manager
agent_executor = create_react_agent(llm, tools, state_modifier=prompt).with_config(
    callback_manager=callback_manager, return_intermediate_steps=True, verbose=True
)
# 2. Planner (WITH TOOL CALLS)

import operator
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict


class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str


from pydantic import BaseModel, Field


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )


from langchain_core.prompts import ChatPromptTemplate

planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.
Use the "Added User Context" to get the objective, taking SUBJECTIVE DECISIONS AS NECESSARY. However if there ARE ANY FINANCIAL TRANSACTIONS OR SENSITIVE INFORMATION REQUIRED, you can respond directly to the user.
YOUR RESPONSE TO THE USER MUST INCLUDE A HIGHLY DETAILED REPORT OF THE RESULTS OF YOUR PLAN!!""",
        ),
        ("placeholder", "{messages}"),
    ]
)
planner = planner_prompt | ChatOpenAI(
    model="gpt-4o",
    temperature=0,
).with_structured_output(Plan)

# 3. ReAct agent replanning

from typing import Union


class Response(BaseModel):
    """Response to user."""

    response: str


class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
        "If you need to further use tools to get the answer, use Plan."
    )


replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.
Your objective was this:
{input}
Your original plan was this:
{plan}
You have currently done the follow steps:
{past_steps}
Update your plan accordingly. If no more steps are needed OR VRAM is LOW and you can return to the user, then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan. 
YOUR RESPONSE TO YTHE USER MUST INCLUDE A HIGHLY DETAILED REPORT OF THE RESULTS OF YOUR PLAN!!
"""
)


replanner = replanner_prompt | ChatOpenAI(
    model="gpt-4o", temperature=0
).with_structured_output(Act)


# LangGraph Definition
from typing import Literal
from langgraph.graph import END


async def execute_step(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step {1}, {task}."""
    agent_response = await agent_executor.ainvoke(
        {"messages": [("user", task_formatted)]}
    )
    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
    }


async def plan_step(state: PlanExecute):
    plan = await planner.ainvoke({"messages": [("user", state["input"])]})
    return {"plan": plan.steps}


async def replan_step(state: PlanExecute):
    output = await replanner.ainvoke(state)
    if isinstance(output.action, Response):
        return {"response": output.action.response}
    else:
        return {"plan": output.action.steps}


# Tracking attempt status


def should_end(state: PlanExecute):
    global replanning_attempts
    if "response" in state and state["response"]:  # Plan successfully completed
        return END
    else:
        replanning_attempts += 1
        return "agent"


from langgraph.graph import StateGraph, START

workflow = StateGraph(PlanExecute)

# Add the plan node
workflow.add_node("planner", plan_step)

# Add the execution step
workflow.add_node("agent", execute_step)

# Add a replan node
workflow.add_node("replan", replan_step)

workflow.add_edge(START, "planner")

# From plan we go to agent
workflow.add_edge("planner", "agent")

# From agent, we replan
workflow.add_edge("agent", "replan")

workflow.add_conditional_edges(
    "replan",
    # Next, we pass in the function that will determine which node is called next.
    should_end,
    ["agent", END],
)

# Finally, we compile it!
# This compiles it into a LangChain Runnable,
# meaning you can use it as you would any other runnable
app = workflow.compile()
# print(app.get_graph())


# Tests
import asyncio


# Define the asynchronous function to process events
async def process_events(inputs, config):
    responses = []  # List to store the processed responses
    # Asynchronously iterate over events from the app's astream
    async for event in app.astream(inputs, config=config):
        for k, v in event.items():
            if k != "__end__":
                responses.append(v)  # Collect responses instead of printing
                # print("Status: " + str(v))
    return responses  # Return the collected responses


import asyncio
from langgraph.errors import GraphRecursionError  # Import your specific error if needed


async def process_input(input_prompt: str) -> tuple:
    """
    Processes the given input prompt, runs the event loop, and returns the results.

    Args:
        input_prompt (str): The input query or prompt to process.

    Returns:
        tuple: A tuple containing:
            - responses[-1] (str): The last response from processing the events.
            - curr_completed (bool): Whether the process completed successfully.
            - replanning_attempts (int): Number of replanning attempts.
    """
    # Initialize variables
    curr_completed = False
    global replanning_attempts
    replanning_attempts = 1  # Initial attempt
    edited_prompt = input_prompt

    # Configuration
    config = {"recursion_limit": 50}
    inputs = {"input": edited_prompt}
    # Call the async function and get the responses
    try:
        responses = await process_events(inputs, config)
        curr_completed = True
        import react_agent_response as react_model_state

        print("Model Response: ", react_model_state.model_response)
        return (
            responses[-1]["response"],
            curr_completed,
            replanning_attempts,
            react_model_state.model_response,
            react_model_state.formatted_input,  # Formatted Input by Planner
        )  # Adding the Object
    except GraphRecursionError:  # Handle specific error
        print("Run failed due to Graph Recursion Error")
        curr_completed = False
        replanning_attempts = 0  # Resetting replanning steps
        return (
            None,
            curr_completed,
            replanning_attempts,
            None,
            react_model_state.formatted_input,
        )  # No return object


# # To use this function
async def caller(detailed_prompt):
    input_prompt = detailed_prompt
    result, completed, attempts, react_model_state, formatted_input = (
        await process_input(input_prompt)
    )
    print("Result: ", result)
    print("Completed: ", completed)
    print("Attempts: ", attempts)
    #print("Model Response: ", react_model_state)
    #print("Formatted Input: ", formatted_input)


# Run the main function (TEST)
# if __name__ == "__main__":
#     asyncio.run(main("What is the capital of France?"))
import asyncio
import json


async def format_and_run_query(query: str, user_context: str = ""):
    """
    Formats the input query with additional user context, processes it, and returns the result.

    Args:
        query (str): The main prompt/query from the user.
        user_context (str, optional): Additional background information to guide the agent. Defaults to "".

    Returns:
        dict: A structured response containing the result, completion status, attempts, model response, and formatted input.
    """

    if not query.strip():
        return {
            "status": "error",
            "error_code": "EMPTY_QUERY",
            "message": "The query cannot be empty. Please provide a valid input.",
            "suggestions": [
                "Ensure that the query contains meaningful text.",
                "Avoid passing empty strings or spaces as input.",
                "Provide specific details in the query for better responses.",
            ],
        }

    # Format the input with context (if provided)
    detailed_prompt = (
        f"User Query: {query}\nUser Context: {user_context}. Combine the two into a detailed, unmabiguous prompt and return it. YOU CAN PLAN ONLY ONCE!"
        if user_context
        else query
    )

    try:
        # Call the main function with formatted input
        result, completed, attempts, react_model_state, formatted_input = await caller(
            detailed_prompt
        )

        return {
            "status": "success",
            "message": "Query processed successfully.",
            "response": {
                "result": result,
                "completed": completed,
                "attempts": attempts,
                "model_response": react_model_state,
                "formatted_input": formatted_input,
            },
        }

    except KeyboardInterrupt:
        return {
            "status": "error",
            "error_code": "USER_INTERRUPTED",
            "message": "Execution was interrupted by the user.",
            "suggestions": [
                "Restart the script if you stopped it accidentally.",
                "Use a proper exit command instead of a keyboard interrupt.",
            ],
        }

    except Exception as e:
        return {
            "status": "error",
            "error_code": "UNKNOWN_ERROR",
            "message": f"An unexpected error occurred: {str(e)}",
            "suggestions": [
                "Try restarting the script.",
                "Check for missing dependencies or incorrect configurations.",
                "Review the query and user context for potential issues.",
            ],
        }


# # Example usage in an async environment
# if __name__ == "__main__":
#     query = "Explain quantum mechanics"
#     user_context = "Focus on beginner-friendly concepts"


#     response = asyncio.run(format_and_run_query(query, user_context))
#     print(json.dumps(response, indent=4))
def run_agent(query, user_context):
    response = asyncio.run(format_and_run_query(query, user_context))
    return response

perplexity_agent_tool = Tool(
    name="PerplexityAgent",
    func=run_agent,
    description="Use this tool to search the internet via the Perplexity API. Input: a search query string. Output: search results in JSON format."
)

# if __name__ == "__main__":
#     query = input("Enter your query: ")
#     user_context = input("Enter additional context (optional): ")

#     response = run_agent(query, user_context)
#     print(response)
