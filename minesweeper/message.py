import re

class MessageRelay(object):
    '''A class to pass around commands to the server and responses from
    the server.
    Call command() to send a command to all of its command receivers,
    and response() to send a response to all of its response receivers.
    '''

    def __init__(self):
        self.command_receivers = []
        self.response_receivers = []

    def add_command_receiver(self, receiver):
        self.command_receivers.append(receiver)

    def add_response_receiver(self, receiver):
        self.response_receivers.append(receiver)

    def command(self, command):
        for receiver in self.command_receivers:
            receiver.command(command)

    def response(self, response):
        for receiver in self.response_receivers:
            receiver.response(response)

class Command(object):
    '''A command to send to the minecraft server.
    Must have a method render() to turn into a minesweeper-compatible
    command message.
    '''

    def render(self):
        pass

class LookCommand(Command):
    def render(self):
        return 'look\n'

class HelpCommand(Command):
    def render(self):
        return 'help\n'

class ByeCommand(Command):
    def render(self):
        return 'bye\n'

class DigCommand(Command):
    def __init__(self, target):
        assert len(target) == 2
        self.target = target

    def render(self):
        return 'dig {} {}\n'.format(*self.target)

class FlagCommand(Command):
    def __init__(self, target):
        assert len(target) == 2
        self.target = target

    def render(self):
        return 'flag {} {}\n'.format(*self.target)

class DeflagCommand(Command):
    def __init__(self, target):
        assert len(target) == 2
        self.target = target

    def render(self):
        return 'deflag {} {}\n'.format(*self.target)


class Response(object):
    '''A parsed response from a minesweeper server.

    Attributes:
        contents: if this response is a HELP, the textual contents of this response.
        board:    if this response is a BOARD, a minesweeper.board.BoardResp
                  storing its contents.
        players:  if this response is a HELLO, the number of players given
                  by the HELLO.
        size:     if this response is a HELLO, the (width, height) of the
                  map given by the HELLO.
    '''

class HelpResp(Response):
    def __init__(self, contents):
        self.contents = contents

class BoomResp(Response):
    pass

class HelloResp(Response):
    def __init__(self, size, players):
        self.size = size
        self.players = players

class BoardResp(Response):
    def __init__(self, board):
        self.board = board

class CloseResp(Response):
    '''Represents the connection from the server closing.'''
    def __init__(self, reason):
        self.reason = reason

