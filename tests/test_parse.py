import pytest
from gandyloo import parse, message, board

def test_parse_first():
    resp, new_buf = parse.parse_start("Welcome to Minesweeper. Board: 40 columns by 37 rows. Players: 1 including you. Type 'help' for help.\n", first=True)
    assert isinstance(resp, message.HelloResp)
    assert resp.size == (40, 37)
    assert resp.players == 1
    assert new_buf == ''

    with pytest.raises(parse.InvalidResponseError):
        parse.parse_start("HelloResp.\r\n", None, first=True)

def test_parse_boom():
    resp, new_buf = parse.parse_start("BOOM!\n", (1,1))
    assert isinstance(resp, message.BoomResp)
    assert new_buf == ''
    resp, new_buf = parse.parse_start("BOOM!\r\n", (1,1))
    assert isinstance(resp, message.BoomResp)
    assert new_buf == ''
    resp, new_buf = parse.parse_start("BOOM!\r", (1,1))
    assert isinstance(resp, message.BoomResp)
    assert new_buf == ''

def test_parse_board():
    # Not actually a valid board, but that's okay
    resp, new_buf = parse.parse_start('- F -\r\n  8 2\n', (3, 2))
    assert isinstance(resp, message.BoardResp)
    assert new_buf == ''
    assert resp.board.width == 3
    assert resp.board.height == 2
    assert resp.board[0, 0] == board.Untouched()
    assert resp.board[1, 0] == board.Flagged()
    assert resp.board[2, 0] == board.Untouched()
    assert resp.board[0, 1] == board.Dug(0)
    assert resp.board[1, 1] == board.Dug(8)
    assert resp.board[2, 1] == board.Dug(2)

def test_parse_board_wrongsize():
    with pytest.raises(parse.InvalidResponseError):
        parse.parse_start('- -\r-\n', (2,2))

def test_parse_help():
    resp, new_buf = parse.parse_start("HELP!\n", (1,1))
    assert isinstance(resp, message.HelpResp)
    assert new_buf == ''
    resp, new_buf = parse.parse_start("rtfm.\r\n", (1,1))
    assert isinstance(resp, message.HelpResp)
    assert new_buf == ''
    resp, new_buf = parse.parse_start('oh no '*1500 + '\r', (1,1))
    assert isinstance(resp, message.HelpResp)
    assert new_buf == ''

def test_parse_unfinished():
    with pytest.raises(parse.NotReadyError):
        parse.parse_start('hi', first=True)

    with pytest.raises(parse.NotReadyError):
        parse.parse_start('banana banana banana', (1, 1))

    with pytest.raises(parse.NotReadyError):
        parse.parse_start('- -\n- -\n', (2, 3))

def test_parse_bufconsume():
    resp, new_buf = parse.parse_start("Welcome to Minesweeper. Board: 40 columns by 37 rows. Players: 1 including you. Type 'help' for help.\nRTFM\nRTFM\n", first=True)
    assert new_buf == 'RTFM\nRTFM\n'
    assert isinstance(resp, message.HelloResp)
    assert resp.size == (40, 37)
    assert resp.players == 1

    resp, new_buf = parse.parse_start('BOOM!\rBOOM!\r\n', (1, 1))
    assert new_buf == 'BOOM!\r\n'
    assert isinstance(resp, message.BoomResp)

    resp, new_buf = parse.parse_start('RTFM\ri am an unfinished message',
            (1, 1))
    assert new_buf == 'i am an unfinished message'
    assert isinstance(resp, message.HelpResp)

    resp, new_buf = parse.parse_start('-   F 8 -\n- - - - -\n', (5, 1))
    assert new_buf == '- - - - -\n'
    assert isinstance(resp, message.BoardResp)
    assert resp.board[0, 0] == board.Untouched()
    assert resp.board[1, 0] == board.Dug(0)
    assert resp.board[2, 0] == board.Flagged()
    assert resp.board[3, 0] == board.Dug(8)
    assert resp.board[4, 0] == board.Untouched()
