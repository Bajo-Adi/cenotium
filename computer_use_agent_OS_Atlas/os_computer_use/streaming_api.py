"""
2 Streams: Video Feed and Text from the Agent decisions being made
"""

import time
from flask import Flask, Response, render_template_string

app = Flask(__name__)


def generate_frames():
    while True:
        try:
            with open("capture.jpg", "rb") as f:
                frame = f.read()
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        except Exception as e:
            print("Error reading capture.jpg:", e)
        time.sleep(0.2)  # roughly match the capture rate


@app.route("/video_feed")
def video_feed():
    # Serve the MJPEG stream.
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/")
def index():
    # Embed the MJPEG stream in a simple HTML page.
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>QWebEngineView Stream</title>
      </head>
      <body>
        <h1>Live QWebEngineView Capture</h1>
        <img src="/video_feed" width="800" height="600">
      </body>
    </html>
    """
    return render_template_string(html)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
