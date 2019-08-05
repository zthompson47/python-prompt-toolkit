"""
patch_stdout
============

This implements a context manager that ensures that print statements within
it won't destroy the user interface. The context manager will replace
`sys.stdout` by something that draws the output above the current prompt,
rather than overwriting the UI.

Usage::

    with patch_stdout(application):
        ...
        application.run()
        ...

Multiple applications can run in the body of the context manager, one after the
other.
"""
import sys
import threading
#from asyncio import get_event_loop
from contextlib import contextmanager
from typing import Generator, List, Optional, TextIO, cast

import trio
#import logging, sys
#logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
#LOG = logging.getLogger("patch_stdout")

from .application import run_in_terminal

__all__ = [
    'patch_stdout',
    'StdoutProxy',
]


@contextmanager
def patch_stdout(raw: bool = False, nursery=None) -> Generator[None, None, None]:
    """
    Replace `sys.stdout` by an :class:`_StdoutProxy` instance.

    Writing to this proxy will make sure that the text appears above the
    prompt, and that it doesn't destroy the output from the renderer.  If no
    application is curring, the behaviour should be identical to writing to
    `sys.stdout` directly.

    :param raw: (`bool`) When True, vt100 terminal escape sequences are not
                removed/escaped.
    """
    proxy = cast(TextIO, StdoutProxy(raw=raw, nursery=nursery))

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # Enter.
    sys.stdout = proxy
    sys.stderr = proxy

    try:
        yield
    finally:
        # Exit.
        proxy.flush()

        sys.stdout = original_stdout
        sys.stderr = original_stderr


class StdoutProxy:
    """
    Proxy object for stdout which captures everything and prints output above
    the current application.
    """
    def __init__(self, raw: bool = False,
                 original_stdout: Optional[TextIO] = None,
                 nursery=None) -> None:

        original_stdout = original_stdout or sys.__stdout__

        self.original_stdout = original_stdout

        self._lock = threading.RLock()
        self._raw = raw
        self._buffer: List[str] = []

        # errors/encoding attribute for compatibility with sys.__stdout__.
        self.errors = original_stdout.errors
        self.encoding = original_stdout.encoding

        #self.loop = get_event_loop()
        self.nursery = nursery

    def _write_and_flush(self, text: str) -> None:
        """
        Write the given text to stdout and flush.
        If an application is running, use `run_in_terminal`.
        """
        if not text:
            # Don't bother calling `run_in_terminal` when there is nothing to
            # display.
            return

        def write_and_flush() -> None:
            self.original_stdout.write(text)
            self.original_stdout.flush()

        async def write_and_flush_in_loop() -> None:
            #z is it `run_in_executor_with_context`?
            # If an application is running, use `run_in_terminal`, otherwise
            # call it directly.
            #LOG.debug(f"<>inner<> {self.nursery}")
            run_in_terminal(write_and_flush, in_executor=False, nursery=self.nursery)

        # Make sure `write_and_flush` is executed *in* the event loop, not in
        # another thread.
        #self.loop.call_soon_threadsafe(write_and_flush_in_loop)
        #LOG.debug(f"<>outer<> {self.nursery}")
        #self.nursery.start_soon(trio.to_thread.run_sync, write_and_flush_in_loop)
        self.nursery.start_soon(write_and_flush_in_loop)

    def _write(self, data: str) -> None:
        """
        Note: print()-statements cause to multiple write calls.
              (write('line') and write('\n')). Of course we don't want to call
              `run_in_terminal` for every individual call, because that's too
              expensive, and as long as the newline hasn't been written, the
              text itself is again overwritten by the rendering of the input
              command line. Therefor, we have a little buffer which holds the
              text until a newline is written to stdout.
        """
        if '\n' in data:
            # When there is a newline in the data, write everything before the
            # newline, including the newline itself.
            before, after = data.rsplit('\n', 1)
            to_write = self._buffer + [before, '\n']
            self._buffer = [after]

            text = ''.join(to_write)
            self._write_and_flush(text)
        else:
            # Otherwise, cache in buffer.
            self._buffer.append(data)

    def _flush(self) -> None:
        text = ''.join(self._buffer)
        self._buffer = []
        self._write_and_flush(text)

    def write(self, data: str) -> int:
        with self._lock:
            self._write(data)

        return len(data)  # Pretend everything was written.

    def flush(self) -> None:
        """
        Flush buffered output.
        """
        with self._lock:
            self._flush()

    def fileno(self) -> int:
        """
        Return file descriptor.
        """
        # This is important for code that expects sys.stdout.fileno() to work.
        return self.original_stdout.fileno()
