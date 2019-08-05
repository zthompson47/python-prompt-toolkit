from __future__ import unicode_literals

import pytest

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.application import current


@pytest.fixture
async def _nursery(nursery):
    current.nursery = nursery


@pytest.fixture
def _history():
    " Prefilled history. "
    history = InMemoryHistory()
    history.append_string('alpha beta gamma delta')
    history.append_string('one two three four')
    return history


# Test yank_last_arg.


async def test_empty_history(_nursery):
    buf = Buffer()
    buf.yank_last_arg()
    assert buf.document.current_line == ''


async def test_simple_search(_history, _nursery):
    buff = Buffer(history=_history)
    buff.yank_last_arg()
    assert buff.document.current_line == 'four'


async def test_simple_search_with_quotes(_history, _nursery):
    _history.append_string("""one two "three 'x' four"\n""")
    buff = Buffer(history=_history)
    buff.yank_last_arg()
    assert buff.document.current_line == '''"three 'x' four"'''


async def test_simple_search_with_arg(_history, _nursery):
    buff = Buffer(history=_history)
    buff.yank_last_arg(n=2)
    assert buff.document.current_line == 'three'


async def test_simple_search_with_arg_out_of_bounds(_history, _nursery):
    buff = Buffer(history=_history)
    buff.yank_last_arg(n=8)
    assert buff.document.current_line == ''


async def test_repeated_search(_history, _nursery):
    buff = Buffer(history=_history)
    buff.yank_last_arg()
    buff.yank_last_arg()
    assert buff.document.current_line == 'delta'


async def test_repeated_search_with_wraparound(_history, _nursery):
    buff = Buffer(history=_history)
    buff.yank_last_arg()
    buff.yank_last_arg()
    buff.yank_last_arg()
    assert buff.document.current_line == 'four'


# Test yank_last_arg.


async def test_yank_nth_arg(_history, _nursery):
    buff = Buffer(history=_history)
    buff.yank_nth_arg()
    assert buff.document.current_line == 'two'


async def test_repeated_yank_nth_arg(_history, _nursery):
    buff = Buffer(history=_history)
    buff.yank_nth_arg()
    buff.yank_nth_arg()
    assert buff.document.current_line == 'beta'


async def test_yank_nth_arg_with_arg(_history, _nursery):
    buff = Buffer(history=_history)
    buff.yank_nth_arg(n=2)
    assert buff.document.current_line == 'three'
