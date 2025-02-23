"""
http://localhost:5001/
"""

import os
import time
import threading

from flask import Flask, Response, render_template_string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ["E2B_API_KEY"] = os.getenv("E2B_API_KEY")

# Flask application setup
flask_app = Flask(__name__)

# Lock for thread safety when reading the image file
image_lock = threading.Lock()

# Store the last valid frame in memory
last_valid_frame = None

# Path to main image file
image_path = "capture.jpg"

# Path to text log file (this file should be updated dynamically)
text_log_path = "log.html"


import subprocess
import time
import sys
import socket
import threading


def is_port_in_use(port):
    """
    Check if a port is currently in use.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_next_available_port(start_port=5001):
    """
    Find the next available port, starting from start_port.
    """
    port = start_port
    while is_port_in_use(port):
        port += 1
    return port


# ISSUE: IDEALLY SHOULD END ON LACK OF A FRAME
def generate_frames():
    """
    Continuously reads 'capture.jpg' and streams it as MJPEG.
    If there's a read error OR the file does not exist,
    we end (break) the stream as requested.
    """
    global last_valid_frame

    while True:
        try:
            with image_lock:
                if not os.path.exists(image_path):
                    # "No incoming capture" -> break the stream
                    print("[WARNING] capture.jpg not found, ending video stream.")

                # Read the latest image into memory
                with open(image_path, "rb") as f:
                    frame = f.read()

                # Update the last valid frame
                last_valid_frame = frame

        except Exception as e:
            print(f"[ERROR] Issue reading capture.jpg: {e}")

        # Always serve a frame (fallback to last valid if necessary)
        if last_valid_frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + last_valid_frame + b"\r\n"
            )
        else:
            print("[ERROR] No valid frame available; ending video stream.")

        # Adjust frame rate as needed
        time.sleep(0.8)  # ~20 FPS


@flask_app.route("/video_feed")
def video_feed():
    """
    Route for the multipart/x-mixed-replace MJPEG stream.
    Embedded as <img src="/video_feed"> in the main page.
    """
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@flask_app.route("/text_feed")
def text_feed():
    """
    Streams the content of 'log.html' as raw HTML.
    """

    def text_stream():
        last_sent_text = None  # Cache to prevent duplicate content
        while True:
            try:
                if os.path.exists(text_log_path):
                    try:
                        with open(text_log_path, "r", encoding="utf-8") as f:
                            current_html = f.read().strip()
                    except UnicodeDecodeError:
                        print(
                            "[WARNING] UTF-8 decoding failed, using ISO-8859-1 instead."
                        )
                        with open(text_log_path, "r", encoding="ISO-8859-1") as f:
                            current_html = f.read().strip()

                    if (
                        current_html != last_sent_text
                    ):  # Send updates only when content changes
                        # Replace newlines with spaces to prevent SSE parsing issues
                        current_html = current_html.replace("\n", " ")
                        yield f"data: {current_html}\n\n"  # SSE format requires '\n\n'
                        last_sent_text = current_html
            except Exception as e:
                print(f"[ERROR] Could not read HTML log file: {e}")

            time.sleep(0.5)  # Adjust refresh rate

    return Response(text_stream(), mimetype="text/event-stream")


@flask_app.route("/")
def index():
    """
    Main page to embed both:
      - The video feed
      - A simple <div> that receives SSE text via JavaScript
    """
    # Basic HTML to show both streams
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Live QWebEngineView Capture & Text</title>
      </head>
      <body>
        <h2>Live VLM-Grounded Operator Agent Capture</h2>
        <img src="/video_feed" width="800" height="600" />
        
        <h2>Task Operator Log</h2>
        <div id="text-log" style="white-space: pre-wrap; border: 1px solid #ccc; padding: 10px;"></div>

        <script>
  // Connect to the /text_feed SSE endpoint
  const textLogDiv = document.getElementById('text-log');
  const evtSource = new EventSource('/text_feed');

  evtSource.onmessage = function(event) {
    textLogDiv.innerHTML = event.data;  // Inject raw HTML into the div
  };

  evtSource.onerror = function(err) {
    console.error("SSE error:", err);
  };
</script>

      </body>
    </html>
    """
    return render_template_string(html)


def run_flask(port=5001):
    """
    Run the Flask app on all interfaces at port 5001.
    """
    global image_path, text_log_path

    # Set up folder paths dynamically
    base_folder = f"server_data/{port}"
    os.makedirs(base_folder, exist_ok=True)  # Ensure directory exists

    image_path = os.path.join(base_folder, "capture.jpg")
    text_log_path = os.path.join(base_folder, "log.html")

    print(f"Starting Flask server on port {port}...")
    print(f"Using image path: {image_path}")
    print(f"Using text log path: {text_log_path}")

    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def start_flask_thread():
    """
    Creates and starts a daemon thread for the Flask server.
    """
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("✅ Flask server started on http://localhost:5001")


# if __name__ == "__main__":
#     # If you want to run this module standalone, just do:
#     start_flask_thread()

#     # Keep the main thread alive or do other stuff
#     while True:
#         try:
#             time.sleep(1)
#         except KeyboardInterrupt:
#             print("Shutting down...")
#             break

import multiprocessing


# Function to spawn a new Flask server dynamically
# Function to spawn a new Flask server dynamically using multiprocessing
def spawn_flask_server():
    """Finds the next available port and starts a Flask server as a separate process."""
    port = find_next_available_port()
    print(f"Spawning new Flask server on port {port}...")

    # Start the Flask server as a separate process
    process = multiprocessing.Process(target=run_flask, args=(port,))
    process.daemon = True  # Ensure the process terminates when the parent does
    process.start()

    time.sleep(2)  # Give the process time to initialize
    return port, process
