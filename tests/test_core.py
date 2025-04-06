import datetime as dt

import pytest

import plomp
from typing import Any


def mock_buffer(key: str):
    """Create a buffer with mocked timestamp function."""
    buffer = plomp.buffer(key=key)

    # Mock timestamp to return a fixed date
    def mock_timestamp_fn() -> dt.datetime:
        return dt.datetime(2023, 10, 1)

    buffer.timestamp_fn = mock_timestamp_fn
    return buffer


def test_manual_traces():
    buffer = mock_buffer("test_manual_traces")
    prompt_response_and_tags = [
        ("What is 1 + 1", "2", {"math": True}),
        ("What is 2 + 1", "3", {"math": True}),
        ("What is 3 + 1", "4", {"math": True, "hard": True}),
    ]
    for prompt, response, tags in prompt_response_and_tags:
        plomp.record_prompt(prompt, tags=tags, buffer=buffer).complete(response)

    assert len(buffer) == 3


def test_wrapped_traces_basic():
    buffer = mock_buffer("test_wrapped_traces_basic")

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
            completion=plomp.PlompCallCompletion(
                completion_timestamp=dt.datetime(2023, 10, 1),
                response="2",
            ),
        ),
        plomp.PlompCallTrace(
            prompt="What is 1 + 3",
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
    buffer = mock_buffer("test_wrapped_traces")

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
        assert buffer_item.tags == {
            "speaker": speaker,
            "system_prompt": system_prompt,
        }
        assert buffer_item.call_trace.completion.response == response


def test_window_functions():
    buffer = mock_buffer("test_window_functions")

    @plomp.wrap_prompt_fn(buffer=buffer)
    def prompt_fn(prompt: str, *, mock_return_value: str, **kwargs) -> str:
        return mock_return_value

    prompt_fn("What is 1 + 1", mock_return_value="2")
    prompt_fn("What is 1 + 3", mock_return_value="4")
    prompt_fn("What is 2 + 3", mock_return_value="5")
    prompt_fn("What is 7 + 3", mock_return_value="10")

    assert len(buffer) == 4
    assert len(buffer.first(2)) == 2
    assert buffer.first(2)[0].call_trace == plomp.PlompCallTrace(
        prompt="What is 1 + 1",
        completion=plomp.PlompCallCompletion(
            completion_timestamp=dt.datetime(2023, 10, 1),
            response="2",
        ),
    )
    assert buffer.first(2).last(1)[0].call_trace == plomp.PlompCallTrace(
        prompt="What is 1 + 3",
        completion=plomp.PlompCallCompletion(
            completion_timestamp=dt.datetime(2023, 10, 1),
            response="4",
        ),
    )

    assert len(buffer.last(2)) == 2
    assert len(buffer.window(1, 3)) == 2
    window_buffer = buffer.window(1, 3)
    assert window_buffer[0].call_trace == plomp.PlompCallTrace(
        prompt="What is 1 + 3",
        completion=plomp.PlompCallCompletion(
            completion_timestamp=dt.datetime(2023, 10, 1),
            response="4",
        ),
    )
    assert window_buffer[-1].call_trace == plomp.PlompCallTrace(
        prompt="What is 2 + 3",
        completion=plomp.PlompCallCompletion(
            completion_timestamp=dt.datetime(2023, 10, 1),
            response="5",
        ),
    )


def test_filters():
    buffer = mock_buffer("test_filters")

    @plomp.wrap_prompt_fn(
        buffer=buffer, capture_tag_kwargs={"speaker", "system_prompt"}
    )
    def prompt_fn(prompt: str, *, mock_return_value: str, **kwargs) -> str:
        return mock_return_value

    prompt_fn("What is 1 + 1", mock_return_value="2", speaker="bob")
    prompt_fn(
        "What is 1 + 3",
        mock_return_value="4",
        speaker="alice",
        system_prompt="you are a calculator",
    )
    prompt_fn("What is 2 + 3", mock_return_value="5", speaker="bob")
    prompt_fn("What is 7 + 3", mock_return_value="10")

    assert len(buffer) == 4

    bob_speaker = buffer.filter(tags_filter={"speaker": "bob"})
    assert len(bob_speaker) == 2
    assert bob_speaker[0].call_trace == plomp.PlompCallTrace(
        prompt="What is 1 + 1",
        completion=plomp.PlompCallCompletion(
            completion_timestamp=dt.datetime(2023, 10, 1),
            response="2",
        ),
    )

    alice_speaker = buffer.filter(tags_filter={"speaker": ["alice"]})
    assert len(alice_speaker) == 1
    assert alice_speaker[0].call_trace == plomp.PlompCallTrace(
        prompt="What is 1 + 3",
        completion=plomp.PlompCallCompletion(
            completion_timestamp=dt.datetime(2023, 10, 1),
            response="4",
        ),
    )

    assert (
        len(
            buffer.filter(
                tags_filter={
                    "speaker": ["bob"],
                    "system_prompt": "you are a calculator",
                },
                how="all",
            )
        )
        == 0
    )

    no_speaker = buffer.filter(tags_filter={"speaker": ["bob", "alice"]}, how="none")
    assert len(no_speaker) == 1
    assert no_speaker[0].call_trace == plomp.PlompCallTrace(
        prompt="What is 7 + 3",
        completion=plomp.PlompCallCompletion(
            completion_timestamp=dt.datetime(2023, 10, 1),
            response="10",
        ),
    )

    no_speaker.record(tags={})

    assert buffer[-1].type_ == plomp.PlompBufferItemType.QUERY
    assert buffer[-1].query.matched_indices == [3]
    assert buffer[3] == no_speaker[0]


def test_union():
    buffer = mock_buffer("test_union")

    @plomp.wrap_prompt_fn(buffer=buffer, capture_tag_kwargs={"speaker"})
    def prompt_fn(prompt: str, *, mock_return_value: str, **kwargs) -> str:
        return mock_return_value

    prompt_fn("What is 1 + 1", mock_return_value="2", speaker="bob")
    prompt_fn("What is 1 + 3", mock_return_value="4", speaker="alice")
    prompt_fn("What is 2 + 3", mock_return_value="5", speaker="bob")
    prompt_fn("What is 7 + 3", mock_return_value="10")

    assert len(buffer) == 4

    bob_speaker = buffer.filter(tags_filter={"speaker": "bob"})
    alice_speaker = buffer.filter(tags_filter={"speaker": "alice"})
    alice_and_bob = bob_speaker.union(alice_speaker)
    assert len(alice_and_bob) == 3


def test_intersection():
    buffer = mock_buffer("test_intersection")

    @plomp.wrap_prompt_fn(buffer=buffer, capture_tag_kwargs={"speaker", "friend"})
    def prompt_fn(prompt: str, *, mock_return_value: str, **kwargs) -> str:
        return mock_return_value

    prompt_fn("What is 1 + 1", mock_return_value="2", speaker="bob")
    prompt_fn("What is 1 + 3", mock_return_value="4", speaker="bob", friend="alice")
    prompt_fn("What is 2 + 3", mock_return_value="5", speaker="bob")
    prompt_fn("What is 7 + 3", mock_return_value="10")

    assert len(buffer) == 4

    bob_speaker = buffer.filter(tags_filter={"speaker": "bob"})
    alice_friend = buffer.filter(tags_filter={"friend": "alice"})
    assert len(bob_speaker.intersection(alice_friend)) == 1


def test_explicit_tags():
    buffer = mock_buffer("test_explicit_tags")

    @plomp.wrap_prompt_fn(buffer=buffer, capture_tag_kwargs={"speaker", "friend"})
    def prompt_fn(prompt: str, *, mock_return_value: str, **kwargs) -> str:
        return mock_return_value

    prompt_fn("What is 1 + 1", mock_return_value="2", speaker="bob")
    prompt_fn("What is 1 + 3", mock_return_value="4", speaker="bob", friend="alice")
    prompt_fn(
        "What is 2 + 3",
        mock_return_value="5",
        speaker="bob",
        plomp_extra_tags={"answer": 42},
    )
    prompt_fn("What is 7 + 3", mock_return_value="10", plomp_extra_tags={"answer": 42})

    answers = buffer.filter(tags_filter={"friend": "alice", "answer": 42}, how="any")
    assert len(answers) == 3


def test_return_dict():
    buffer = mock_buffer("test_return_dict")

    @plomp.wrap_prompt_fn(buffer=buffer)
    def prompt_fn(prompt: str, **kwargs) -> dict[str, Any]:
        return {}

    prompt_fn("return some json")


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

    @plomp.wrap_prompt_fn(prompt_arg=1)
    def prompt_fn3(*, kwarg_only: str) -> str:
        raise NotImplementedError()

    with pytest.raises(plomp.PlompMisconfiguration):
        prompt_fn3("who are you?")

    with pytest.raises(plomp.PlompMisconfiguration):

        @plomp.wrap_prompt_fn(prompt_kwarg="plomp_extra_tags")
        def prompt_fn4(*, prompt_kwarg: str) -> str:
            raise NotImplementedError()

    with pytest.raises(plomp.PlompMisconfiguration):

        @plomp.wrap_prompt_fn(capture_tag_kwargs={"plomp_extra_tags"})
        def prompt_fn5() -> str:
            raise NotImplementedError()
