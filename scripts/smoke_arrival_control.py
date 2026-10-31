"""Select quiet login paths for unrelated PTY checks; never disable gameplay.

A new login legitimately draws different disruption locations. Historical trade,
combat and report checks select a normally returned path without a committed
forced warp. A recorded forced warp or scanner disruption warning interrupts that attempt; after
its child has stopped, restore the exact pre-login disposable world and retry.
Other errors always propagate. Dedicated arrival checks use unfiltered drivers or observe_disruption().
"""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
import re

_observing=ContextVar('observe_disruption',default=False)
MARKER=b'A *-BLACK HOLE-* grabs you! Forced warp saved:'
SCANNER_WARNING=re.compile(rb'Danger scanner has detected the following in sector [0-9]+!\r?\n\*\* Space-time disruption detected!')

class DisruptionInterruption(Exception):
    pass


def reject_disruption(output):
    if not _observing.get() and (MARKER in output or SCANNER_WARNING.search(output)):
        raise DisruptionInterruption()


@contextmanager
def observe_disruption():
    token=_observing.set(True)
    try:
        yield
    finally:
        _observing.reset(token)


def without_disruption(play):
    @wraps(play)
    def quiet(data,*args,**kwargs):
        if _observing.get():
            return play(data,*args,**kwargs)
        # The oldest harness passes the CLI arguments rather than the data path.
        location=data[data.index('-data')+1] if isinstance(data,list) else data
        path=Path(location)/'world.json'
        baseline=path.read_bytes()
        for _ in range(128):
            try:
                return play(data,*args,**kwargs)
            except DisruptionInterruption:
                # Every decorated play owns and stops its process in finally.
                # Keep the stable lock inode; only restore the disposable save.
                path.write_bytes(baseline)
        raise AssertionError('No quiet disruption path after 128 bounded login attempts')
    return quiet
