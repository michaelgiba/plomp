import plomp


def simulate_llm_response(prompt: str) -> str:
    return f"This is a simulated response to: '{prompt[:30]}...'"


def example_manual_recording():
    print("Running manual recording example...")

    handle = plomp.record_prompt(
        "What is the capital of France?",
        tags={"purpose": "geography", "language": "en"},
    )

    response = simulate_llm_response("What is the capital of France?")

    handle.complete(response)

    plomp.record_event(
        payload={
            "plomp_display_event_type": "user_feedback",
            "plomp_display_text": "User rated the response 4/5",
            "rating": 4,
        },
        tags={"event_type": "feedback", "source": "user"},
    )

    plomp.write_html(plomp.buffer(), "manual_recording_example.html")
    print("Created manual_recording_example.html")


@plomp.wrap_prompt_fn(
    prompt_arg=0,  # Use the first argument as the prompt
    capture_tag_kwargs={"model", "temperature"},  # Capture these kwargs as tags
)
def ask_llm(prompt: str, *, model="gpt-3.5-turbo", temperature=0.7) -> str:
    """A function that calls an LLM and is wrapped with Plomp."""
    return simulate_llm_response(prompt)


def example_decorator_recording():
    print("Running decorator example...")

    response1 = ask_llm(
        "What are the top 3 tourist attractions in Paris?",
        model="gpt-4",
        temperature=0.8,
        plomp_extra_tags={"purpose": "travel"},  # Additional tags
    )

    response2 = ask_llm(
        "Suggest a 3-day itinerary for Paris.",
        plomp_extra_tags={"purpose": "itinerary"},
    )

    plomp.record_event(
        payload={
            "plomp_display_event_type": "search_performed",
            "plomp_display_text": "User searched for 'Paris hotels'",
            "query": f"Paris hotels: {response1!r} {response2!r}",
        },
        tags={"event_type": "search", "topic": "travel"},
    )

    plomp.write_html(plomp.buffer(), "decorator_example.html")
    print("Created decorator_example.html")


if __name__ == "__main__":
    example_manual_recording()
    example_decorator_recording()
