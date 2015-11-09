import re

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
            + r'Board: ([0-9]+) columns by ([0-9]+) rows. '
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


