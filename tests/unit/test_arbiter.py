"""State machine: allowed edges only, and every action is guarded."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from oslab.core import state  # noqa: E402
from oslab.core.arbiter import Arbiter  # noqa: E402
from oslab.core.errors import BadTransition  # noqa: E402


def test_idle_to_booting_allowed():
    arb = Arbiter()
    arb.to(state.BOOTING, "run")
    assert arb.state == state.BOOTING


def test_booting_cannot_jump_to_running_twice():
    arb = Arbiter()
    arb.to(state.BOOTING, "run")
    arb.to(state.RUNNING, "booted")
    with pytest.raises(BadTransition):
        arb.to(state.BOOTING, "again")


def test_guard_rejects_unlisted_source():
    arb = Arbiter()
    arb.to(state.BOOTING, "run")
    with pytest.raises(BadTransition):
        arb.guard(state.STOPPED)


def test_running_can_pause_and_hit():
    arb = Arbiter()
    arb.to(state.BOOTING, "run")
    arb.to(state.RUNNING, "booted")
    arb.to(state.STOPPED, "pause")
    assert arb.state == state.STOPPED
    arb.to(state.RUNNING, "cont")


def test_faulted_is_reachable_from_running():
    assert state.FAULTED in state.ALLOWED[state.RUNNING]
