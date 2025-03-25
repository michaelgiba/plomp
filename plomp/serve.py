import http.server
import importlib.resources
import json
import os
import shutil
import socketserver
import tempfile
import threading
import time

from plomp.core import PlompBuffer


def _get_template_file(filename):
    path = importlib.resources.files("plomp.resources.templates").joinpath(filename)
    with open(path) as f:
        return f.read()


def write_html(buffer: PlompBuffer, output_uri: str):
    # Convert buffer to JSON string
    json_contents = buffer.to_dict()
    json_str = json.dumps(json_contents)

    # Get component files
    template = _get_template_file("buffer_viewer.html")
    css = _get_template_file("buffer_viewer.css")
    js = _get_template_file("buffer_viewer.js")

    # Assemble the HTML with components and data
    html = (
        template.replace("<!-- CSS_PLACEHOLDER -->", f"<style>\n{css}\n</style>")
        .replace("<!-- JS_PLACEHOLDER -->", f"<script>\n{js}\n</script>")
        .replace("__PLOMP_BUFFER_JSON__", json_str)
    )

    # Write to output file
    with open(output_uri, "w", encoding="utf-8") as f:
        f.write(html)


def serve_buffer(buffer: PlompBuffer, port: int = 9700, update_interval: float = 1.0):
    """
    Serve a PlompBuffer via HTTP server.

    Args:
        buffer: The PlompBuffer to serve
        port: Port to serve on (default 9700)
        update_interval: How often to update the HTML file in seconds (default 1.0)
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    html_path = os.path.join(temp_dir, "index.html")

    # Define the handler and set the directory
    handler = http.server.SimpleHTTPRequestHandler

    def update_html():
        while True:
            write_html(buffer, html_path)
            time.sleep(update_interval)

    # Start the HTML update thread
    update_thread = threading.Thread(target=update_html, daemon=True)
    update_thread.start()

    # Change to the temp directory and start the server
    os.chdir(temp_dir)
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving buffer at http://localhost:{port}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
