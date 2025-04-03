import datetime as dt
from copy import deepcopy
from typing import Callable, Iterator, Literal, Union
from plomp._query import PlompBufferQuery
from typeguard import typechecked
from plomp._types import TagsType, TagsFilter
from plomp._buffer_items import (
    PlompBufferItem,
    PlompCallHandle,
    PlompBufferItemType,
    PlompEvent,
    PlompCallTrace,
)


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

    @typechecked
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

    @typechecked
    def record_prompt_completion(self, call_index: int, response: str):
        if self._buffer_items[call_index].type_ != PlompBufferItemType.PROMPT:
            raise ValueError("Item at index is not a prompt request")

        self._buffer_items[call_index].call_trace.complete(
            self.timestamp_fn(), response
        )

    @typechecked
    def record_event(self, *, payload: dict, tags: TagsType):
        event_time = self.timestamp_fn()
        self._buffer_items.append(
            PlompBufferItem(
                event_time, tags, PlompBufferItemType.EVENT, PlompEvent(payload=payload)
            )
        )

    @typechecked
    def record_query(self, *, plomp_query: PlompBufferQuery, tags: TagsType):
        record_time = self.timestamp_fn()
        self._buffer_items.append(
            PlompBufferItem(record_time, tags, PlompBufferItemType.QUERY, plomp_query)
        )

    def __iter__(self) -> Iterator[PlompBufferItem]:
        for buffer_item in self._buffer_items:
            yield deepcopy(buffer_item)

    @typechecked
    def where(
        self,
        *,
        truth_fn: Callable[[PlompBufferItem], bool],
    ) -> PlompBufferQuery:
        return PlompBufferQuery(self).where(truth_fn=truth_fn)

    @typechecked
    def filter(
        self,
        *,
        how: Literal["any"] | Literal["all"] | Literal["none"] = "any",
        tags_filter: TagsFilter,
    ) -> PlompBufferQuery:
        return PlompBufferQuery(self).filter(how=how, tags_filter=tags_filter)

    @typechecked
    def first(self, size: int = 1) -> "PlompBufferQuery":
        return PlompBufferQuery(self).first(size)

    @typechecked
    def last(self, size: int = 1) -> "PlompBufferQuery":
        return PlompBufferQuery(self).last(size)

    @typechecked
    def window(self, start: int, end: int) -> "PlompBufferQuery":
        return PlompBufferQuery(self).window(start, end)

    @typechecked
    def union(
        self, plomp_buffer_query: Union["PlompBuffer", PlompBufferQuery]
    ) -> PlompBufferQuery:
        if isinstance(plomp_buffer_query, PlompBuffer):
            plomp_buffer_query = PlompBufferQuery(plomp_buffer_query)

        return PlompBufferQuery(self).union(plomp_buffer_query)

    @typechecked
    def intersection(
        self, plomp_buffer_query: Union["PlompBuffer", PlompBufferQuery]
    ) -> PlompBufferQuery:
        if isinstance(plomp_buffer_query, PlompBuffer):
            plomp_buffer_query = PlompBufferQuery(plomp_buffer_query)

        return PlompBufferQuery(self).intersection(plomp_buffer_query)

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
