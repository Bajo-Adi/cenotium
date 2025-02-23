# output_parser.py

"""Output parser for LLMCompiler."""
import ast
import re
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers.transform import BaseTransformOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from typing_extensions import TypedDict

THOUGHT_PATTERN = r"Thought: ([^\n]*)"
ACTION_PATTERN = r"\n*(\d+)\. (\w+)\((.*)\)(\s*#\w+\n)?"
ID_PATTERN = r"\$\{?(\d+)\}?"

def _ast_parse(arg: str) -> Any:
    """Parse string arguments into Python objects."""
    try:
        return ast.literal_eval(arg)
    except Exception:
        return arg

def _parse_llm_compiler_action_args(args: str, tool: Union[str, BaseTool]) -> dict:
    """Parse tool arguments from string format."""
    if args == "":
        return {}
    
    extracted_args = {}
    tool_key = None
    prev_idx = None
    
    # Parse tool arguments if it's a BaseTool
    if isinstance(tool, BaseTool):
        for key in tool.args.keys():
            if f"{key}=" in args:
                idx = args.index(f"{key}=")
                if prev_idx is not None:
                    extracted_args[tool_key] = _ast_parse(args[prev_idx:idx].strip().rstrip(","))
                args = args.split(f"{key}=", 1)[1]
                tool_key = key
                prev_idx = 0
        
        if prev_idx is not None:
            extracted_args[tool_key] = _ast_parse(args[prev_idx:].strip().rstrip(",").rstrip(")"))
    
    return extracted_args

def _get_dependencies_from_graph(idx: int, tool_name: str, args: Dict[str, Any]) -> List[int]:
    """Extract task dependencies from arguments."""
    if tool_name == "join":
        # A “join” step typically depends on all prior steps
        return list(range(1, idx))
    
    # Find dependencies in arguments
    def extract_deps(arg_str: str) -> List[int]:
        matches = re.findall(ID_PATTERN, str(arg_str))
        return [int(match) for match in matches]
    
    deps = []
    for arg_value in args.values():
        deps.extend(extract_deps(str(arg_value)))
    
    return sorted(list(set(deps)))

class Task(TypedDict):
    """Task definition for LLMCompiler."""
    idx: int
    tool: Union[BaseTool, str]
    args: Dict[str, Any]
    dependencies: List[int]
    thought: Optional[str]

def instantiate_task(
    tools: List[BaseTool],
    idx: int,
    tool_name: str,
    args: str,
    thought: Optional[str] = None
) -> Task:
    """Create a task instance from parsed components."""
    if tool_name == "join":
        tool = "join"
    else:
        try:
            tool = tools[[t.name for t in tools].index(tool_name)]
        except ValueError as e:
            raise OutputParserException(f"Tool {tool_name} not found.") from e
    
    tool_args = _parse_llm_compiler_action_args(args, tool)
    dependencies = _get_dependencies_from_graph(idx, tool_name, tool_args)
    
    return Task(
        idx=idx,
        tool=tool,
        args=tool_args,
        dependencies=dependencies,
        thought=thought,
    )

class LLMCompilerPlanParser(BaseTransformOutputParser[Dict]):
    """Parser for LLMCompiler output."""
    tools: List[BaseTool]

    def _transform(self, input: Union[str, BaseMessage, List[Union[str, BaseMessage]]]) -> Iterator[Task]:
        """Transform input into tasks."""
        texts = []
        thought = None
        
        # Handle input which could be string, message, or list
        if isinstance(input, list):
            chunks = input
        else:
            chunks = [input]
        
        for chunk in chunks:
            # Convert chunk to text
            if isinstance(chunk, str):
                text = chunk
            elif isinstance(chunk, BaseMessage):
                text = chunk.content
            else:
                text = str(chunk)
            
            # Process the text into tasks
            for task, new_thought in self.ingest_token(text, texts, thought):
                thought = new_thought
                if task:
                    yield task
        
        # Process any remaining text
        if texts:
            task, _ = self._parse_task("".join(texts), thought)
            if task:
                yield task

    def parse(self, text: str) -> List[Task]:
        """Parse complete text into tasks."""
        return list(self._transform(text))

    def stream(
        self,
        input: Union[str, BaseMessage, List[Union[str, BaseMessage]]],
        config: Optional[RunnableConfig] = None,
        **kwargs
    ) -> Iterator[Task]:
        """Stream parse results."""
        yield from self._transform(input)

    def ingest_token(
        self,
        token: str,
        buffer: List[str],
        thought: Optional[str]
    ) -> Iterator[Tuple[Optional[Task], str]]:
        """Process incoming tokens line by line."""
        buffer.append(token)
        
        if "\n" in token:
            buffer_ = "".join(buffer).split("\n")
            suffix = buffer_[-1]
            
            for line in buffer_[:-1]:
                task, thought = self._parse_task(line, thought)
                if task:
                    yield task, thought
            
            buffer.clear()
            buffer.append(suffix)

    def _parse_task(self, line: str, thought: Optional[str] = None) -> Tuple[Optional[Task], Optional[str]]:
        """Parse a single line into a task or update the 'thought'."""
        task = None
        
        # Match a line that has the 'Thought:' pattern
        if match := re.match(THOUGHT_PATTERN, line):
            thought = match.group(1)

        # Match lines that look like: '1. SomeTool(args...)'
        elif match := re.match(ACTION_PATTERN, line):
            idx, tool_name, args, _ = match.groups()
            idx = int(idx)
            task = instantiate_task(
                tools=self.tools,
                idx=idx,
                tool_name=tool_name,
                args=args,
                thought=thought
            )
            # Reset the thought after creating a task
            thought = None
        
        return task, thought
