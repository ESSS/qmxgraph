from contextlib import contextmanager
from enum import Enum
from typing import Callable, Optional, Tuple, Any, Generator

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtTest import QTest
from attr import define
from pytestqt.wait_signal import SignalBlocker, CallbackBlocker


def wait_signals(*signals: pyqtSignal, timeout: int=1000, raising: bool=True, check_params_cb=None):
    """

    """
    # TODO[ASIM-4284]: remove this as no longer used.
    blocker = SignalBlocker(
        timeout=timeout, raising=raising, check_params_cb=check_params_cb
    )
    for signal in signals:
        blocker.connect(signal)
    return blocker

@contextmanager
def wait_signals_called(*signals: pyqtSignal, timeout_ms: int=1000, check_params_cb=None) -> Generator["_Callback", None, None]:
    """

    """
    callback = _Callback()
    for signal in signals:
        signal.connect(callback)
    yield callback

    def success() -> bool:
        return callback.was_called() and (check_params_cb is None or check_params_cb(*callback.args))

    wait_until(success, timeout_ms=timeout_ms)


def wait_callback(*, timeout_ms=1000):
    """

    """
    # TODO[ASIM-4284]: remove this as no longer used.
    blocker = CallbackBlocker(timeout=timeout_ms, raising=True)
    return blocker


@contextmanager
def wait_callback_called(*, timeout_ms=1000) -> Generator["_Callback", None, None]:
    """

    """
    callback = _Callback()
    yield callback
    wait_until(callback.was_called, timeout_ms=timeout_ms)


@define
class _Callback:
    args: Optional[Tuple[Any, ...]] = None

    def __call__(self, *args: Any) -> None:
        self.args = args

    def was_called(self) -> bool:
        return self.args is not None



class _Sentinel(Enum):
    value = 0


def silent_disconnect(signal: pyqtSignal, slot: Callable) -> None:
    """
    Disconnects a signal from a slot, ignoring errors. Sometimes Qt
    might disconnect a signal automatically for unknown reasons.
    """
    # TODO[ASIM-4284]: remove this method.
    from contextlib import suppress
    with suppress(TypeError, RuntimeError):
        signal.disconnect(slot)


def wait_until(predicate: Callable[[], bool], *, timeout_ms: int=1000, error_callback: Optional[Callable[[], str]]=None, wait_interval_ms: int =1) -> None:
    """

    """
    __tracebackhide__ = True
    import time

    start = time.perf_counter()

    def timed_out():
        elapsed = time.perf_counter() - start
        elapsed_ms = elapsed * 1000
        return elapsed_ms > timeout_ms

    while True:
        result = predicate()
        if result:
            return
        else:
            if timed_out():
                msg = "wait_until timed out in %s milliseconds" % timeout_ms
                if error_callback is not None:
                    msg += f":\n{error_callback()}"
                raise TimeoutError(msg)

        QTest.qWait(wait_interval_ms)
