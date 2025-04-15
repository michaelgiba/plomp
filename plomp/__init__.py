import io
import textwrap
from functools import cache, partial, wraps
from typing import Callable

from typeguard import typechecked

from plomp._core import (
    PlompBuffer,
)
from plomp._buffer_items import (
    PlompCallCompletion,
    PlompCallHandle,
    PlompCallTrace,
    PlompBufferItemType,
)
from plomp._query import PlompBufferQuery
from plomp._types import TagsType
from plomp._progress import write_html, write_json, read_json


class PlompMisconfiguration(Exception):
    pass


@cache
def _shared_plomp_buffer(key: str | None) -> PlompBuffer:
    return PlompBuffer(key=key)


@typechecked
def buffer(*, key: str | None = None) -> PlompBuffer:
    return _shared_plomp_buffer(key)


@typechecked
def record_prompt(
    prompt: str,
    tags: TagsType | None = None,
    *,
    buffer: PlompBuffer | None = None,
) -> PlompCallHandle:
    if buffer is None:
        buffer = _shared_plomp_buffer(None)

    return buffer.record_prompt_start(prompt=prompt, tags=tags or dict())


@typechecked
def record_event(
    payload: dict,
    tags: TagsType | None = None,
    *,
    buffer: PlompBuffer | None = None,
) -> None:
    if buffer is None:
        buffer = _shared_plomp_buffer(None)

    return buffer.record_event(payload=payload, tags=tags or dict())


@typechecked
def render(buffer: PlompBuffer | PlompBufferQuery, write_to: io.IOBase):
    for item in buffer:
        item.render(write_to, indent=0)
        write_to.write("\n")


def _trace_decorator(
    fn,
    *,
    capture_prompt: Callable[[Callable, tuple, dict], str],
    capture_tags: Callable[[Callable, tuple, dict], TagsType],
    buffer: PlompBuffer | None = None,
):
    @wraps(fn)
    def inner(*args, plomp_extra_tags: TagsType | None = None, **kwargs):
        plomp_extra_tags = plomp_extra_tags or {}
        assert isinstance(plomp_extra_tags, dict), (
            "Invalid argument passed for `plomp_extra_tags`"
        )

        prompt = capture_prompt(fn, *args, **kwargs)
        tags = capture_tags(
            fn,
            *args,
            plomp_extra_tags=plomp_extra_tags or {},
            **kwargs,  # type: ignore
        )
        handle = record_prompt(prompt, tags=tags, buffer=buffer)
        result = fn(*args, **kwargs)
        handle.complete(str(result))
        return result

    return inner


def _validate_wrap_kwargs(
    prompt_arg: int | None = None,
    prompt_kwarg: str | None = None,
    capture_tag_args: dict[int, str] | None = None,
    capture_tag_kwargs: set[str] | None = None,
):
    if prompt_arg is not None and prompt_kwarg is not None:
        raise PlompMisconfiguration(
            "You cannot pass both `prompt_arg` and `prompt_kwarg` at the same time"
        )

    if (
        capture_tag_args is not None
        and prompt_arg is not None
        and prompt_arg in capture_tag_args
    ):
        raise PlompMisconfiguration(
            textwrap.dedent(
                f"""
            Argument at position {prompt_arg} cannot be used as both prompt source and tag source
        """
            )
        )

    if (
        capture_tag_kwargs is not None
        and prompt_kwarg is not None
        and prompt_kwarg in capture_tag_kwargs
    ):
        raise PlompMisconfiguration(
            textwrap.dedent(
                f"""
            Keyword argument '{prompt_kwarg}' cannot be used as both prompt source and tag source
        """
            )
        )

    if any(
        [
            (
                capture_tag_kwargs is not None
                and "plomp_extra_tags" in capture_tag_kwargs
            ),
            (prompt_kwarg is not None and "plomp_extra_tags" in prompt_kwarg),
        ]
    ):
        raise PlompMisconfiguration(
            textwrap.dedent(
                """
            Keyword argument 'plomp_extra_tags' is a special argument and cannot be supplied as a
            capture kwarg"""
            )
        )


_MISSING = object()


@typechecked
def wrap_prompt_fn(
    *,
    prompt_arg: int | None = None,
    prompt_kwarg: str | None = None,
    capture_tag_args: dict[int, str] | None = None,
    capture_tag_kwargs: set[str] | None = None,
    buffer: PlompBuffer | None = None,
):
    _validate_wrap_kwargs(
        prompt_arg=prompt_arg,
        prompt_kwarg=prompt_kwarg,
        capture_tag_args=capture_tag_args,
        capture_tag_kwargs=capture_tag_kwargs,
    )

    def _capture_from_arg_i(i, /, fn, *args, **kwargs) -> str:
        try:
            return args[i]
        except IndexError as e:
            raise PlompMisconfiguration(f"Could not capture prompt for arg{i}") from e

    def _capture_prompt_from_kwarg(kwarg, /, fn, *args, **kwargs) -> str | object:
        return kwargs.get(kwarg, _MISSING)

    def _capture_prompts_with_options(capture_fns, /, fn, *args, **kwargs) -> str:
        for capture_fn in capture_fns:
            result = capture_fn(fn, *args, **kwargs)
            if result is not _MISSING:
                return result

        raise PlompMisconfiguration("Could not capture prompt given parameters.")

    if prompt_arg is None and prompt_kwarg is None:
        capture_prompt = partial(
            _capture_prompts_with_options,
            [
                partial(_capture_from_arg_i, 0),
                partial(_capture_prompt_from_kwarg, prompt_kwarg),
            ],
        )

    elif prompt_arg is not None:
        capture_prompt = partial(
            _capture_prompts_with_options,
            [partial(_capture_from_arg_i, prompt_arg)],
        )

    elif prompt_kwarg is not None:
        capture_prompt = partial(
            _capture_prompts_with_options,
            [partial(_capture_prompt_from_kwarg, prompt_kwarg)],
        )

    capture_tag_args = capture_tag_args or dict()
    capture_tag_kwargs = capture_tag_kwargs or set()

    if set(capture_tag_args) & set(capture_tag_kwargs):
        raise PlompMisconfiguration(
            "You cannot use the same argument as both a positional and keyword tag source"
        )

    def capture_tags(fn, *args, plomp_extra_tags: TagsType, **kwargs) -> TagsType:
        tags: TagsType = {}
        for arg_i, arg_tag_name in capture_tag_args.items():
            tags[arg_tag_name] = _capture_from_arg_i(arg_i, fn, *args, **kwargs)

        for kwarg in capture_tag_kwargs:
            kwarg_tag = kwargs.get(kwarg, _MISSING)
            if kwarg_tag is not _MISSING:
                tags[kwarg] = kwarg_tag

        for explicit_tag_key, explicit_tag_value in plomp_extra_tags.items():
            tags[explicit_tag_key] = explicit_tag_value

        return tags

    return partial(
        _trace_decorator,
        capture_prompt=capture_prompt,
        capture_tags=capture_tags,  # type: ignore
        buffer=buffer,
    )


__all__ = [
    "buffer",
    "PlompBuffer",
    "PlompCallCompletion",
    "PlompCallHandle",
    "PlompBufferItemType",
    "PlompCallTrace",
    "record_event",
    "record_prompt",
    "render",
    "read_json",
    "serve_buffer",
    "wrap_prompt_fn",
    "write_html",
    "write_json",
]

__version__ = "0.1.4"
