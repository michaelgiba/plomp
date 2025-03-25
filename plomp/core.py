import datetime as dt
import io
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Iterator, List, Literal, Union

TagType = str | dict
TagsType = dict[str, TagType]
TagsFilter = dict[str, list[TagType] | TagType]


@dataclass(slots=True, frozen=True, kw_only=True)
class PlompCallCompletion:
    completion_timestamp: dt.datetime
    response: str

    def to_dict(self) -> dict:
        return {
            "completion_timestamp": self.completion_timestamp.isoformat(),
            "response": self.response,
        }


@dataclass(slots=True, kw_only=True)
class PlompCallTrace:

    prompt: str
    completion: PlompCallCompletion | None = None

    def __init__(
        self,
        prompt: str,
        *,
        completion: PlompCallCompletion | None = None,
    ):
        self.prompt = prompt
        self.completion = completion

    def complete(self, completion_timestamp: dt.datetime, response: str):
        if self.completion is not None:
            raise ValueError("Call has already been completed")

        self.completion = PlompCallCompletion(
            completion_timestamp=completion_timestamp,
            response=response,
        )

    def render(self, io: io.IOBase, *, indent: int = 0):
        io.write(indent * " " + repr(self))

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt,
            "completion": self.completion.to_dict() if self.completion else None,
        }


class PlompCallHandle:

    def __init__(self, buffer: "PlompBuffer", index: int):
        self.buffer = buffer
        self.index = index

    def complete(self, response: str):
        self.buffer.record_prompt_completion(self.index, response)


@dataclass(slots=True, kw_only=True)
class PlompEvent:
    payload: dict

    def render(self, io: io.IOBase, *, indent: int = 0):
        io.write(indent * " " + repr(self))

    def to_dict(self) -> dict:
        return {"payload": self.payload}


class PlompBufferItemType(Enum):
    PROMPT = "prompt"
    EVENT = "event"


@dataclass
class PlompBufferItem:
    timestamp: dt.datetime
    tags: TagsType
    type_: PlompBufferItemType
    _data: PlompCallTrace | PlompEvent

    @property
    def call_trace(self) -> PlompCallTrace:
        if self.type_ != PlompBufferItemType.PROMPT:
            raise ValueError("Item is not a prompt request")
        assert isinstance(self._data, PlompCallTrace)
        return self._data

    @property
    def event(self) -> PlompEvent:
        if self.type_ != PlompBufferItemType.EVENT:
            raise ValueError("Item is not an event")
        assert isinstance(self._data, PlompEvent)
        return self._data

    def render(self, io: io.IOBase, *, indent: int = 0):
        io.write(indent * " " + self.__class__.__name__ + "(\n")
        io.write((indent + 1) * " " + f"timestamp={repr(self.timestamp)},\n")
        io.write((indent + 1) * " " + f"tags={repr(self.tags)},\n")
        io.write((indent + 1) * " " + f"type_={repr(self.type_)},\n")
        io.write((indent + 1) * " " + "_data=(\n")
        self._data.render(io, indent=indent + 2)
        io.write("\n")
        io.write((indent + 1) * " " + ")\n")
        io.write(indent * " " + ")")

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "type": self.type_.value,
            "data": self._data.to_dict(),
        }


class PlompBuffer:

    def __init__(
        self,
        *,
        buffer_items: list[PlompBufferItem] | None = None,
        timestamp_fn: Callable[[], dt.datetime] = dt.datetime.now,
        key: str | None = None,
    ):
        self.timestamp_fn = timestamp_fn
        self.key = key
        self._buffer_items = [
            deepcopy(buffer_item) for buffer_item in (buffer_items or [])
        ]

    def record_prompt_start(self, *, prompt: str, tags: TagsType) -> PlompCallHandle:
        insert_index = len(self._buffer_items)
        self._buffer_items.append(
            PlompBufferItem(
                self.timestamp_fn(),
                tags,
                PlompBufferItemType.PROMPT,
                PlompCallTrace(prompt),
            )
        )
        return PlompCallHandle(self, insert_index)

    def record_prompt_completion(self, call_index: int, response: str):
        if self._buffer_items[call_index].type_ != PlompBufferItemType.PROMPT:
            raise ValueError("Item at index is not a prompt request")

        self._buffer_items[call_index].call_trace.complete(
            self.timestamp_fn(), response
        )

    def record_event(self, *, payload: dict, tags: TagsType):
        event_time = self.timestamp_fn()
        self._buffer_items.append(
            PlompBufferItem(
                event_time, tags, PlompBufferItemType.EVENT, PlompEvent(payload=payload)
            )
        )

    def __iter__(self) -> Iterator[PlompBufferItem]:
        for buffer_item in self._buffer_items:
            yield deepcopy(buffer_item)

    def where(
        self,
        *,
        truth_fn: Callable[[PlompBufferItem], bool],
    ) -> "PlompBuffer":
        """Filter buffer items based on a truth function."""
        filtered_buffer = []
        for buffer_item in self._buffer_items:
            if truth_fn(buffer_item):
                filtered_buffer.append(buffer_item)
        return PlompBuffer(buffer_items=filtered_buffer, key=self.key)

    def filter(
        self,
        *,
        how: Literal["any"] | Literal["all"] | Literal["none"] = "any",
        tags_filter: TagsFilter,
    ) -> "PlompBuffer":

        def _normalize_tag_filter(tags_filter: TagsFilter) -> TagsFilter:
            return {
                tag_key: tag_value if isinstance(tag_value, list) else [tag_value]
                for tag_key, tag_value in tags_filter.items()
            }

        def _tags_match_filter(
            filter_tag_key: str,
            filter_tag_values: list[TagType] | TagType,
            tags: TagsType,
        ) -> bool:
            if filter_tag_key not in tags:
                return False

            tag_value = tags[filter_tag_key]
            for filter_value in filter_tag_values:
                if isinstance(tag_value, dict) and isinstance(filter_value, dict):
                    # Compare dictionaries by their contents
                    if tag_value == filter_value:
                        return True
                elif tag_value == filter_value:
                    return True
            return False

        tags_filter = _normalize_tag_filter(tags_filter)

        if how == "any":
            return self.where(
                truth_fn=lambda buffer_item: any(
                    _tags_match_filter(
                        filter_tag_key, filter_tag_values, buffer_item.tags
                    )
                    for filter_tag_key, filter_tag_values in tags_filter.items()
                )
            )
        elif how == "all":
            return self.where(
                truth_fn=lambda buffer_item: all(
                    _tags_match_filter(
                        filter_tag_key, filter_tag_values, buffer_item.tags
                    )
                    for filter_tag_key, filter_tag_values in tags_filter.items()
                )
            )
        elif how == "none":
            return self.where(
                truth_fn=lambda buffer_item: not any(
                    _tags_match_filter(
                        filter_tag_key, filter_tag_values, buffer_item.tags
                    )
                    for filter_tag_key, filter_tag_values in tags_filter.items()
                )
            )
        else:
            raise ValueError(f"Invalid filter method: {how}")

    def _filter_all(self, tags: Union[List[str], dict]) -> "PlompBuffer":
        if isinstance(tags, list):
            return self.where(
                truth_fn=lambda buffer_item: all(
                    tag in buffer_item.tags for tag in tags
                )
            )
        elif isinstance(tags, dict):
            return self.where(
                truth_fn=lambda buffer_item: all(
                    key in buffer_item.tags and buffer_item.tags[key] == value
                    for key, value in tags.items()
                )
            )
        else:
            raise TypeError(f"Expected list or dict, got {type(tags).__name__}")

    def first(self, size: int = 1) -> "PlompBuffer":
        return PlompBuffer(buffer_items=self._buffer_items[:size], key=self.key)

    def last(self, size: int = 1) -> "PlompBuffer":
        return PlompBuffer(buffer_items=self._buffer_items[-size:], key=self.key)

    def window(self, start: int, end: int) -> "PlompBuffer":
        return PlompBuffer(buffer_items=self._buffer_items[start:end], key=self.key)

    def __getitem__(self, index: int) -> PlompBufferItem:
        return self._buffer_items[index]

    def __len__(self) -> int:
        return len(self._buffer_items)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "buffer_items": [
                buffer_item.to_dict() for buffer_item in self._buffer_items
            ],
        }
