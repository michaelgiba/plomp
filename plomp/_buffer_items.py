import datetime as dt
import io
from dataclasses import dataclass
from enum import Enum
from typing import Union, TYPE_CHECKING
from typeguard import typechecked
from plomp._types import TagsType

if TYPE_CHECKING:
    from plomp._core import PlompBuffer
    from plomp._query import PlompBufferQuery


@typechecked
@dataclass(slots=True, frozen=True, kw_only=True)
class PlompCallCompletion:
    completion_timestamp: dt.datetime
    response: str

    def to_dict(self) -> dict:
        return {
            "completion_timestamp": self.completion_timestamp.isoformat(),
            "response": self.response,
        }


@typechecked
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

    @typechecked
    def complete(self, completion_timestamp: dt.datetime, response: str):
        if self.completion is not None:
            raise ValueError("Call has already been completed")

        self.completion = PlompCallCompletion(
            completion_timestamp=completion_timestamp,
            response=response,
        )

    @typechecked
    def render(self, io: io.IOBase, *, indent: int = 0):
        io.write(indent * " " + repr(self))

    def to_dict(self) -> dict:
        return {
            "prompt": self.prompt,
            "completion": self.completion.to_dict() if self.completion else None,
        }


@typechecked
class PlompCallHandle:
    def __init__(self, buffer: "PlompBuffer", index: int):
        self.buffer = buffer
        self.index = index

    @typechecked
    def complete(self, response: str):
        self.buffer.record_prompt_completion(self.index, response)


@typechecked
@dataclass(slots=True, kw_only=True)
class PlompEvent:
    payload: dict

    @typechecked
    def render(self, io: io.IOBase, *, indent: int = 0):
        io.write(indent * " " + repr(self))

    def to_dict(self) -> dict:
        return {"payload": self.payload}


class PlompBufferItemType(Enum):
    PROMPT = "prompt"
    EVENT = "event"
    QUERY = "query"


@dataclass
class PlompBufferItem:
    timestamp: dt.datetime
    tags: TagsType
    type_: PlompBufferItemType
    _data: Union[PlompCallTrace, PlompEvent, "PlompBufferQuery"]

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

    @property
    def query(self) -> "PlompBufferQuery":
        from plomp._query import PlompBufferQuery

        if self.type_ != PlompBufferItemType.QUERY:
            raise ValueError("Item is not a query")
        assert isinstance(self._data, PlompBufferQuery)
        return self._data

    @typechecked
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
