from twisted.internet.protocol import Protocol
from minesweeper import parse

class MinesweeperClient(Protocol):
    '''Represents a connection to a server using twisted's Protocol framework.
    Created with an event sink, where parsed events (subclasses of
    minesweeper.parse.Response) are fired. Sink should have a method
    self.fire(event).
    '''

    def __init__(self, event_sink):
        self.buffer = ""
        self.hello_received = False
        self.size = None
        self.event_sink = event_sink

    def dataReceived(self, data):
        self.buffer += data

        if not self.hello_received:
            try:
                resp, self.buffer = parse.parse_start(self.buffer, first=True)
                self.size = resp.size
                event_sink.fire(resp)
            except parse.NotReadyError:
                return # Haven't received enough data yet

        try:
            while True:
                resp, self.buffer = parse.parse_start(self.buffer, self.size)
                event_sink.fire(resp)
        except parse.NotReadyError:
            return

    def clientConnectionLost(self, connection, reason):
        event_sink.fire(parse.CloseResp(reason))

