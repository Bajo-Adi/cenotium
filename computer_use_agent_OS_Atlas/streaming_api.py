"""
2 Streams: Video Feed and Text from the Agent decisions being made
"""

from flask import Flask, render_template_string, send_from_directory
import os

app = Flask(__name__, static_folder="hls")


@app.route("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>HLS Streaming Viewer</title>
      </head>
      <body>
        <h1>HLS Streaming (M3U8)</h1>
        <video width="800" height="600" controls autoplay>
          <source src="/stream.m3u8" type="application/x-mpegURL">
        </video>
        <p>If the video does not play, your browser may not support HLS natively.</p>
      </body>
    </html>
    """
    return render_template_string(html)


# Optional: Serve files from the hls directory explicitly
@app.route("/<path:filename>")
def serve_hls(filename):
    return send_from_directory(app.static_folder, filename)


if __name__ == "__main__":
    # Run the Flask server on port 5001 (or any port you prefer)
    app.run(host="0.0.0.0", port=5001, debug=True)
