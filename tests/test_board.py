import pytest
from minesweeper import board

def test_init():
    b = board.Board(10, 10)
    for x, y in ((x,y) for x in xrange(10) for y in xrange(10)):
        assert isinstance(b[x, y], board.Untouched)

    with pytest.raises(AssertionError):
        b = board.Board(0, -1)

def test_tiles():
    assert board.Untouched() == board.Untouched()
    assert board.Flagged() == board.Flagged()
    for i in xrange(9):
        assert board.Dug(i) == board.Dug(i)

def test_setget():
    b = board.Board(100, 100)
    for x, y in ((x,y) for x in xrange(100) for y in xrange(100)):
        b[x, y] = board.Dug(x % 9)
    for x, y in ((x,y) for x in xrange(100) for y in xrange(100)):
        assert b[x, y] == board.Dug(x % 9)

    b[1, 57] = board.Untouched()
    assert b[1, 57] == board.Untouched()
    b[1, 58] = board.Flagged()
    assert b[1, 58] == board.Flagged()

def test_oob():
    b = board.Board(10, 11)
    with pytest.raises(AssertionError):
        b[-1, -1] = board.Dug(1)
    with pytest.raises(AssertionError):
        b[0, 100]
    with pytest.raises(AssertionError):
        b[-1, 30] = board.Dug(1)
    with pytest.raises(AssertionError):
        b[57, 100]

