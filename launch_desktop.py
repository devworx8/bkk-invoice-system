#!/usr/bin/env python3
"""Launch BKK Invoice System as a native desktop application."""

import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(port: int, timeout: float = 30.0) -> bool:
    """Block until the Streamlit server responds or *timeout* elapses."""
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/_stcore/health"
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.4)
    return False


def main() -> None:
    try:
        import webview  # pywebview
    except ImportError:
        print(
            "pywebview is required for the desktop app.\n"
            "Install it with:  pip install pywebview\n"
            "On Linux you may also need:  sudo apt install python3-gi gir1.2-webkit2-4.1"
        )
        sys.exit(1)

    port = _find_free_port()
    app_dir = Path(__file__).resolve().parent

    # Start Streamlit in the background
    server = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            str(app_dir / "app.py"),
            "--server.port", str(port),
            "--server.address", "127.0.0.1",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--global.developmentMode", "false",
        ],
        cwd=str(app_dir),
    )

    try:
        if not _wait_for_server(port):
            print("Streamlit server failed to start within 30 seconds.")
            server.terminate()
            sys.exit(1)

        url = f"http://127.0.0.1:{port}"
        window = webview.create_window(
            "BKK Invoice System",
            url,
            width=1320,
            height=860,
            min_size=(960, 640),
        )
        webview.start()
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == "__main__":
    main()
