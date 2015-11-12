#!/usr/bin/env python2
import urwid

from minesweeper import board, parse, message


class FlatMinesweeperWidget(urwid.Widget):
    _sizing = frozenset(['fixed'])

    def __init__(self, command_sink):
        self.command_sink = command_sink
        self.size = (1, 1) # (columns, rows)

        # one of 'wait', 'board', 'boom'
        # 'wait': waiting for the first board to be sent
        # 'board': ready to render a board
        # 'boom': ready to render a BOOM
        self.state = 'wait'
        self.selected = (0, 0)

    def render(self, size, focus=False):
        assert size == ()

        if self.state == 'wait':
            result = urwid.SolidCanvas('#', *self.size)
            result = urwid.CompositeCanvas(result)
            result.fill_attr(Palette.GRAY)
            return result
        
        if self.state == 'boom':
            result = urwid.SolidCanvas('#', *self.size)
            result = urwid.CompositeCanvas(result)
            result.fill_attr(Palette.BOOM)
            return result

        if self.state == 'board':
            width, height = self.size
            result_strings = []
            result_attrs = []
            for y in range(height):
                row = ''
                row_attr = []
                for x in range(width):
                    tile = self.board[x, y]
                    t = type(tile)

                    if t == board.Untouched:
                        row += '-'
                        row_attr.append((Palette.UNTOUCHED, 1))
                    elif t == board.Flagged:
                        row += 'F'
                        row_attr.append((Palette.FLAGGED, 1))
                    elif t == board.Dug:
                        if tile.surrounding == 0:
                            row += ' '
                        else:
                            row += str(tile.surrounding)
                        row_attr.append((Palette.DUG[tile.surrounding], 1))
                    if (x, t) == self.selected:
                        row_attr[-1] = Palette.SELECTED

                result_strings.append(row)
                result_attrs.append(row_attr)

            return urwid.TextCanvas(result_strings, result_attrs,
                    cursor=self.selected,
                    maxcol=width,
                    check_width=True)


    def pack(self, size, focus=False):
        #assert size == ()
        return self.size

    def rows(self, maxcol, focus=False):
        assert maxcol == ()
        return self.size[1]

    def columns(self, maxcol, focus=False):
        assert maxcol == ()
        return self.size[0]

    def selectable(self):
        return self.state == 'board'

    def keypress(self, size, key):
        assert size == ()

        k = key.lower() # don't care about 'shift'

        # Movement
        # Support WASD, hjkl+yubn, arrow keys
        if k in 'wasdhjklyubn' or k in ('up', 'left', 'down', 'right'):
            if k in ('w', 'k', 'up'):
                delta = (0, -1)
            elif k in ('a', 'h', 'left'):
                delta = (-1, 0)
            elif k in ('s', 'j', 'down'):
                delta = (0, 1)
            elif k in ('d', 'l', 'right'):
                delta = (1, 0)
            elif k == 'y':
                delta = (-1, -1)
            elif k == 'u':
                delta = (1, -1)
            elif k == 'b':
                delta = (-1, 1)
            elif k == 'n':
                delta = (1, 1)

            x, y = self.selected
            dx, dy = delta
            width, height = self.size

            self.selected = ((x+dx) % width, (y+dy) % height)
            self._invalidate()
            return # handled

        # Flagging and digging
        if k == 'enter' or k == '1':
            self._dig()
            return # handled
        elif k == "'" or k == '"' or k == '2' or k == 'f':
            self._flag()
            return # handled

        return key # not handled

    def mouse_event(self, size, event, button, col, row, focus):
        assert size == ()

        if 'mouse press' in event:
            self.selected = (col, row)
            if button == 1:
                # Left click; dig
                self._dig()
            if button == 2:
                # Right click; flag
                self._flag()
            # Other click; select, but do nothing else

        return True # handled

    def get_cursor_coords(self, size):
        assert size == ()

        return self.selected

    # Custom minesweeper messaging stuff

    def _dig(self):
        '''Dig if the tile at self.selected can be dug.'''
        tiletype = type(self.board[self.selected])
        if tiletype == board.Untouched:
            self.command_sink.command(message.DigCommand(self.selected))

    def _flag(self):
        '''Flag or deflag the tile at self.selected as necessary.'''
        tiletype = type(self.board[self.selected])
        if tiletype == board.Untouched:
            self.command_sink.command(message.FlagCommand(self.selected))
        elif tiletype == board.Flagged:
            self.command_sink.command(message.DeflagCommand(self.selected))

    def response(self, resp):
        '''Process a response from the server.'''

        if type(resp) == message.HelloResp:
            self.size = resp.size
            self.command_sink.command(message.LookCommand())
            self._invalidate()
        elif type(resp) == message.BoardResp:
            assert self.size == (resp.board.width, resp.board.height)
            self.board = resp.board
            self.state = 'board'
            self._invalidate()
        elif type(resp) == message.BoomResp:
            self.state = 'boom'
            self._invalidate()


class Palette:
    '''Colors available to use.
    GRAY is just gray.
    BOOM is bold black on red.
    UNTOUCHED is light gray on white.
    FLAGGED is red on white.
    SELECTED is white on blue.
    DUG[0:9] are colors ranging from blue to red on black.
    '''
    GRAY = 'gray'
    BOOM = 'boom'
    UNTOUCHED = 'untouched'
    FLAGGED = 'flagged'
    SELECTED = 'selected'
    DUG = ['dug' + str(n) for n in xrange(9)]

PALETTE = [
        (Palette.GRAY, 'light gray', 'dark gray'),
        (Palette.BOOM, 'black,bold', 'dark red'),
        (Palette.UNTOUCHED, 'dark gray', 'white'),
        (Palette.SELECTED, 'white', 'dark blue'),
        (Palette.FLAGGED, 'dark red,bold', 'white')
]
PALETTE += zip(Palette.DUG, 
        ['black'] * 8,
        ['', 'dark blue', 'dark green', 'yellow',
            'dark red', 'light red', 'light magenta', 'white'])

def exit_on_q(key):
    if type(key) == str:
        if key.lower() in ('q', 'ctrl c', 'ctrl d'):
            raise urwid.ExitMainLoop()


relay = message.MessageRelay()
core_widget = FlatMinesweeperWidget(relay)
widget = urwid.Overlay(core_widget, urwid.SolidFill(' '), 'center', 'pack', 'middle', 'pack')
from minesweeper.connection import MinesweeperClient
client = MinesweeperClient(relay)
relay.add_command_receiver(client)
relay.add_response_receiver(core_widget)

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

point = TCP4ClientEndpoint(reactor, 'localhost', 4444)
d = connectProtocol(point, client)

loop = urwid.MainLoop(widget, PALETTE, unhandled_input=exit_on_q)
loop.screen.set_terminal_properties(colors=16)
loop.event_loop = urwid.TwistedEventLoop(reactor)
loop.run()
