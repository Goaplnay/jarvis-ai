import webview
import threading
import server

def start_server():
    server.app.run(
        host="127.0.0.1",
        port=5000
    )

threading.Thread(
    target=start_server,
    daemon=True
).start()

webview.create_window(
    "JARVIS AI",
    "http://127.0.0.1:5000",
    width=1200,
    height=800
)

webview.start(
    debug=True,
    http_server=True
)