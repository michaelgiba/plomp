import datetime as dt
import io
import sys

import pytest

import plomp


def test_manual_traces():
    buffer = plomp.buffer(key="test_manual_traces")
    prompt_response_and_tags = [
        ("What is 1 + 1", "2", ["math"]),
        ("What is 2 + 1", "3", ["math"]),
        ("What is 3 + 1", "5", ["math", "hard"]),
    ]
    for prompt, response, tags in prompt_response_and_tags:
        plomp.record_prompt(prompt, tags=tags, buffer=buffer).complete(response)

    assert len(buffer) == 3


def test_wrapped_traces_basic():

    # TODO: Properly mock the datetimes
    def mock_timestamp_fn() -> dt.datetime:
        return dt.datetime(2023, 10, 1)

    buffer = plomp.buffer(key="test_wrapped_traces_basic")
    buffer.timestamp_fn = mock_timestamp_fn

    @plomp.wrap_prompt_fn(buffer=buffer)
    def prompt_fn(prompt: str, *, mock_return_value: str, **kwargs) -> str:
        return mock_return_value

    prompt_fn(
        "What is 1 + 1",
        mock_return_value="2",
        model="claude-sonnet-3.7",
        max_tokens=10053,
        my_favorite_kwarg="this_one",
    )
    prompt_fn("What is 1 + 3", mock_return_value="4")
    prompt_fn("What is 2 + 3", mock_return_value="5")

    start_buffer = buffer.first(2)

    calls = [
        plomp.PlompCallTrace(
            prompt="What is 1 + 1",
            tags={},
            completion=plomp.PlompCallCompletion(
                completion_timestamp=dt.datetime(2023, 10, 1),
                response="2",
            ),
        ),
        plomp.PlompCallTrace(
            prompt="What is 1 + 3",
            tags={},
            completion=plomp.PlompCallCompletion(
                completion_timestamp=dt.datetime(2023, 10, 1),
                response="4",
            ),
        ),
    ]

    assert len(start_buffer) == 2
    for buffer_item, call_trace in zip(start_buffer, calls):
        assert buffer_item.call_trace == call_trace


def test_wrapped_traces():

    # TODO: Properly mock the datetimes
    def mock_timestamp_fn() -> dt.datetime:
        return dt.datetime(2023, 10, 1)

    buffer = plomp.buffer(key="test_wrapped_traces")
    buffer.timestamp_fn = mock_timestamp_fn

    @plomp.wrap_prompt_fn(
        capture_tag_kwargs={"system_prompt"},
        capture_tag_args={2: "speaker"},
        buffer=buffer,
    )
    def prompt_fn(prompt: str, mock_return_value: str, speaker: str, **kwargs) -> str:
        return mock_return_value

    system_prompt = "you are a calculator"
    prompt_response_and_speaker = [
        ("What is 1 + 1", "2", "bob"),
        ("What is 1 + 3", "4", "alice"),
        ("What is 2 + 3", "5", "bob"),
        ("What is 7 + 3", "10", "alice"),
    ]

    for prompt, response, speaker in prompt_response_and_speaker:
        prompt_fn(prompt, response, speaker, system_prompt=system_prompt)

    assert len(buffer) == 4
    for item in zip(buffer, prompt_response_and_speaker):
        buffer_item, (prompt_text, response, speaker) = item
        assert buffer_item.call_trace.prompt == prompt_text
        assert buffer_item.call_trace.tags == {
            "speaker": speaker,
            "system_prompt": system_prompt,
        }
        assert buffer_item.call_trace.completion.response == response


def test_failures_of_wrapping():

    @plomp.wrap_prompt_fn()
    def prompt_fn1() -> str:
        raise NotImplementedError()

    with pytest.raises(plomp.PlompMisconfiguration):
        prompt_fn1()

    @plomp.wrap_prompt_fn(prompt_kwarg="prompt_unset")
    def prompt_fn2(prompt) -> str:
        raise NotImplementedError()

    with pytest.raises(plomp.PlompMisconfiguration):
        prompt_fn2("what is your name?")
