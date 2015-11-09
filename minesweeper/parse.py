import re

from minesweeper import board

def parse(message, first=False):
    '''Parse a message into a Response.'''

    if first:
        return Response(ResponseType.HELLO, message)

    if ResponseType.BOOM.regex.match(message):
        return Response(ResponseType.BOOM, message)

    if ResponseType.BOARD.regex.match(message):
        return Response(ResponseType.BOARD, message)

    return Response(ResponseType.HELP, message)

class ResponseType:
    '''Types of message that can be received from the Minesweeper Server.
    
    Attributes:
        name: the NAME of the response type.
        regex: a regular expression that matches responses of the type.

    Variants:
        ResponseType.HELLO
        ResponseType.HELP
        ResponseType.BOARD
        ResponseType.BOOM
    '''

    def __init__(self, name, regex):
        self.name = name
        self.regex = re.compile(regex)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

# Make a wacky enum-thing.
ResponseType.HELLO = ResponseType('HELLO', r'Welcome to Minesweeper. Board: ([0-9]+) columns by ([0-9]+) rows. '
        + r"Players: ([0-9]+) including you. Type 'help' for help.(?:\r\n?|\n)$")
ResponseType.HELP  = ResponseType('HELP',  r'[^\r\n]+(\r\n?|\n)$')
ResponseType.BOARD = ResponseType('BOARD', r'(([0-8F -] )*[0-8F -](\r\n?|\n))+$')
ResponseType.BOOM  = ResponseType('BOOM',  r'BOOM!(\r\n?|\n)$')


class Response:
    '''A parsed response from a minesweeper server.

    Attributes:
        type:     the ResponseType of this response.
        contents: the textual contents of this response.
        board:    if this response is a BOARD, a minesweeper.board.Board
                  storing its contents.
        players:  if this response is a HELLO, the number of players given
                  by the HELLO.
        size:     if this response is a HELLO, the (width, height) of the
                  map given by the HELLO.
    '''

    def __init__(self, type, contents):
        '''Create a response of a type, with the given contents.'''
        if not type.regex.match(contents):
            raise InvalidResponseError(contents)

        self.type = type
        self.contents = contents

        if self.type == ResponseType.BOARD:
            self.board = _parse_board(self.contents)
        else:
            self.board = None

        if self.type == ResponseType.HELLO:
            match = ResponseType.HELLO.regex.match(self.contents)
            self.size = (int(match.group(1)), int(match.group(2)))
            self.players = int(match.group(3))
        else:
            self.size = None
            self.players = None

class InvalidResponseError(Exception):
    def __init__(self, response):
        self.response = response

    def __str__(self):
        return self.response

def _parse_board(board_contents):
    '''Parse a board into a Board object.'''
    lines = board_contents.splitlines()
    print lines
    if lines[-1] == '':
        lines = lines[:-1]

    assert len(lines) > 0
    
    height = len(lines)
    width = len(lines[0][::2])

    print width, height

    result = board.Board(width, height)

    for (y, line) in enumerate(lines):
        for (x, tile) in enumerate(line[::2]):
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
                    raise InvalidResponseError(board_contents)

    return result
