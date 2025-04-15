import os
import random
import tempfile
from datetime import datetime, timedelta
import pytest

import plomp
import json


@pytest.fixture
def temp_html_file():
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as temp_file:
        yield temp_file.name
    # Cleanup after test
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


def test_serialization(temp_html_file):
    buffer = plomp.buffer(key="test_serialization")

    # Base data templates
    prompt_templates = [
        "What would you like to say to {recipient}?",
        "How would you respond to {recipient}'s message?",
        "Write a message to {recipient} about {topic}",
        "Compose a {tone} response to {recipient}",
        "Help me draft a message to {recipient} regarding {topic}",
    ]

    topics = [
        "the project",
        "yesterday's meeting",
        "next week's deadline",
        "the budget",
        "team collaboration",
        "vacation plans",
        "quarterly review",
        "new product launch",
        "client feedback",
        "internal process",
        "system upgrade",
        "staff training",
        "market research",
        "customer support",
        "strategic planning",
        "resource allocation",
        "website redesign",
        "sales strategy",
    ]

    tones = [
        "formal",
        "casual",
        "friendly",
        "serious",
        "urgent",
        "humorous",
        "professional",
        "enthusiastic",
        "concerned",
        "apologetic",
        "grateful",
        "direct",
        "diplomatic",
        "supportive",
        "inquisitive",
    ]

    names = [
        "alice",
        "bob",
        "charlie",
        "diana",
        "evan",
        "fiona",
        "greg",
        "hannah",
        "ian",
        "julia",
        "kevin",
        "lisa",
        "michael",
        "natalie",
        "olivia",
        "paul",
        "quinn",
        "rachel",
        "samuel",
        "tina",
        "victor",
        "wendy",
    ]

    models = [
        "claude",
        "gpt4",
        "llama",
        "mistral",
        "gemini",
        "palm",
        "bert",
        "falcon",
        "davinci",
        "chinchilla",
        "bloom",
        "pythia",
        "baichuan",
        "qwen",
        "yi",
    ]

    for i in range(2000):
        entry_type = random.choice(["prompt", "event"])
        if entry_type == "prompt":
            recipient = random.choice(names)
            topic = random.choice(topics)
            tone = random.choice(tones)
            model = random.choice(models)

            prompt = random.choice(prompt_templates).format(
                recipient=recipient, topic=topic, tone=tone
            )

            # Sometimes include a response
            response = (
                f"Here's a {tone} message about {topic}"
                if random.random() > 0.3
                else None
            )

            tags = {"model": model}
            if random.random() > 0.7:
                tags["importance"] = random.choice(["low", "medium", "high"])

            handle = plomp.record_prompt(prompt, tags=tags, buffer=buffer)
            if response:
                handle.complete(response)

        else:  # event
            sender = random.choice(names)
            recipient = random.choice([n for n in names if n != sender])

            payload = {
                "plomp_display_event_type": "sent_message",
                "plomp_display_text": f"Message {i} about {random.choice(topics)}",
                "from": sender,
                "to": recipient,
                "timestamp": (
                    datetime.now() - timedelta(minutes=random.randint(0, 1000))
                ).isoformat(),
            }

            tags = {
                "event_type": random.choice(["chat", "notification", "system", "alert"])
            }

            plomp.record_event(payload, tags=tags, buffer=buffer)

        buffer.last(10).filter(
            tags_filter={
                "event_type": random.choice(["chat", "notification", "system", "alert"])
            }
        ).record(tags={})

    # Write to the temp file provided by the fixture
    plomp.write_html(buffer, temp_html_file)

    # Verify the file contains expected elements
    with open(temp_html_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert len(content) > 0


def test_readme_example(temp_html_file):
    buffer = plomp.buffer(key="test_readme_example")

    @plomp.wrap_prompt_fn(buffer=buffer)
    def prompt_llm(prompt: str) -> str:
        return "<EXAMPLE LLM RESPONSE>"

    _ = prompt_llm("What's the weather today?")

    for i in range(4):
        plomp.record_event(
            {
                "plomp_display_event_type": "weather_data_accessed",
                "plomp_display_text": f"accessed weather data from API: {i + 1}/10",
                "value": random.random(),
            },
            tags={"tool": "weather_api"},
            buffer=buffer,
        )

    past_weather_events = buffer.filter(tags_filter={"tool": ["weather_api"]}).last(3)
    past_weather_events.record(tags={"type": "recent_weather_queries"})

    _ = prompt_llm(
        "How has the temperature changed over the last three samples?: "
        + str(past_weather_events.to_dict())
    )

    plomp.write_html(buffer, temp_html_file)

    # Verify the file contains expected elements
    with open(temp_html_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert len(content) > 0


def test_write_json(temp_html_file):
    buffer = plomp.buffer(key="test_json_serialization")

    handle = plomp.record_prompt(
        "Test prompt", tags={"type": "json_test"}, buffer=buffer
    )
    handle.complete("Test response")

    plomp.record_event(
        {
            "plomp_display_event_type": "test_event",
            "plomp_display_text": "Test event for JSON serialization",
            "value": 123,
        },
        tags={"type": "json_test_event"},
        buffer=buffer,
    )

    new_buffer = plomp.buffer(key="test_json_serialization_after_read")
    with tempfile.NamedTemporaryFile() as f:
        plomp.write_json(buffer, f.name)
        content = json.load(f)
        assert isinstance(content["buffer_items"], list)
        assert len(content["buffer_items"]) == 2

        plomp.read_json(new_buffer, f.name)
        assert len(new_buffer) == 2

        assert new_buffer[0].tags == buffer[0].tags
        assert new_buffer[1].type_ == buffer[1].type_
