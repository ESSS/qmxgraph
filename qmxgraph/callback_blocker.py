# Heavily based on `pytestqt.wait_signal.CallbackBlocker`.
from typing import Any, Callable, Optional

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal


class CallbackBlocker:
    """
    An object which checks if the returned callback gets called.

    Intended to be used as a context manager.

    :ivar int timeout:
        Maximum time to wait for the callback to be called.

    :ivar tuple args:
        The arguments with which the callback was called, or None if the
        callback wasn't called at all.

    :ivar dict kwargs:
        The keyword arguments with which the callback was called, or None if
        the callback wasn't called at all.
    """

    DEFAULT_TIMEOUT = 1000

    def __init__(
        self, timeout: int = DEFAULT_TIMEOUT, msg: Optional[str] = None,
    ):
        self.timeout = timeout
        self.args = None
        self.msg = msg
        self.kwargs = None
        self.called = False
        self._loop = QtCore.QEventLoop()
        if timeout is None:
            self._timer = None
        else:
            self._timer = QtCore.QTimer(self._loop)
            self._timer.setSingleShot(True)
            self._timer.setInterval(timeout)

    def wait(self) -> None:
        """
        Waits until either the returned callback is called or timeout is
        reached.
        """
        __tracebackhide__ = True
        if self.called:
            return
        if self._timer is not None:
            self._timer.timeout.connect(self._quit_loop_by_timeout)
            self._timer.start()
        self._loop.exec_()
        if not self.called:
            msg = f"Callback wasn't called after {self.timeout}ms."
            if self.msg:
                msg += f'\n> {self.msg}'
            raise TimeoutError(msg)

    def _quit_loop_by_timeout(self) -> None:
        try:
            self._cleanup()
        finally:
            self._loop.quit()

    def _cleanup(self) -> None:
        if self._timer is not None:
            silent_disconnect(self._timer.timeout, self._quit_loop_by_timeout)
            self._timer.stop()
            self._timer = None

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        # Not inside the try: block, as if self.called is True, we did quit the
        # loop already.
        if self.called:
            raise CallbackCalledTwiceError("Callback called twice")
        try:
            self.args = args
            self.kwargs = kwargs
            self.called = True
            self._cleanup()
        finally:
            self._loop.quit()

    def __enter__(self) -> 'CallbackBlocker':
        return self

    def __exit__(self, type, value, traceback) -> None:
        __tracebackhide__ = True
        if value is None:
            # only wait if no exception happened inside the "with" block.
            self.wait()


class CallbackCalledTwiceError(Exception):
    """
    The exception raise by `CallbackBlocker` instances if called more
    than once.
    """


def silent_disconnect(signal: pyqtSignal, slot: Callable) -> None:
    """
    Disconnects a signal from a slot, ignoring errors. Sometimes Qt
    might disconnect a signal automatically for unknown reasons.
    """
    from contextlib import suppress
    with suppress(TypeError, RuntimeError):
        signal.disconnect(slot)
