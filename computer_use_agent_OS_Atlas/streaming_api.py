"""
2 Streams: Video Feed and Text from the Agent decisions being made
"""

import cv2
import numpy as np
import requests
from flask import Flask, Response

app = Flask(__name__)

# FFmpeg is already running and serving the stream here
STREAM_URL = "http://localhost:8080"  # Change if needed


def generate_mjpeg():
    """Fetches the existing FFmpeg stream and serves it as MJPEG."""
    print("Client connected, fetching stream...")

    with requests.get(STREAM_URL, stream=True) as response:
        chunk_size = 1024 * 64  # Read in chunks (adjust if needed)
        buffer = b""  # Buffer to store incomplete frame data

        for chunk in response.iter_content(chunk_size):
            buffer += chunk

            # Find MPEG-TS frame boundaries (basic sync)
            start_idx = buffer.find(b"\x00\x00\x01")  # Start of an MPEG frame
            if start_idx != -1:
                frame_data = buffer[start_idx:]
                buffer = b""  # Clear buffer after extracting frame

                # Convert MPEG-TS frame to OpenCV image
                np_frame = np.frombuffer(frame_data, np.uint8)
                frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)

                if frame is None:
                    continue  # Skip invalid frames

                # Convert frame to JPEG format
                success, jpeg = cv2.imencode(".jpg", frame)
                if not success:
                    continue

                # Yield MJPEG frame
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n"
                )


@app.route("/stream")
def stream():
    """Serves the live stream only when accessed."""
    return Response(
        generate_mjpeg(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
