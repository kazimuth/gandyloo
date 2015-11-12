#!/usr/bin/env python2
import urwid

from minesweeper import board, parse, message

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

class MinesweeperMapMinimap(object):
    '''Class that handles a map-minimap Widget pair. It's a mix of model and
    controller.
    The map is large, and shows actual tiles. Its 'aperture' is the current
    area it is showing - in case the map is larger than available space.
    It has borders that show the edge of the board.
    The minimap is a sort of two-dimensional scrollbar. It simply shows the
    size of the map, and a rectangle of the currently visible area. It isn't
    actually directly selectable.
    We cheat to store the size of the aperture so that the minimap can render
    it's scroll rectangle in the correct size.
    Access .map to get the Map widget, and .minimap to get the Minimap
    widget.
    '''

    def __init__(self, command_sink):
        # To send user commands to.
        self.command_sink = command_sink

        # The pre-HELLO size of the board.
        self.board_size = (1, 1)

        # one of 'wait', 'board', 'boom'
        # 'wait': waiting for the first board to be sent
        # 'board': ready to render a board
        # 'boom': ready to render a BOOM
        self.state = 'wait'

        # The first tile shown, in the top left of the screen.
        self.aperture_top_left = (-1, -1)

        # The most recent size the aperture used.
        self.cached_aperture_size = None

        # The tile of the map that's selected. In board coordinates - i.e.
        # not relative to focus.
        self.selected = (0, 0)

        # Currently no board.
        self.board = None

        # Map and Minimap.
        self.map = MinesweeperMapMinimap.Map(self)
        self.minimap = MinesweeperMapMinimap.MiniMap(self)

    def board_to_aperture(self, coord):
        '''Compute coord in aperture space from board space.'''
        cx, cy = coord
        tlx, tly = self.aperture_top_left

        return (cx - tlx, cy - tly)

    def aperture_to_board(self, coord):
        '''Compute coord in board space from aperture space.'''
        cx, cy = coord
        tlx, tly = self.aperture_top_left

        return (cx + tlx, cy + tly)

    def in_aperture(self, board_coord):
        aw, ah = self.cached_aperture_size
        ax, ay = self.board_to_aperture(board_coord)

        return 0 <= ax < aw and 0 <= ay < ah

    @property
    def aperture_selected(self):
        '''Selected tile relative to aperture.'''
        return self.board_to_aperture(self.selected)

    @property
    def show_whole_map(self):
        '''Determine if we're currently showing the whole map, or a window
        into it.'''
        aw, ah = self.cached_aperture_size
        bw, bh = self.board_size
        return bw <= aw and bh <= ah

    def resize_aperture(self, aperture_size):
        '''Resize the aperture to take advantage of the new size.'''
        assert len(aperture_size) == 2
        
        if aperture_size == self.cached_aperture_size:
            return

        # Update cache
        self.cached_aperture_size = aperture_size

        # Clamp selection to new aperture
        naw, nah = aperture_size
        sx, sy = self.selected
        tlx, tly = self.aperture_top_left
        sx = clamp(sx, tlx+1, tlx+naw-1)
        sy = clamp(sy, tly+1, tly+nah-1)
        self.selected = (sx, sy)

        # Redraw
        self.map._invalidate()
        self.minimap._invalidate()

    def move_selection(self, delta):
        '''Attempt to move the selection by (dx, dy), possibly moving the
        aperture. dx and dy may have magnitude greater than one.
        '''
        sx, sy = self.selected
        dsx, dsy = delta
        board_width, board_height = self.board_size

        # New sx and sy
        nx = clamp(sx+dsx, 0, board_width-1)
        ny = clamp(sy+dsy, 0, board_height-1)

        # Have we moved at all?
        if nx == sx and ny == sy:
            return

        # Move selection
        self.selected = (nx, ny)
        self.map._invalidate()
        self.minimap._invalidate() # TODO redundant?

        # Are we moving the aperture?
        if self.show_whole_map:
            # No, we're showing the whole map.
            return

        # We move the aperture when the selection is in or beyond the outside
        # border of the aperture. Example:
        # self.cached_aperture_size = (4, 4)
        # self.board_size = (10, 10)
        # self.aperture_top_left = (0, 2)
        # nx, ny = (0, 4)
        # new self.aperture_top_left = (-1, 2)
        # ---- -> #---
        # ----    #---
        # s---    #s--
        # ----    #---
        aw, ah = self.cached_aperture_size
        
        # If the aperture is too small to have tiles besides the border,
        # always have the aperture start at the selection.
        if aw < 3 or ah < 3:
            self.aperture_top_left = self.selected
            return


        # selection relative to aperture (0 = left, aw-1: right, etc.)
        ax, ay = self.aperture_selected

        tlx, tly = self.aperture_top_left

        # If selection is past border, move aperture.
        if ax <= 0:
            tlx = nx - 1
        elif ax >= aw-1:
            tlx = nx + 2 - aw
        
        if ay <= 0:
            tly = ny - 1
        elif ay >= ah-1:
            tly = ny + 2 - ah

        # Aperture might not have changed; that's okay.
        self.aperture_top_left = (tlx, tly)

    # Server communication stuff.
    def response(self, resp):
        '''Process a response from the server.'''

        if type(resp) == message.HelloResp:
            self.board_size = resp.size
            self.command_sink.command(message.LookCommand())
            self.map._invalidate()
        elif type(resp) == message.BoardResp:
            assert self.board_size == (resp.board.width, resp.board.height)
            self.board = resp.board
            self.state = 'board'
            self.map._invalidate()
        elif type(resp) == message.BoomResp:
            self.state = 'boom'
            self.map._invalidate()

    def _dig(self):
        '''Dig at the current selected tile, if it can be dug.'''
        assert self.state == 'board'

        tiletype = type(self.board[self.selected])
        if tiletype == board.Untouched:
            self.command_sink.command(message.DigCommand(self.selected))

    def _flag(self):
        assert self.state == 'board'
        tiletype = type(self.board[self.selected])
        if tiletype == board.Untouched:
            self.command_sink.command(message.FlagCommand(self.selected))
        elif tiletype == board.Flagged:
            self.command_sink.command(message.DeflagCommand(self.selected))

    # The widgets.
    class Map(urwid.Widget):
        _sizing = frozenset({'box'})

        def __init__(self, model):
            self.model = model

        def selectable(self):
            return self.model.state == 'board'

        def keypress(self, size, key):
            self.model.resize_aperture(size)

            if key.startswith('shift'):
                upper = True
                k = key[6:]
            else:
                upper = key.isupper()
                k = key.lower()

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

                dx, dy = delta
                if upper:
                    dx *= 10
                    dy *= 10

                self.model.move_selection((dx, dy))
                return # handled

            # Flagging and digging
            if k == 'enter' or k == '1':
                self.model._dig()
                return # handled
            elif k == "'" or k == '"' or k == '2' or k == 'f':
                self.model._flag()
                return # handled

            return key # not handled

        def mouse_event(self, size, event, button, col, row, focus):
            self.model.resize_aperture(size)
            
            if 'mouse press' in event:
                asx, asy = self.model.aperture_selected
                self.model.move_selection((col-asx, row-asy))

                if button == 1:
                    # Left click; dig
                    self.model._dig()
                if button == 2:
                    # Right click; flag
                    self.model._flag()

            return True # handled
        
        def get_cursor_coords(self, size):
            self.model.resize_aperture(size)
            
            return self.model.aperture_selected

        def render(self, size, focus=False):
            self.model.resize_aperture(size)

            if self.model.state == 'wait':
                result = urwid.SolidCanvas('#', *size)
                result = urwid.CompositeCanvas(result)
                result.fill_attr(Palette.GRAY)
                return result
            
            if self.model.state == 'boom':
                result = urwid.SolidCanvas('#', *size)
                result = urwid.CompositeCanvas(result)
                result.fill_attr(Palette.BOOM)
                return result

            if self.model.state == 'board':
                aw, ah = size
                result_strings = []
                result_attrs = []
                for ay in xrange(ah):
                    row = ''
                    row_attr = []
                    for ax in xrange(aw):
                        board_coord = self.model.aperture_to_board((ax, ay))

                        if self.model.board.in_bounds(board_coord):
                            tile = self.model.board[board_coord]
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
                        else:
                            row += '#'
                            row_attr.append((Palette.EDGE, 1))

                    result_strings.append(row)
                    result_attrs.append(row_attr)

                return urwid.TextCanvas(result_strings, result_attrs,
                        cursor=self.model.aperture_selected,
                        maxcol=aw,
                        check_width=True)
    
    class MiniMap(urwid.Widget):
        _sizing = frozenset({'box'})
        _selectable = False

        def __init__(self, model):
            self.model = model

        def render(self, size, focus=False):
            assert not focus
            
            if self.model.state == 'wait':
                result = urwid.SolidCanvas('#', *size)
                result = urwid.CompositeCanvas(result)
                result.fill_attr(Palette.GRAY)
                return result
            
            if self.model.state == 'boom':
                result = urwid.SolidCanvas('#', *size)
                result = urwid.CompositeCanvas(result)
                result.fill_attr(Palette.BOOM)
                return result

            mmw, mmh = size
            bw, bh = self.model.board_size
            
            x_scale = float(bw) / float(mmw)
            y_scale = float(bh) / float(mmh)

            result_strings = []
            result_attrs = []
            for y in xrange(mmh):
                row = ''
                row_attr = []
                for x in xrange(mmw):
                    row += ' '
                    if self.model.in_aperture((round(x * x_scale), round(y * y_scale))):
                        row_attr.append((Palette.BOOM, 1))
                    else:
                        row_attr.append((Palette.GRAY, 1))

                result_strings.append(row)
                result_attrs.append(row_attr)

            sx, sy = self.model.selected
            mmsx, mmsy = clamp(int(round(sx / x_scale)), 0, mmw-1), clamp(int(round(sy / y_scale)), 0, mmh-1)

            result_strings[mmsy] = result_strings[mmsy][:mmsx] + 'X' + result_strings[mmsy][mmsx+1:]

            return urwid.TextCanvas(result_strings, result_attrs,
                    maxcol=mmw,
                    check_width=True)

class Palette:
    '''Colors available to use.
    GRAY is just gray.
    BOOM is bold black on red.
    EDGE is blue on white.
    UNTOUCHED is light gray on white.
    FLAGGED is red on white.
    SELECTED is white on blue.
    DUG[0:9] are colors ranging from blue to red on black.
    '''
    GRAY = 'gray'
    BOOM = 'boom'
    EDGE = 'edge'
    UNTOUCHED = 'untouched'
    FLAGGED = 'flagged'
    SELECTED = 'selected'
    DUG = ['dug' + str(n) for n in xrange(9)]

PALETTE = [
        (Palette.GRAY, 'light gray', 'dark gray'),
        (Palette.BOOM, 'black,bold', 'dark red'),
        (Palette.EDGE, 'dark blue', 'white'),
        (Palette.UNTOUCHED, 'dark gray', 'white'),
        (Palette.FLAGGED, 'dark red,bold', 'white'),
        (Palette.SELECTED, 'white', 'dark blue'),
]
PALETTE += zip(Palette.DUG, 
        ['black'] * 8,
        ['', 'dark blue', 'dark green', 'yellow',
            'dark red', 'light red', 'light magenta', 'white'])

def handle_exit(key):
    if type(key) == str:
        if key.lower() in ('q', 'ctrl c', 'ctrl d'):
            raise urwid.ExitMainLoop()

HELP_MESSAGE = u'''Welcome to the gandyloo minesweeper interface!

Controls:
    - Movement can be done with:
        - WASD       (fps-style)
        - hjkl+yubn  (roguelike-style)
        - arrow keys (normal-style)

    - Press shift to move faster!

    - To dig:
        - Enter

    - To flag:
        - '
        - f

About:
    Author:  James Gilles
    License: MIT
'''

# Final setup
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="6.005 compatible minesweeper client.")
    parser.add_argument('--server', default='localhost', help='The server to connect to [default: localhost]')
    parser.add_argument('--port', default='4444', type=int, help='The port to connect to [default: 4444]')
    args = parser.parse_args()

    from minesweeper.connection import MinesweeperClient
    from twisted.internet import reactor
    from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

    relay = message.MessageRelay()

    model = MinesweeperMapMinimap(relay)

    client = MinesweeperClient(relay)

    point = TCP4ClientEndpoint(reactor, args.server, args.port)
    d = connectProtocol(point, client)

    relay.add_command_receiver(client)
    relay.add_response_receiver(model)

    minimap = urwid.LineBox(model.minimap, "Minimap")
    help_box = urwid.LineBox(urwid.Filler(urwid.Text(HELP_MESSAGE), 'top'), 'Help')
    mini_help_stack = urwid.Pile([('weight', .3, minimap), ('weight', .7, help_box)])

    main_map = urwid.LineBox(model.map, "Gandyloo")

    core_widget = urwid.Columns([('weight', .7, main_map), ('weight', .3, mini_help_stack)], box_columns=[0])

    loop = urwid.MainLoop(core_widget, PALETTE, unhandled_input=handle_exit)
    loop.screen.set_terminal_properties(colors=16)
    loop.event_loop = urwid.TwistedEventLoop(reactor)
    loop.run()
