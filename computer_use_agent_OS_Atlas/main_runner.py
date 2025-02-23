from fastapi import FastAPI
from pydantic import BaseModel
from threading import Thread
import asyncio
from typing import Optional

# Assuming these functions are defined in your main module
from main import start, initialize_output_directory

app = FastAPI()


class TaskRequest(BaseModel):
    prompt: str
    context: Optional[str] = None


def run_task_in_thread(prompt: str, context: Optional[str]):
    """
    Function to start a new thread for running the task.
    This ensures that each request runs in an isolated thread.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize output directory
        output_dir = initialize_output_directory(lambda id: f"./output/run_{id}")

        # Run the task inside the event loop
        loop.run_until_complete(
            start(
                user_input=prompt,
                output_dir=output_dir,
                added_context=context if context else None,
            )
        )
        loop.close()
    except Exception as e:
        print(f"Error in thread: {e}")


@app.post("/run-task/")
async def run_task(request: TaskRequest):
    """
    Endpoint to trigger a background task in a separate thread.
    """
    thread = Thread(target=run_task_in_thread, args=(request.prompt, request.context))
    thread.daemon = True  # Allows thread to exit when main process exits
    thread.start()

    return {"message": f"Task started successfully in thread {thread.name}."}


@app.post("/run-perplexity/")
async def run_perplexity(request: TaskRequest):
    """
    Endpoint to trigger a Perplexity task in a separate thread.
    """
    thread = Thread(target=run_task_in_thread, args=(request.prompt, request.context))
    thread.daemon = True  # Allows thread to exit when main process exits
    thread.start()

    return {"message": f"Task started successfully in thread {thread.name}."}


@app.post("/run-twilio/")
def run_twilio(request: TaskRequest):
    """
    Endpoint to trigger a Twilio task in a separate thread.
    """
    thread = Thread(target=run_task_in_thread, args=(request.prompt, request.context))
    thread.daemon = True  # Allows thread to exit when main process exits
    thread.start()

    return {"message": f"Task started successfully in thread {thread.name}."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
