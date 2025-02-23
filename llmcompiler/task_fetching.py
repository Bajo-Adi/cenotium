# task_fetching.py

"""Task Fetching Unit for LLMCompiler."""
import re
import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Dict, Iterable, List, Optional, Union

from langchain_core.messages import BaseMessage, FunctionMessage
from langchain_core.runnables import RunnableConfig
from typing_extensions import TypedDict

from .output_parser import Task

class SchedulerInput(TypedDict):
    """Input type for the task scheduler."""
    messages: List[BaseMessage]
    tasks: Iterable[Task]

def _get_observations(messages: List[BaseMessage]) -> Dict[int, Any]:
    """Extract previous task results from messages."""
    results = {}
    for message in reversed(messages):
        if isinstance(message, FunctionMessage):
            idx_val = message.additional_kwargs.get("idx")
            if idx_val is not None:
                results[int(idx_val)] = message.content
    return results

def _resolve_arg(arg: Union[str, Any], observations: Dict[int, Any]) -> Any:
    """
    Resolve references like ${1} or $1 in the tool arguments.
    Looks up the previously observed result of that task index.
    """
    if isinstance(arg, str):
        ID_PATTERN = r"\$\{?(\d+)\}?"
        def replace_match(match):
            idx = int(match.group(1))
            return str(observations.get(idx, match.group(0)))
        return re.sub(ID_PATTERN, replace_match, arg)
    elif isinstance(arg, list):
        return [_resolve_arg(a, observations) for a in arg]
    return arg

def _execute_task(task: Task, observations: Dict, config: Optional[RunnableConfig] = None) -> Any:
    """Execute a single task by calling its tool with resolved arguments."""
    tool_to_use = task["tool"]
    if isinstance(tool_to_use, str):
        # If it's just 'join', or some string, no actual tool call
        return tool_to_use
    
    args = task["args"]
    try:
        if isinstance(args, dict):
            resolved_args = {
                key: _resolve_arg(val, observations)
                for key, val in args.items()
            }
        else:
            resolved_args = args
    except Exception as e:
        return f"ERROR: Failed to resolve arguments for {tool_to_use.name}. Error: {repr(e)}"
    
    try:
        return tool_to_use.invoke(resolved_args, config)
    except Exception as e:
        return f"ERROR: Failed to execute {tool_to_use.name}. Error: {repr(e)}"

def schedule_task(task_inputs: Dict) -> None:
    """Schedule and execute a single task."""
    task: Task = task_inputs["task"]
    observations: Dict[int, Any] = task_inputs["observations"]
    config = task_inputs.get("config")
    try:
        observation = _execute_task(task, observations, config)
        observations[task["idx"]] = observation
    except Exception as e:
        observations[task["idx"]] = f"ERROR: Task execution failed. {repr(e)}"

def schedule_pending_task(
    task: Task,
    observations: Dict[int, Any],
    retry_after: float = 0.2,
    config: Optional[RunnableConfig] = None
) -> None:
    """Schedule a task that has dependencies. Wait for them if needed."""
    while True:
        deps = task["dependencies"]
        # If any dependencies are not yet in 'observations', keep waiting
        if deps and any(dep not in observations for dep in deps):
            time.sleep(retry_after)
            continue
        schedule_task({"task": task, "observations": observations, "config": config})
        break

def schedule_tasks(
    scheduler_input: SchedulerInput,
    config: Optional[RunnableConfig] = None
) -> List[FunctionMessage]:
    """
    Schedule and execute tasks in parallel when possible.
    Returns a list of FunctionMessages capturing the results.
    """
    tasks_iter = scheduler_input["tasks"]
    messages = scheduler_input["messages"]
    observations = _get_observations(messages)
    task_names = {}
    originals = set(observations)
    futures = []
    
    retry_after = 0.25
    with ThreadPoolExecutor() as executor:
        for task in tasks_iter:
            deps = task["dependencies"]
            # For naming:
            task_names[task["idx"]] = (
                task["tool"] if isinstance(task["tool"], str)
                else task["tool"].name
            )
            
            if deps and any(dep not in observations for dep in deps):
                # If we can't run yet, schedule a 'pending' task
                futures.append(
                    executor.submit(
                        schedule_pending_task,
                        task,
                        observations,
                        retry_after,
                        config
                    )
                )
            else:
                # Dependencies are satisfied, run now
                schedule_task({
                    "task": task,
                    "observations": observations,
                    "config": config
                })
        
        # Wait for parallel tasks
        wait(futures)
    
    # Convert new observations (excluding the original ones) to FunctionMessages
    tool_messages = []
    for idx in sorted(observations.keys() - originals):
        tool_messages.append(
            FunctionMessage(
                name=task_names[idx],
                content=str(observations[idx]),
                additional_kwargs={"idx": idx},
                tool_call_id=str(idx)
            )
        )
    
    return tool_messages
