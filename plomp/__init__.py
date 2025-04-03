import contextlib
import io
import textwrap
from functools import cache, partial, wraps
from typing import Callable

from typeguard import typechecked

from plomp.core import (
    PlompBuffer,
    PlompBufferItemType,
    PlompBufferQuery,
    PlompCallCompletion,
    PlompCallHandle,
    PlompCallTrace,
    TagsType,
)
from plomp.serve import write_html


class PlompMisconfiguration(Exception):
    pass


@cache
def _shared_plomp_buffer(key: str | None) -> PlompBuffer:
    return PlompBuffer(key=key)


def buffer(*, key: str | None = None) -> PlompBuffer:
    return _shared_plomp_buffer(key)


def record_prompt(
    prompt: str,
    tags: TagsType | None = None,
    *,
    buffer: PlompBuffer | None = None,
) -> PlompCallHandle:
    if buffer is None:
        buffer = _shared_plomp_buffer(None)

    return buffer.record_prompt_start(prompt=prompt, tags=tags or dict())


def record_event(
    payload: dict,
    tags: TagsType | None = None,
    *,
    buffer: PlompBuffer | None = None,
) -> PlompCallHandle:
    if buffer is None:
        buffer = _shared_plomp_buffer(None)

    return buffer.record_event(payload=payload, tags=tags or dict())


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
    def inner(*args, **kwargs):
        prompt = capture_prompt(fn, *args, **kwargs)
        tags = capture_tags(fn, *args, **kwargs)
        handle = record_prompt(prompt, tags=tags, buffer=buffer)
        result = fn(*args, **kwargs)
        handle.complete(result)
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

    def capture_tags(fn, *args, **kwargs) -> TagsType:
        tags: TagsType = {}
        for arg_i, arg_tag_name in capture_tag_args.items():
            tags[arg_tag_name] = _capture_from_arg_i(arg_i, fn, *args, **kwargs)

        for kwarg in capture_tag_kwargs:
            kwarg_tag = kwargs.get(kwarg, _MISSING)
            if kwarg_tag is not _MISSING:
                tags[kwarg] = kwarg_tag

        return tags

    return partial(
        _trace_decorator,
        capture_prompt=capture_prompt,
        capture_tags=capture_tags,
        buffer=buffer,
    )


__all__ = [
    "buffer",
    "PlompBuffer",
    "PlompCallCompletion",
    "PlompCallHandle",
    "PlompCallTrace",
    "record_event",
    "record_prompt",
    "render",
    "serve_buffer",
    "wrap_prompt_fn",
    "write_html",
]

__version__ = "0.1.0"
