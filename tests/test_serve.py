import datetime as dt
import io
import json
import random
import sys
import textwrap
from datetime import datetime, timedelta

import pytest

import plomp


def test_serialization():
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
                "message": f"Message {i} about {random.choice(topics)}",
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

    plomp.write_html(buffer, "/home/michaelgiba/out.html")
