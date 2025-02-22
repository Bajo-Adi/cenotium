from os_computer_use.streaming import Sandbox, DisplayClient, Browser
from os_computer_use.sandbox_agent import SandboxAgent
from os_computer_use.logging_internal import Logger
import asyncio
import argparse
import threading
import os_computer_use.streaming_api
from os_computer_use.streaming_api import run_flask
import json
import os
from dotenv import load_dotenv

logger = Logger()

# Load environment variables from .env file
load_dotenv()

# Configure E2B
os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY")


async def start(user_input=None, output_dir=None, added_context=None):
    sandbox = None
    client = None
    message = None
    try:
        sandbox = Sandbox(template="desktop-dev-v2")

        # The display server won't work on desktop-dev-v2 since ffmpeg is not installed
        # client = DisplayClient(output_dir)
        # print("Starting the display server...")
        # stream_url = sandbox.start_stream()
        # print("(The display client will start in five seconds.)")
        # If the display client is opened before the stream is ready, it will close immediately
        # await client.start(stream_url, user_input or "Sandbox", delay=5)

        agent = SandboxAgent(sandbox, output_dir)

        print("Starting the VNC server...")
        sandbox.vnc_server.start()
        vnc_url = sandbox.vnc_server.get_url()

        print("Starting the VNC client...")
        browser = Browser()
        browser.start(vnc_url, user_input or "Sandbox")

        flask_thread = threading.Thread(target=run_flask)
        flask_thread.setDaemon(True)
        flask_thread.start()

        if user_input is None:
            return json.dumps(
                {
                    "status": "error",
                    "error_code": "EMPTY_INPUT",
                    "message": "The input query is empty. Please provide a valid prompt.",
                    "suggestions": [
                        "Ensure that the --prompt argument is passed when running the script.",
                        "Provide a non-empty string as input.",
                        "Check if the calling function correctly supplies the user input.",
                    ],
                },
                indent=4,
            )

        # Run the agent, and go back to the prompt if the user presses ctl-c
        else:
            try:
                response = agent.run(
                    user_input, added_context=added_context
                )  # Handed off to the black-box agent
                message = json.dumps(
                    {
                        "status": "success",
                        "message": "Agent processed the request successfully.",
                        "response": response,
                    },
                    indent=4,
                )
            except KeyboardInterrupt:
                logger.log("User interrupted the execution via keyboard input.")
                message = json.dumps(
                    {
                        "status": "error",
                        "error_code": "USER_INTERRUPTED",
                        "message": "Execution was interrupted by the user.",
                        "suggestions": [
                            "Restart the script if you stopped it accidentally.",
                            "Use a proper exit command instead of a keyboard interrupt.",
                        ],
                    },
                    indent=4,
                )
            except Exception as e:
                logger.log(f"An unexpected error occurred: {e}")
                message = json.dumps(
                    {
                        "status": "error",
                        "error_code": "UNKNOWN_ERROR",
                        "message": "An unexpected error occurred. Please check the logs for details.",
                        "suggestions": [
                            "Try restarting the script.",
                            "Check for missing dependencies or incorrect configurations.",
                        ],
                    },
                    indent=4,
                )

    finally:
        # if client:
        #    print("Stopping the display client...")
        #    try:
        #        await client.stop()
        #    except Exception as e:
        #        print(f"Error stopping display client: {str(e)}")

        if sandbox:
            print("Stopping the sandbox...")
            try:
                sandbox.kill()
            except Exception as e:
                print(f"Error stopping sandbox: {str(e)}")

        # if client:
        #    print("Saving the stream as mp4...")
        #    try:
        #        await client.save_stream()
        #    except Exception as e:
        #        print(f"Error saving stream: {str(e)}")

        print("Stopping the VNC client...")
        try:
            browser.stop()
        except Exception as e:
            print(f"Error stopping VNC client: {str(e)}")

    return message


def initialize_output_directory(directory_format):
    run_id = 1
    while os.path.exists(directory_format(run_id)):
        run_id += 1
    os.makedirs(directory_format(run_id), exist_ok=True)
    return directory_format(run_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt", type=str, required=True, help="User prompt for the agent"
    )
    # Added context for the task at hand
    parser.add_argument(
        "--context",
        type=str,
        default="",
        help="Additional context to provide to the agent",
    )
    args = parser.parse_args()

    output_dir = initialize_output_directory(lambda id: f"./output/run_{id}")
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        start(
            user_input=args.prompt,
            output_dir=output_dir,
            added_context=(
                args.context if args.context else None
            ),  # May or may not exist
        )
    )
