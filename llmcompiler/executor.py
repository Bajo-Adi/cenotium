# executor.py

"""Executor for LLMCompiler tasks."""
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

class FunctionExecutor:
    """Executes functions with isolated memory spaces."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize the executor with optional worker limit."""
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.memory = {}  # Isolated memory per function call
    
    def execute(
        self,
        tool: BaseTool,
        args: Dict[str, Any],
        call_id: str,
        config: Optional[RunnableConfig] = None
    ) -> Any:
        """Execute a tool with isolated memory."""
        try:
            # Initialize isolated memory for this call
            self.memory[call_id] = {}
            
            # Execute the tool
            result = tool.invoke(args, config)
            
            # Clean up memory after execution
            if call_id in self.memory:
                del self.memory[call_id]
            
            return result
        except Exception as e:
            if call_id in self.memory:
                del self.memory[call_id]
            raise e

class ExecutorPool:
    """Pool of function executors for parallel task execution."""
    
    def __init__(self, num_executors: int = 4):
        """Initialize the executor pool."""
        self.executors = [FunctionExecutor() for _ in range(num_executors)]
        self.current = 0
    
    def get_executor(self) -> FunctionExecutor:
        """Get the next available executor."""
        executor = self.executors[self.current]
        self.current = (self.current + 1) % len(self.executors)
        return executor
    
    def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        config: Optional[RunnableConfig] = None
    ) -> List[Any]:
        """Execute a batch of tasks in parallel."""
        results = []
        futures = []
        
        with ThreadPoolExecutor() as thread_pool:
            for task in tasks:
                executor = self.get_executor()
                future = thread_pool.submit(
                    executor.execute,
                    tool=task["tool"],
                    args=task["args"],
                    call_id=str(task["idx"]),
                    config=config
                )
                futures.append(future)
        
        # Collect results in order
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                results.append(f"ERROR: {str(e)}")
        
        return results
