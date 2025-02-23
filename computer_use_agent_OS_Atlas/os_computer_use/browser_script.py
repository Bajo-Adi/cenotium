import sys
import os
import platform
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

try:
    # Ensure proper arguments
    if len(sys.argv) < 4:
        print("Usage: python browser_script.py <URL> <Window Title> <Port Number>")
        sys.exit(1)

    url = sys.argv[1]
    title = sys.argv[2]
    port = sys.argv[3]  # Get port number from command line
    save_directory = f"server_data/{port}"  # Dynamic save path based on port

    # Ensure the directory exists
    os.makedirs(save_directory, exist_ok=True)

    app = QApplication(sys.argv)
    viewer = QWebEngineView()

    # Configure viewer settings
    settings = viewer.settings()
    settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)

    if platform.system() == "Darwin":
        viewer.setWindowFlags(Qt.Window)
    else:
        viewer.setWindowFlags(
            Qt.Window
            | Qt.CustomizeWindowHint
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
        )

    # Capture function to save the image under the specific port directory
    def capture_view():
        pixmap = viewer.grab()
        image_path = os.path.join(
            save_directory, "capture.jpg"
        )  # Save under specific port
        pixmap.save(image_path, "JPG")
        print(f"Captured: {image_path}")

    # Timer to capture the view periodically
    timer = QTimer()
    timer.timeout.connect(capture_view)
    timer.start(200)  # Capture every 200ms

    # Set up the viewer
    viewer.setUrl(QUrl(url))
    viewer.setWindowTitle(title)
    viewer.setGeometry(100, 100, 800, 600)
    viewer.show()

    sys.exit(app.exec_())

except Exception as e:
    print(f"Error: {e}")
