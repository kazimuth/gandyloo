from twisted.internet.protocol import Protocol
from gandyloo import parse

class MinesweeperClient(Protocol):
    '''Represents a connection to a server using twisted's Protocol framework.
    Created with an event sink, where parsed events (subclasses of
    gandyloo.message.Response) are fired. Sink should have a method
    self.response(resp).
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
            except parse.NotReadyError:
                return # Haven't received enough data yet
            self.hello_received = True
            self.size = resp.size
            self.event_sink.response(resp)
        try:
            while True:
                resp, self.buffer = parse.parse_start(self.buffer, self.size)
                self.event_sink.response(resp)
        except parse.NotReadyError:
            return

    def command(self, command):
        self.transport.write(command.render())

    def clientConnectionLost(self, connection, reason):
        self.event_sink.response(message.CloseResp(reason))


