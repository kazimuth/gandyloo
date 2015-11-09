from minesweeper import message
import pytest

def test_rendering():
    assert message.LookCommand().render() == 'look\n'
    assert message.HelpCommand().render() == 'help\n'
    assert message.ByeCommand().render()  == 'bye\n'
    assert message.DigCommand((10, 20)).render() == 'dig 10 20\n'
    assert message.FlagCommand((50, 50020)).render() == 'flag 50 50020\n'
    assert message.DeflagCommand((0, 0)).render() == 'deflag 0 0\n'
