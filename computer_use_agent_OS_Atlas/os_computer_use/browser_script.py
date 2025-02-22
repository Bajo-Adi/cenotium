import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
import platform

try:
    app = QApplication(sys.argv)
    
    viewer = QWebEngineView()
    
    settings = viewer.settings()
    settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
    settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
    settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
    settings.setAttribute(QWebEngineSettings.AllowRunningInsecureContent, True)
    
    if platform.system() == "Darwin":
        viewer.setWindowFlags(Qt.Window)
    else:
        viewer.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
    
    viewer.setUrl(QUrl(sys.argv[1]))
    viewer.setWindowTitle(sys.argv[2])
    viewer.setGeometry(100, 100, 800, 600)
    viewer.show()
    
    sys.exit(app.exec_())
except Exception as e:
    print(f"Error: {e}")