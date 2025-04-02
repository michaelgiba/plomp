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
    json_contents = buffer.to_dict()
    json_str = json.dumps(json_contents)
    template = _get_template_file("index.html")
    html = template.replace(
        "<!-- insert plomp JSON data here -->",
        f"window.__PLOMP_BUFFER_JSON__ = {json_str};",
    )

    with open(output_uri, "w", encoding="utf-8") as f:
        f.write(html)
