from gandyloo import message, board
import pytest

def test_rendering():
    assert message.LookCommand().render() == 'look\n'
    assert message.HelpCommand().render() == 'help\n'
    assert message.ByeCommand().render()  == 'bye\n'
    assert message.DigCommand((10, 20)).render() == 'dig 10 20\n'
    assert message.FlagCommand((50, 50020)).render() == 'flag 50 50020\n'
    assert message.DeflagCommand((0, 0)).render() == 'deflag 0 0\n'

def test_relay():
    class ResponseReceiver:
        def __init__(self):
            self.received = []

        def response(self, resp):
            self.received.append(resp)

    class CommandReceiver:
        def __init__(self):
            self.received = []

        def command(self, command):
            self.received.append(command)

    r = message.MessageRelay()

    resps = ResponseReceiver()
    coms = CommandReceiver()

    r.add_command_receiver(coms)
    r.add_response_receiver(resps)

    d = message.DigCommand((0,0))
    b = message.BoardResp(board.Board(10, 10))
    hc = message.HelpCommand()
    hr = message.HelpResp('RTFM\r\n')

    r.command(d)
    r.response(b)
    r.command(hc)
    r.response(hr)

    assert coms.received == [d, hc]
    assert resps.received == [b, hr]

    

    

