import datetime as dt
import io
from copy import deepcopy
from dataclasses import dataclass
from functools import wraps
from typing import Callable, Iterator

TagType = str | dict
TagsType = dict[str, TagType]


@dataclass(slots=True, frozen=True, kw_only=True)
class PlompCallCompletion:
    completion_timestamp: dt.datetime
    response: str


@dataclass(slots=True, kw_only=True)
class PlompCallTrace:

    prompt: str
    tags: TagsType
    completion: PlompCallCompletion | None = None

    def __init__(
        self,
        prompt: str,
        tags: TagsType,
        *,
        completion: PlompCallCompletion | None = None,
    ):
        self.prompt = prompt
        self.tags = deepcopy(tags)
        self.completion = completion

    def complete(self, completion_timestamp: dt.datetime, response: str):
        if self.completion is not None:
            raise ValueError("Call has already been completed")

        self.completion = PlompCallCompletion(
            completion_timestamp=completion_timestamp,
            response=response,
        )

    def __repr__(self):
        cn = self.__class__.__name__
        parts = [
            f"prompt='{self.prompt!r}'",
            f"tags={self.tags!r}",
            f"completion={self.completion!r}",
        ]

        parts_string = ", ".join(parts)
        return f"{cn}({parts_string})"

    def render(self, io: io.IOBase, *, indent: int = 0):
        io.write(indent * " " + repr(self))


class PlompCallHandle:

    def __init__(self, buffer: "PlompBuffer", index: int):
        self.buffer = buffer
        self.index = index

    def complete(self, response: str):
        self.buffer.record_completion(self.index, response)


class PlompBufferItem:

    def __init__(
        self, timestamp: dt.datetime, seq_number: int, call_trace: PlompCallTrace
    ):
        self.timestamp = timestamp
        self.seq_number = seq_number
        self.call_trace = call_trace

    def __repr__(self):
        parts = [
            f"timestamp={self.timestamp!r}",
            f"seq_number={self.seq_number!r}",
            f"call_trace={self.call_trace!r}",
        ]
        args = ", ".join(parts)
        return f"{self.__class__.__name__}({args})"

    def render(self, io: io.IOBase, *, indent: int = 0):
        io.write(indent * " " + repr(self))


class PlompBuffer:

    def __init__(
        self,
        *,
        calls: list[tuple[dt.datetime, PlompCallTrace]] | None = None,
        timestamp_fn: Callable[[], dt.datetime] = dt.datetime.now,
        key: str | None = None,
    ):
        self.timestamp_fn = timestamp_fn
        self.key = key
        self._calls = [deepcopy(call) for call in (calls or [])]

    def record_invocation(self, *, prompt: str, tags: TagsType) -> PlompCallHandle:
        call_time = self.timestamp_fn()
        invoked_call = PlompCallTrace(prompt, tags)
        insert_index = len(self._calls)
        self._calls.append((call_time, invoked_call))
        return PlompCallHandle(self, insert_index)

    def record_completion(self, invoked_call_index: int, response: str):
        self._calls[invoked_call_index][1].complete(self.timestamp_fn(), response)

    def __iter__(self) -> Iterator[PlompBufferItem]:
        for index, (call_time, call_trace) in enumerate(self._calls):
            yield PlompBufferItem(call_time, index, deepcopy(call_trace))

    def filter(self, *, tags: list) -> "PlompBuffer":
        filtered_calls = []
        for call_time, call in self._calls:
            if any(tag in call.tags for tag in tags):
                filtered_calls.append((call_time, call))
        return PlompBuffer(calls=filtered_calls, key=self.key)

    def first(self, size: int = 1) -> "PlompBuffer":
        """Return the first 'size' items from the buffer."""
        return PlompBuffer(calls=self._calls[:size], key=self.key)

    def last(self, size: int = 1) -> "PlompBuffer":
        """Return the last 'size' items from the buffer."""
        return PlompBuffer(calls=self._calls[-size:], key=self.key)

    def window(self, start: int, end: int) -> "PlompBuffer":
        """Return items from index 'start' (inclusive) to 'end' (exclusive)."""
        return PlompBuffer(calls=self._calls[start:end], key=self.key)

    def __getitem__(self, index: int) -> PlompBufferItem:
        if index < 0:
            index += len(self._calls)
        return PlompBufferItem(
            self._calls[index][0], index, deepcopy(self._calls[index][1])
        )

    def __len__(self) -> int:
        return len(self._calls)
