import io
from dataclasses import dataclass
from typing import Callable, Iterable, Literal, TYPE_CHECKING
from typeguard import typechecked
from plomp._types import TagsType, TagsFilter, TagType
from plomp._buffer_items import (
    PlompBufferItem,
)


if TYPE_CHECKING:
    from plomp._core import PlompBuffer


@typechecked
@dataclass(slots=True, kw_only=True)
class PlompBufferQuery:
    buffer: "PlompBuffer"
    matched_indices: list[int]
    op_name: str

    def __init__(
        self,
        buffer: "PlompBuffer",
        *,
        matched_indices: Iterable[int] | None = None,
        op_name: str | None = None,
    ):
        self.buffer = buffer
        self.matched_indices: list[int] = sorted(
            list(range(len(buffer))) if matched_indices is None else matched_indices
        )
        self.op_name = op_name or "<buffer>"

    def __iter__(self):
        for matched_index in self.matched_indices:
            yield self.buffer[matched_index]

    @typechecked
    def _where(
        self,
        *,
        truth_fn: Callable[[PlompBufferItem], bool],
        condition_op_name: str,
    ) -> "PlompBufferQuery":
        """Filter buffer items based on a truth function."""
        matched_indices = []
        for i in self.matched_indices:
            if truth_fn(self.buffer[i]):
                matched_indices.append(i)

        return PlompBufferQuery(
            buffer=self.buffer,
            matched_indices=matched_indices,
            op_name=f"{condition_op_name}({self.op_name})",
        )

    @typechecked
    def record(self, *, tags: TagsType):
        self.buffer.record_query(plomp_query=self, tags=tags)

    @typechecked
    def where(
        self,
        *,
        truth_fn: Callable[[PlompBufferItem], bool],
    ) -> "PlompBufferQuery":
        return self._where(truth_fn=truth_fn, condition_op_name="where[]")

    @typechecked
    def filter(
        self,
        *,
        how: Literal["any"] | Literal["all"] | Literal["none"] = "any",
        tags_filter: TagsFilter,
    ) -> "PlompBufferQuery":
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

            if not isinstance(filter_tag_values, list):
                filter_tag_values = [filter_tag_values]

            tag_value = tags[filter_tag_key]
            for filter_value in filter_tag_values:
                if isinstance(tag_value, dict) and isinstance(filter_value, dict):
                    if tag_value == filter_value:
                        return True
                elif tag_value == filter_value:
                    return True
            return False

        tags_filter = _normalize_tag_filter(tags_filter)
        condition_op_name = f"filter[how={how!r}, tags={tags_filter!r}]"

        if how == "any":
            return self._where(
                truth_fn=lambda buffer_item: any(
                    _tags_match_filter(
                        filter_tag_key, filter_tag_values, buffer_item.tags
                    )
                    for filter_tag_key, filter_tag_values in tags_filter.items()
                ),
                condition_op_name=condition_op_name,
            )
        elif how == "all":
            return self._where(
                truth_fn=lambda buffer_item: all(
                    _tags_match_filter(
                        filter_tag_key, filter_tag_values, buffer_item.tags
                    )
                    for filter_tag_key, filter_tag_values in tags_filter.items()
                ),
                condition_op_name=condition_op_name,
            )
        elif how == "none":
            return self._where(
                truth_fn=lambda buffer_item: not any(
                    _tags_match_filter(
                        filter_tag_key, filter_tag_values, buffer_item.tags
                    )
                    for filter_tag_key, filter_tag_values in tags_filter.items()
                ),
                condition_op_name=condition_op_name,
            )
        else:
            raise ValueError(f"Invalid filter method: {how}")

    @typechecked
    def first(self, size: int = 1) -> "PlompBufferQuery":
        return PlompBufferQuery(
            buffer=self.buffer,
            matched_indices=self.matched_indices[:size],
            op_name=f"first[size={size}]({self.op_name})",
        )

    @typechecked
    def last(self, size: int = 1) -> "PlompBufferQuery":
        return PlompBufferQuery(
            buffer=self.buffer,
            matched_indices=self.matched_indices[-size:],
            op_name=f"last[size={size}]({self.op_name})",
        )

    @typechecked
    def window(self, start: int, end: int) -> "PlompBufferQuery":
        return PlompBufferQuery(
            buffer=self.buffer,
            matched_indices=self.matched_indices[start:end],
            op_name=f"window[start={start}, end={end}]({self.op_name})",
        )

    @typechecked
    def union(self, other: "PlompBufferQuery") -> "PlompBufferQuery":
        return PlompBufferQuery(
            buffer=self.buffer,
            matched_indices=sorted(
                set(self.matched_indices) | set(other.matched_indices)
            ),
            op_name=f"union[other={other.op_name}]({self.op_name})",
        )

    @typechecked
    def intersection(self, other: "PlompBufferQuery") -> "PlompBufferQuery":
        return PlompBufferQuery(
            buffer=self.buffer,
            matched_indices=sorted(
                set(self.matched_indices) & set(other.matched_indices)
            ),
            op_name=f"intersection[other={other.op_name}]({self.op_name})",
        )

    def to_dict(self) -> dict:
        return {
            "buffer_key": self.buffer.key,
            "op_name": self.op_name,
            "matched_indices": self.matched_indices,
        }

    def __len__(self):
        return len(self.matched_indices)

    def __getitem__(self, i: int) -> "PlompBufferItem":
        return self.buffer[self.matched_indices[i]]

    @typechecked
    def render(self, io: io.IOBase, *, indent: int = 0):
        io.write(indent * " " + repr(self))
