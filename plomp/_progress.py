import importlib.resources
import json
import os
from plomp._core import PlompBuffer
from plomp._query import PlompBufferQuery
from typeguard import typechecked


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


def write_json(buffer: PlompBuffer, output_uri: str):
    json_contents = buffer.to_dict()

    with open(output_uri, "w", encoding="utf-8") as f:
        json.dump(json_contents, f)


@typechecked
def read_json(buffer: PlompBuffer, fpath: str) -> None:
    if not os.path.exists(fpath):
        raise ValueError(f"File {fpath} does not exist")

    with open(fpath) as f:
        input_json = json.load(f)

    if not isinstance(input_json, dict):
        raise ValueError(f"Malformed input, expected dict, got {type(input_json)}")

    if "buffer_items" not in input_json:
        raise ValueError("Malformed input, expected 'buffer_items' key in dict")

    for item in input_json["buffer_items"]:
        if item["type"] == "event":
            buffer.record_event(
                payload=item["data"]["payload"],
                tags=item["tags"],
            )
        elif item["type"] == "prompt":
            handle = buffer.record_prompt_start(
                prompt=item["data"]["prompt"],
                tags=item["tags"],
            )
            if item["data"].get("completion"):
                handle.complete(
                    item["data"]["completion"]["response"],
                )
        elif item["type"] == "query":
            buffer.record_query(
                plomp_query=PlompBufferQuery(
                    buffer,
                    matched_indices=item["data"]["matched_indices"],
                    op_name=item["data"]["op_name"],
                ),
                tags=item["tags"],
            )
        else:
            raise ValueError(
                f"Malformed input, unknown buffer item type: {item['type']!r}"
            )
