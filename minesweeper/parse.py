import re

from minesweeper import message, board

_NEWLINE = re.compile(r'\r\n?|\n')

class ResponseParsers:
    HELLO = re.compile(r'Welcome to Minesweeper. '
            + r'Board: ([0-9]+) columns by ([0-9]+) rows. '
            + r'Players: ([0-9]+) including you. '
            + r"Type 'help' for help.(?:\r\n?|\n)")
    BOOM = re.compile(r'BOOM!(\r\n?|\n)')
    BOARD = re.compile(r'(([0-8F -] )*[0-8F -](\r\n?|\n))+')
    HELP = re.compile(r'[^\r\n]+(\r\n?|\n)')

def parse_start(buf, size=None, first=False):
    '''Extract a message from the start of a string.
    raise NotReadyError if the string does not contain an entire message.
    return (Response, rest of buf after Response is consumed).

    Arguments:
        size:  (width, height) of expected boards, or None if first=True.
        first: if this is the first message received (i.e. it should be a
               HELLO).
    '''
    
    while buf.startswith('\n') or buf.startswith('\r'):
        buf = buf[1:]
    
    if not _NEWLINE.search(buf):
        raise NotReadyError()

    # First message; must be a HELLO.
    if first:
        hello_match = ResponseParsers.HELLO.match(buf)
        if hello_match:
            size = (int(hello_match.group(1)), int(hello_match.group(2)))
            players = int(hello_match.group(3))
            return message.HelloResp(size, players), buf[hello_match.end():]
        else:
            raise InvalidResponseError('HELLO does not match spec', buf)

    boom_match = ResponseParsers.BOOM.match(buf)
    if boom_match:
        return message.BoomResp(), buf[boom_match.end():]

    board_match = ResponseParsers.BOARD.match(buf)
    if board_match:
        width, height = size
        contents = board_match.group(0)
        lines = contents.splitlines(True) # keep newlines
        if len(lines) < height:
            # We haven't received the full board
            raise NotReadyError()

        # We may have received multiple boards; only take
        # the first one.
        contents = ''.join(lines[:height])

        board = parse_board(contents, size)
        return message.BoardResp(board), buf[len(contents):]

    help_match = ResponseParsers.HELP.match(buf)
    if help_match:
        contents = help_match.group(0)
        return message.HelpResp(contents), buf[help_match.end():]

    raise InvalidResponseError("No match on response (this should be impossible)", buf)


def parse_board(board_contents, expected_size):
    '''Parse a board into a message.BoardResp object.
    board_contents must match message.BoardResp.regex.'''
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


class InvalidResponseError(Exception):
    def __init__(self, cause, response):
        self.cause = cause
        self.response = response

    def __str__(self):
        return self.cause + ": " + repr(self.response)


class NotReadyError(Exception):
    pass

