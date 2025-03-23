import contextlib
import io
import textwrap
from functools import cache, partial, wraps
from typing import Callable

from plomp.core import (PlompBuffer, PlompCallCompletion, PlompCallHandle,
                        PlompCallTrace, TagsType)


class PlompMisconfiguration(Exception):
    pass


@cache
def _shared_plomp_buffer(key: str | None) -> PlompBuffer:
    return PlompBuffer(key=key)


def buffer(*, key: str | None = None) -> PlompBuffer:
    return _shared_plomp_buffer(key)


def record_prompt(
    prompt: str,
    tags: list[str | dict] | None = None,
    *,
    buffer: str | None = None,
) -> PlompCallHandle:
    if buffer is None:
        buffer = _shared_plomp_buffer(None)

    return buffer.record_invocation(prompt=prompt, tags=tags)


def render(buffer: PlompBuffer, write_to: io.IOBase):
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
    prompt_kwarg: int | None = None,
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


def wrap_prompt_fn(
    *,
    prompt_arg: int | None = None,
    prompt_kwarg: int | None = None,
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
        return args[i]

    def _capture_prompt_from_kwarg(kwarg, /, fn, *args, **kwargs) -> str:
        return kwargs[kwarg]

    def _capture_prompts_with_options(capture_fns, /, fn, *args, **kwargs) -> str:
        for capture_fn in capture_fns:
            with contextlib.suppress(KeyError, IndexError):
                return capture_fn(fn, *args, **kwargs)

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
            # TODO: Handle when the arg value itself is `None`
            if arg_tag := _capture_from_arg_i(arg_i, fn, *args, **kwargs):
                tags[arg_tag_name] = arg_tag

        for kwarg in capture_tag_kwargs:
            # TODO: Handle when the kwarg value itself is `None`
            if kwarg_tag := kwargs.get(kwarg):
                tags[kwarg] = kwarg_tag

        return tags

    return partial(
        _trace_decorator,
        capture_prompt=capture_prompt,
        capture_tags=capture_tags,
        buffer=buffer,
    )
