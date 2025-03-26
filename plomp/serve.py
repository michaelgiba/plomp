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
