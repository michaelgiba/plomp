import plomp
import random


def simulate_llm_response(prompt: str) -> str:
    return f"This is a simulated response to: '{prompt[:30]}...'"


@plomp.wrap_prompt_fn()
def ask_llm(prompt: str, *, tags=None) -> str:
    return simulate_llm_response(prompt)


def record_sample_data():
    london_response = ask_llm(
        "Tell me about the weather in London",
        plomp_extra_tags={"domain": "weather", "location": "London"},
    )
    london_temp = 18 + random.uniform(-2, 2)

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

    ny_temp = 22 + random.uniform(-3, 3)

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

    for i in range(3):
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
    buffer = plomp.buffer()

    weather_items = buffer.filter(tags_filter={"domain": "weather"})
    print(f"Found {len(weather_items)} weather-related items")

    weather_items.record(tags={"query_purpose": "weather_data_collection"})

    london_weather = buffer.filter(
        how="all",  # Require all conditions to match
        tags_filter={"domain": "weather", "location": "London"},
    )
    print(f"Found {len(london_weather)} London weather items")

    llm_derived_data = buffer.where(
        truth_fn=lambda item: (
            item.type_.value == "event"
            and "data_source" in item.tags
            and item.tags["data_source"] == "llm_derived"
        )
    )
    print(f"Found {len(llm_derived_data)} events derived from LLM responses")
    llm_derived_data.record(tags={"query_purpose": "llm_data_analysis"})

    combined_query = london_weather.union(llm_derived_data)
    print(f"Union query has {len(combined_query)} items")

    recent_events = buffer.filter(tags_filter={"domain": "weather"}).last(3)
    print(f"Found {len(recent_events)} recent weather events")
    recent_events.record(tags={"query_purpose": "recent_weather_summary"})

    summary_prompt = "Summarize the following weather data:\n"
    for idx, item in enumerate(recent_events):
        if item.type_.value == "event":
            data = item.event.payload
            summary_prompt += (
                f"{idx + 1}. {data.get('plomp_display_text', 'Unknown')}\n"
            )

    response = ask_llm(summary_prompt, plomp_extra_tags={"purpose": "weather_summary"})

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

    plomp.write_html(buffer, "query_example.html")
    print("Created query_example.html with visualized queries")


if __name__ == "__main__":
    record_sample_data()
    run_query_examples()
