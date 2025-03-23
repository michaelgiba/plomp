import datetime as dt
import io
import json
import sys
import textwrap

import pytest

import plomp


def test_serialization():
    buffer = plomp.buffer(key="test_serialization")
    type_data_and_tags = [
        (
            "prompt",
            {
                "data": {
                    "prompt": "What would you like to say to bob?",
                    "response": "Hello?",
                },
                "tags": {"model": "claude"},
            },
        ),
        (
            "event",
            {
                "data": {
                    "message": "Hello?",
                    "from": "bob",
                    "to": "alice",
                },
                "tags": {"event_type": "chat"},
            },
        ),
        (
            "prompt",
            {
                "data": {
                    "prompt": textwrap.dedent(
                        """
                        You have recieved a message from bob saying 'Hello?'. How would you like to respond?
                    """
                    ),
                    "response": "Hi there",
                },
                "tags": {"model": "claude"},
            },
        ),
        (
            "event",
            {
                "data": {
                    "message": "Hello?",
                    "from": "alice",
                    "to": "bob",
                },
                "tags": {"event_type": "chat"},
            },
        ),
    ]

    for type_, data_and_tags in type_data_and_tags:
        if type_ == "prompt":
            prompt = data_and_tags["data"]["prompt"]
            response = data_and_tags["data"]["response"]
            tags = data_and_tags["tags"]
            plomp.record_prompt(prompt, tags=tags, buffer=buffer).complete(response)
        elif type_ == "event":
            payload = data_and_tags["data"]
            tags = data_and_tags["tags"]
            plomp.record_event(payload, tags=tags, buffer=buffer)
        else:
            raise ValueError(f"Unknown type: {type_}")

    plomp.write_html(buffer, "/home/michaelgiba/out.html")
