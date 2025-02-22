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

# Path to main and backup images
image_path = "capture.jpg"
backup_image = "capture_backup.jpg"


def generate_frames():
    """
    Continuously reads 'capture.jpg' safely and streams it as MJPEG.
    If there's a read error, it falls back to the last valid frame.
    """
    global last_valid_frame

    while True:
        try:
            with image_lock:  # Ensure no conflicts while reading
                if not os.path.exists(image_path):
                    print("[WARNING] capture.jpg not found. Using last valid frame.")
                    raise FileNotFoundError

                # Read the latest image into memory
                with open(image_path, "rb") as f:
                    frame = f.read()

                # Update the last valid frame
                last_valid_frame = frame

        except Exception as e:
            print(f"[ERROR] Issue reading capture.jpg: {e} - Using last valid frame.")

        # Always serve a frame (fallback to last valid if necessary)
        if last_valid_frame:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + last_valid_frame + b"\r\n"
            )
        else:
            print("[ERROR] No valid frame available.")

        time.sleep(0.05)  # Stream at ~20 FPS


@flask_app.route("/video_feed")
def video_feed():
    """
    Route that responds with the multipart/x-mixed-replace stream.
    This will be embedded as <img src="/video_feed"> on the main page.
    """
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@flask_app.route("/")
def index():
    """
    Main page to embed the video feed.
    """
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Live QWebEngineView Capture</title>
      </head>
      <body>
        <h1>Live QWebEngineView Capture</h1>
        <img src="/video_feed" width="800" height="600" />
      </body>
    </html>
    """
    return render_template_string(html)


def run_flask():
    """
    Run the Flask app on all interfaces at port 5001.
    debug=False and use_reloader=False to avoid multiple threads.
    """
    flask_app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)
