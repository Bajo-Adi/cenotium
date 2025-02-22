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
text_log_path = "os_computer_use/task_operator_log.txt"


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
                    break

                # Read the latest image into memory
                with open(image_path, "rb") as f:
                    frame = f.read()

                # Update the last valid frame
                last_valid_frame = frame

        except Exception as e:
            print(f"[ERROR] Issue reading capture.jpg: {e}")
            # Decide if you want to end the stream on read errors
            break

        # Always serve a frame (fallback to last valid if necessary)
        if last_valid_frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + last_valid_frame + b"\r\n"
            )
        else:
            print("[ERROR] No valid frame available; ending video stream.")
            break

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
    Route that streams text from 'task_operator_log.txt' using
    Server-Sent Events (SSE).
    """

    def text_stream():
        last_sent_text = None  # Cache to prevent sending duplicate text
        while True:
            try:
                if os.path.exists(text_log_path):
                    with open(text_log_path, "r") as f:
                        current_text = f.read().strip()

                    if current_text != last_sent_text:  # Only send updates
                        yield f"data: {current_text}\n\n"
                        last_sent_text = current_text

            except Exception as e:
                print(f"[ERROR] Could not read text log file: {e}")

            time.sleep(1)  # Adjust refresh rate

    # Use the 'text/event-stream' MIME type for SSE
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
          // Simple JavaScript to connect to /text_feed SSE endpoint
          const textLogDiv = document.getElementById('text-log');
          const evtSource = new EventSource('/text_feed');

          evtSource.onmessage = function(event) {
            textLogDiv.textContent = event.data;
          };

          evtSource.onerror = function(err) {
            console.error("SSE error:", err);
          };
        </script>
      </body>
    </html>
    """
    return render_template_string(html)


def run_flask():
    """
    Run the Flask app on all interfaces at port 5001.
    """
    flask_app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)


def start_flask_thread():
    """
    Creates and starts a daemon thread for the Flask server.
    """
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("✅ Flask server started on http://localhost:5001")


if __name__ == "__main__":
    # If you want to run this module standalone, just do:
    start_flask_thread()

    # Keep the main thread alive or do other stuff
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
            break
