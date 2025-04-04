# Plomp

A small python module for managing and debugging agent contexts.

Just 'plomp' it in and 'prompt' away


# Overview

Plomp is designed to easily integrate into python programs which invoke an LLM over multiple 
steps and provide some useful benefits such as visualizing progress and making context retrival easier.

Plomp has three main goals:
1. Provide simple observability into execution multistep LLM prompts ("agents" if you must)
2. Track and manage context retrieval
3. Integrate easily into existing code in an unopinionated way


# Example Usage

For a richer example look at the example project which simulates the game surivivor at https://michaelgiba.github.io/survivor/static/plomp.html with the repo here https://github.com/michaelgiba/survivor


A simpler example below:

```python
import plomp

@plomp.wrap_prompt_fn()
def prompt_llm(prompt: str) -> str:
    return "<EXAMPLE LLM RESPONSE>"

llm_response = prompt_llm("What's the weather today?")

for i in range(4):
    plomp.record_event(
        {
            "plomp_display_event_type": "weather_data_accessed",
            "plomp_display_text": f"accessed weather data from API: {i + 1}/10",
            "value": random.random(),
        },
        tags={"tool": "weather_api"},
    )

past_weather_events = plomp.buffer().filter(tags_filter={"tool": ["weather_api"]}).last(3)
past_weather_events.record(tags={"type": "recent_weather_queries"})

llm_response = prompt_llm(
    f"How has the temperature changed over the last three samples?: "
    + str(past_weather_events.to_dict())
)

plomp.write_html(plomp.buffer(), "progress.html")
```

This would produce a self-contained HTML page which looks like this:

![Plomp UI Example](img/example-recording.gif)


# Structure

Plomp revolves around a centralized buffer which stores three different types of sequential records:

1. "Events": Discrete events which happened that could useful future context for decision making
2. "Queries": An expression which matches previous events based on user provided logic
3. "Prompts": A record of a prompt to an LLM and the response recieved



# Installation

```bash
pip install plomp
```

For development:

```bash
pip install plomp[dev]
```


