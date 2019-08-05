from __future__ import unicode_literals

import pytest

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.application import current

@pytest.fixture
async def _buffer(nursery):
    current.nursery = nursery
    buff = Buffer()
    return buff


async def test_initial(_buffer):
    assert _buffer.text == ''
    assert _buffer.cursor_position == 0


async def test_insert_text(_buffer):
    _buffer.insert_text('some_text')
    assert _buffer.text == 'some_text'
    assert _buffer.cursor_position == len('some_text')


async def test_cursor_movement(_buffer):
    _buffer.insert_text('some_text')
    _buffer.cursor_left()
    _buffer.cursor_left()
    _buffer.cursor_left()
    _buffer.cursor_right()
    _buffer.insert_text('A')

    assert _buffer.text == 'some_teAxt'
    assert _buffer.cursor_position == len('some_teA')


async def test_backspace(_buffer):
    _buffer.insert_text('some_text')
    _buffer.cursor_left()
    _buffer.cursor_left()
    _buffer.delete_before_cursor()

    assert _buffer.text == 'some_txt'
    assert _buffer.cursor_position == len('some_t')


async def test_cursor_up(_buffer):
    # Cursor up to a line thats longer.
    _buffer.insert_text('long line1\nline2')
    _buffer.cursor_up()

    assert _buffer.document.cursor_position == 5

    # Going up when already at the top.
    _buffer.cursor_up()
    assert _buffer.document.cursor_position == 5

    # Going up to a line that's shorter.
    _buffer.reset()
    _buffer.insert_text('line1\nlong line2')

    _buffer.cursor_up()
    assert _buffer.document.cursor_position == 5


async def test_cursor_down(_buffer):
    _buffer.insert_text('line1\nline2')
    _buffer.cursor_position = 3

    # Normally going down
    _buffer.cursor_down()
    assert _buffer.document.cursor_position == len('line1\nlin')

    # Going down to a line that's shorter.
    _buffer.reset()
    _buffer.insert_text('long line1\na\nb')
    _buffer.cursor_position = 3

    _buffer.cursor_down()
    assert _buffer.document.cursor_position == len('long line1\na')


async def test_join_next_line(_buffer):
    _buffer.insert_text('line1\nline2\nline3')
    _buffer.cursor_up()
    _buffer.join_next_line()

    assert _buffer.text == 'line1\nline2 line3'

    # Test when there is no '\n' in the text
    _buffer.reset()
    _buffer.insert_text('line1')
    _buffer.cursor_position = 0
    _buffer.join_next_line()

    assert _buffer.text == 'line1'


async def test_newline(_buffer):
    _buffer.insert_text('hello world')
    _buffer.newline()

    assert _buffer.text == 'hello world\n'


async def test_swap_characters_before_cursor(_buffer):
    _buffer.insert_text('hello world')
    _buffer.cursor_left()
    _buffer.cursor_left()
    _buffer.swap_characters_before_cursor()

    assert _buffer.text == 'hello wrold'
