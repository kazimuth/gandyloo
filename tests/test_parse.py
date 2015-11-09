import pytest
from minesweeper import parse, board

def test_parse_first():
    resp = parse.parse("Welcome to Minesweeper. Board: 40 columns by 37 rows. Players: 1 including you. Type 'help' for help.\n", True)
    assert resp.type == parse.ResponseType.HELLO
    assert resp.size == (40, 37)
    assert resp.players == 1

    with pytest.raises(parse.InvalidResponseError):
        parse.parse("Hello.", True)

def test_parse_boom():
    resp = parse.parse("Boom!\n")
    assert resp.type == parse.ResponseType.BOOM
    resp = parse.parse("Boom!\r\n")
    assert resp.type == parse.ResponseType.BOOM
    resp = parse.parse("Boom!\r")
    assert resp.type == parse.ResponseType.BOOM

def test_parse_board():
    # Not actually a valid board, but that's okay
    resp = parse.parse('- F -\n  8 2\n')
    assert resp.type == parse.ResponseType.BOARD
    assert resp.board.width == 3
    assert resp.board.height == 2
    assert resp.board[0, 0] == board.Untouched()
    assert resp.board[1, 0] == board.Flagged()
    assert resp.board[2, 0] == board.Untouched()
    assert resp.board[0, 1] == board.Dug(0)
    assert resp.board[1, 1] == board.Dug(8)
    assert resp.board[2, 1] == board.Dug(2)
