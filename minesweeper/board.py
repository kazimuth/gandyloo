from array import array

class Board:
    '''Class representing a (client-side) minesweeper board.
    Access individual items like so:
        board[x, y]
        board[x, y] = 0
    Out-of-bounds accesses will raise an exception.
    '''
    # _tiles is a width*height byte array.
    # _tiles[x + y*width] represents the tile at (x, y).
    # A _tiles entry of 0-8 represents a Dug tile with
    # that many surrounding mines.
    # A _tiles entry of 9 represents an Untouched tile;
    # A _tiles entry of 10 represents a Flagged tile.

    def __init__(self, width, height):
        '''Create a new, entirely untouched board.'''
        assert width > 0 and height > 0

        self.width = width
        self.height = height
        self._tiles = array('B', [9]*(width*height))

    def __getitem__(self, idx):
        x, y = idx
        assert self.in_bounds(x, y)

        tile = self._tiles[x + y*self.width]
        if 0 <= tile <= 8:
            return Dug(tile)
        if tile == 9:
            return Untouched()
        if tile == 10:
            return Flagged()

    def __setitem__(self, idx, val):
        x, y = idx
        assert self.in_bounds(x, y)

        if isinstance(val, Dug):
            self._tiles[x + y*self.width] = val.surrounding
        elif isinstance(val, Untouched):
            self._tiles[x + y*self.width] = 9
        elif isinstance(val, Flagged):
            self._tiles[x + y*self.width] = 10

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

class Tile:
    pass

class Dug(Tile):
    '''A dug tile. tile.surrounding represents the number of surrounding mines.'''
    def __init__(self, surrounding):
        self.surrounding = surrounding

    def __eq__(self, other):
        return isinstance(other, Dug) and other.surrounding == self.surrounding

class Untouched(Tile):
    '''An untouched tile.'''
    def __eq__(self, other):
        return isinstance(other, Untouched)

class Flagged(Tile):
    '''A flagged tile.'''
    def __eq__(self, other):
        return isinstance(other, Flagged)

