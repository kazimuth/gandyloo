import re

from minesweeper import board

_NEWLINE = re.compile(r'\r\n?|\n')

def parse_start(buf, size=None, first=False):
    '''Extract a message from the start of a string.
    raise NotReadyError if the string does not contain an entire message.
    return (Response, rest of buf after Response is consumed).

    Arguments:
        size:  (width, height) of expected boards, or None if first=True.
        first: if this is the first message received (i.e. it should be a
               HELLO).
    '''

    if not _NEWLINE.search(buf):
        raise NotReadyError()

    # First message; should be a HELLO.
    if first:
        hello_match = HelloResp.regex.match(buf)
        if hello_match:
            message = hello_match.group(0)
            return HelloResp(message), buf[len(message):]
        else:
            raise InvalidResponseError('HELLO does not match spec', buf)

    boom_match = BoomResp.regex.match(buf)
    if boom_match:
        message = boom_match.group(0)
        return BoomResp(message), buf[len(message):]

    board_match = BoardResp.regex.match(buf)
    if board_match:
        width, height = size
        message = board_match.group(0)
        lines = message.splitlines(True) # keep newlines
        if len(lines) < height:
            # We haven't received the full board
            raise NotReadyError()

        # We may have received multiple boards; only take
        # the first one.
        message = ''.join(lines[:height])
        
        board = parse_board(message, size)
        return BoardResp(message, board), buf[len(message):]

    help_match = HelpResp.regex.match(buf)
    if help_match:
        message = help_match.group(0)
        return HelpResp(message), buf[len(message):]


class Response:
    '''A parsed response from a minesweeper server.

    Attributes:
        contents: the textual contents of this response.
        board:    if this response is a BOARD, a minesweeper.board.BoardResp
                  storing its contents.
        players:  if this response is a HELLO, the number of players given
                  by the HELLO.
        size:     if this response is a HELLO, the (width, height) of the
                  map given by the HELLO.
    '''


class HelpResp(Response):
    regex = re.compile(r'[^\r\n]+(\r\n?|\n)')

    def __init__(self, contents):
        if not HelpResp.regex.match(contents):
            raise InvalidResponseError('Invalid HELP message', contents)
        self.contents = contents


class BoomResp(Response):
    regex = re.compile(r'BOOM!(\r\n?|\n)')

    def __init__(self, contents):
        if not HelpResp.regex.match(contents):
            raise InvalidResponseError('Invalid HELP message', contents)
        self.contents = contents


class HelloResp(Response):
    regex = re.compile(r'Welcome to Minesweeper. '
            + r'BoardResp: ([0-9]+) columns by ([0-9]+) rows. '
            + r'Players: ([0-9]+) including you. '
            + r"Type 'help' for help.(?:\r\n?|\n)")

    def __init__(self, contents):
        match = HelloResp.regex.match(contents)
        self.size = (int(match.group(1)), int(match.group(2)))
        self.players = int(match.group(3))
        self.contents = contents


class BoardResp(Response):
    regex = re.compile(r'(([0-8F -] )*[0-8F -](\r\n?|\n))+')

    def __init__(self, contents, board):
        '''Note: board MUST be the result of parse_board(contents).'''
        self.board = board
        self.contents = contents


class CloseResp(Response):
    '''Represents the connection from the server closing.'''
    def __init__(self, reason):
        self.reason = reason


class InvalidResponseError(Exception):
    def __init__(self, cause, response):
        self.cause = cause
        self.response = response

    def __str__(self):
        return self.cause


class NotReadyError(Exception):
    pass


def parse_board(board_contents, expected_size):
    '''Parse a board into a BoardResp object.
    board_contents must match BoardResp.regex.'''
    lines = board_contents.splitlines()
    if lines[-1] == '':
        lines = lines[:-1]

    width, height = expected_size

    if len(lines) != height:
        raise InvalidResponseError('Wrong size board', board_contents)

    result = board.Board(width, height)

    for (y, line) in enumerate(lines):
        line_tiles = line[::2]
        if len(line_tiles) != width:
            raise InvalidResponseError('Wrong size board', board_contents)

        for (x, tile) in enumerate(line_tiles):
            if tile == '-':
                result[x, y] = board.Untouched()
            elif tile == 'F':
                result[x, y] = board.Flagged()
            elif tile == ' ':
                result[x, y] = board.Dug(0)
            else:
                try:
                    result[x, y] = board.Dug(int(tile))
                except:
                    raise InvalidResponseError('Invalid tile',
                            board_contents)

    return result
