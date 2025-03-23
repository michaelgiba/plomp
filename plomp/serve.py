import importlib.resources
import json

from plomp.core import PlompBuffer


def _get_template_plomp_content():
    """
    Loads the HTML template for displaying and interacting with Plomp buffer data.
    The template is loaded from the package resources.

    """

    path = importlib.resources.files("plomp.resources.templates").joinpath(
        "buffer_viewer.html"
    )
    print(path)
    with open(path) as f:
        return f.read()


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

    # Get HTML template
    html_template = _get_template_plomp_content()
    # Insert JSON data into the template
    html_with_data = html_template.replace("__PLOMP_BUFFER_JSON__", json_str)

    # Write to output file
    with open(output_uri, "w", encoding="utf-8") as f:
        f.write(html_with_data)
