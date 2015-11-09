import re

from minesweeper import message, board

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
        hello_match = message.HelloResp.regex.match(buf)
        if hello_match:
            contents = hello_match.group(0)
            return message.HelloResp(contents), buf[len(contents):]
        else:
            raise InvalidResponseError('HELLO does not match spec', buf)

    boom_match = message.BoomResp.regex.match(buf)
    if boom_match:
        contents = boom_match.group(0)
        return message.BoomResp(contents), buf[len(contents):]

    board_match = message.BoardResp.regex.match(buf)
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
        return message.BoardResp(contents, board), buf[len(contents):]

    help_match = message.HelpResp.regex.match(buf)
    if help_match:
        contents = help_match.group(0)
        return message.HelpResp(contents), buf[len(contents):]

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
        return self.cause


class NotReadyError(Exception):
    pass

