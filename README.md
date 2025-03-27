# Plomp

A small python module for managing and debugging agent contexts.

Just 'plomp' it in and 'prompt' away


# Overview

Plomp has three main goals:
1. Provide observability into the execution of an agent(s)
2. Simplify and track context retrieval through `queries`
3. Integrate easily into existing code in an unopinionated way

# Example Usage


```python
import plomp

@plomp.wrap_prompt_fn
def prompt_llm(prompt: str) -> str:
    return ...

llm_response = prompt_llm("What's the weather today?")

for i in range(10):
    plomp.record_event(
        {"payload": f"accessed weather data from API: {i + 1}/10"},
        tags={"tool": "weather_api"},
    )


past_weather_events = plomp.filter(tags={"tool": ["weather_api"]}).last(3)
past_weather_events.record()

llm_response = prompt_llm(
    f"How has the temperature changed over the last three samples?: "
    + past_weather_events.to_dict()
)


plomp.write_html(plomp.buffer(), "out.html")
```


# Tracker

1. [X] Implement initial single-threaded `PlompBuffer` with decorators and manual invocations
2. [X] Handle `prompt`, `query` and `event` buffer events
3. [X] Implement intial barebones visualizer for static visualization
4. [] Insert example HTML file for example usage
5. [] Add richer examples directory
6. [] Expand tests for serving
7. [] Add support for concurrent buffer access
8. [] Add a mode where HTML live updates from an active buffer
