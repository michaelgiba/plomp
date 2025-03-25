import importlib.resources
import json

from plomp.core import PlompBuffer


def _get_template_file(filename):
    """
    Loads a template file from the package resources.
    """
    path = importlib.resources.files("plomp.resources.templates").joinpath(filename)
    with open(path) as f:
        return f.read()


def _get_template_plomp_content():
    """
    Loads the HTML template for displaying and interacting with Plomp buffer data.
    The template is loaded from the package resources.
    """
    return _get_template_file("buffer_viewer.html")


def assemble_and_write_buffer_viewer(output_uri):
    """
    Assemble the buffer viewer HTML from separate components and write to file.
    """
    # Get component files
    template = _get_template_file("buffer_viewer.html")
    css = _get_template_file("buffer_viewer.css")
    js = _get_template_file("buffer_viewer.js")

    # Assemble the final HTML
    html = template.replace(
        "<!-- CSS_PLACEHOLDER -->", f"<style>\n{css}\n</style>"
    ).replace("<!-- JS_PLACEHOLDER -->", f"<script>\n{js}\n</script>")

    # Write to the output file
    with open(output_uri, "w", encoding="utf-8") as f:
        f.write(html)

    return output_uri


def write_html(buffer: PlompBuffer, output_uri: str):
    """
    Converts the content of a plomp buffer into a self contained HTML
    page which allows for a user to analyze the buffer that was created.

    1. converts the buffer to json
    2. loads the lightweight HTML and javascript from a location
    3. Inserts the buffer json into the page
    4. writes to an output location `output_uri`
    """
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
