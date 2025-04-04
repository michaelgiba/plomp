"""
Plomp Query Example

This example demonstrates Plomp's query functionality:
- Filtering items by tags
- Using different query methods
- Combining queries
- Recording queries for visualization
"""

import plomp
import random


def simulate_llm_response(prompt: str) -> str:
    """Simulate a response from an LLM."""
    return f"This is a simulated response to: '{prompt[:30]}...'"


@plomp.wrap_prompt_fn()
def ask_llm(prompt: str, *, tags=None) -> str:
    """A function that calls an LLM with Plomp tracking."""
    # In a real application, this would call an actual LLM API
    return simulate_llm_response(prompt)


def record_sample_data():
    """Populate the buffer with sample data for querying."""
    # Record some prompts with different tags and then use their responses
    london_response = ask_llm(
        "Tell me about the weather in London",
        plomp_extra_tags={"domain": "weather", "location": "London"},
    )

    # Extract mock temperature from the response (in a real app, this would parse the actual response)
    london_temp = 18 + random.uniform(-2, 2)

    # Record an event using the response content
    plomp.record_event(
        payload={
            "plomp_display_event_type": "weather_info_processed",
            "plomp_display_text": f"Processed London weather info: {london_temp:.1f}°C",
            "value": london_temp,
            "unit": "celsius",
            "source": "LLM response",
            "response_excerpt": london_response[:40],
        },
        tags={"location": "London", "domain": "weather", "data_source": "llm_derived"},
    )

    ny_response = ask_llm(
        "What's the forecast for New York?",
        plomp_extra_tags={"domain": "weather", "location": "New York"},
    )

    # Extract mock temperature from the response
    ny_temp = 22 + random.uniform(-3, 3)

    # Record event using the New York response
    plomp.record_event(
        payload={
            "plomp_display_event_type": "weather_info_processed",
            "plomp_display_text": f"Processed New York weather info: {ny_temp:.1f}°C",
            "value": ny_temp,
            "unit": "celsius",
            "source": "LLM response",
            "response_excerpt": ny_response[:40],
        },
        tags={
            "location": "New York",
            "domain": "weather",
            "data_source": "llm_derived",
        },
    )

    quantum_response = ask_llm(
        "Explain quantum computing",
        plomp_extra_tags={"domain": "science", "topic": "physics"},
    )

    # Create an event based on the science topic response
    term_count = len(quantum_response.split()) // 5  # Simplified analysis of response
    plomp.record_event(
        payload={
            "plomp_display_event_type": "technical_terms_identified",
            "plomp_display_text": f"Identified approximately {term_count} technical terms in quantum computing explanation",
            "term_count": term_count,
            "domain": "physics",
            "complexity_score": 0.8,
            "response_excerpt": quantum_response[:40],
        },
        tags={"domain": "science", "topic": "physics", "analysis_type": "terminology"},
    )

    # Record additional sensor data events
    for i in range(3):
        # Generate sensor data that could complement the LLM-derived weather info
        plomp.record_event(
            payload={
                "plomp_display_event_type": "temperature_reading",
                "plomp_display_text": f"Temperature reading: {20 + random.uniform(-5, 5):.1f}°C",
                "value": 20 + random.uniform(-5, 5),
                "unit": "celsius",
            },
            tags={
                "sensor_id": f"sensor_{i % 3 + 1}",
                "domain": "weather",
                "reading_type": "temperature",
            },
        )

        plomp.record_event(
            payload={
                "plomp_display_event_type": "humidity_reading",
                "plomp_display_text": f"Humidity reading: {50 + random.uniform(-20, 20):.1f}%",
                "value": 50 + random.uniform(-20, 20),
                "unit": "percent",
            },
            tags={
                "sensor_id": f"sensor_{i % 3 + 1}",
                "domain": "weather",
                "reading_type": "humidity",
            },
        )


def run_query_examples():
    """Demonstrate different query capabilities."""
    buffer = plomp.buffer()

    # 1. Basic filtering by tag
    weather_items = buffer.filter(tags_filter={"domain": "weather"})
    print(f"Found {len(weather_items)} weather-related items")

    # Record this query in the buffer
    weather_items.record(tags={"query_purpose": "weather_data_collection"})

    # 2. More specific filtering with multiple tag conditions
    london_weather = buffer.filter(
        how="all",  # Require all conditions to match
        tags_filter={"domain": "weather", "location": "London"},
    )
    print(f"Found {len(london_weather)} London weather items")

    # 3. Using custom filter functions - find events derived from LLM responses
    llm_derived_data = buffer.where(
        truth_fn=lambda item: (
            item.type_.value == "event"
            and "data_source" in item.tags
            and item.tags["data_source"] == "llm_derived"
        )
    )
    print(f"Found {len(llm_derived_data)} events derived from LLM responses")
    llm_derived_data.record(tags={"query_purpose": "llm_data_analysis"})

    # 4. Combining queries - union
    combined_query = london_weather.union(llm_derived_data)
    print(f"Union query has {len(combined_query)} items")

    # 5. Getting the most recent items
    recent_events = buffer.filter(tags_filter={"domain": "weather"}).last(3)
    print(f"Found {len(recent_events)} recent weather events")
    recent_events.record(tags={"query_purpose": "recent_weather_summary"})

    # 6. Using the query results to generate a new prompt
    summary_prompt = "Summarize the following weather data:\n"
    for idx, item in enumerate(recent_events):
        if item.type_.value == "event":
            data = item.event.payload
            summary_prompt += (
                f"{idx + 1}. {data.get('plomp_display_text', 'Unknown')}\n"
            )

    response = ask_llm(summary_prompt, plomp_extra_tags={"purpose": "weather_summary"})

    # Create a final event with the analysis result
    plomp.record_event(
        payload={
            "plomp_display_event_type": "weather_summary_generated",
            "plomp_display_text": "Generated weather data summary from recent events",
            "summary": response[:100],
            "data_points_analyzed": len(recent_events),
            "analysis_timestamp": "2023-10-01T14:30:00Z",
        },
        tags={
            "domain": "weather",
            "event_type": "analysis_result",
            "based_on_query": "recent_weather_summary",
        },
    )

    print("Generated a summary based on query results")

    # Generate an HTML visualization of the buffer
    plomp.write_html(buffer, "query_example.html")
    print("Created query_example.html with visualized queries")


if __name__ == "__main__":
    record_sample_data()
    run_query_examples()
