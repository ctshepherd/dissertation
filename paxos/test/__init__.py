from twisted.trial import unittest
from paxos import util


def enable_debug(func, level=1):
    """Decorator to enable debug for a specific test method"""
    def f(*args):
        saved_dbg = util.DEBUG
        util.DEBUG = level
        func(*args)
        util.DEBUG = saved_dbg
    return f


class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.debug = kwargs.get('debug', False)
        super(TestCase, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        """Override the standard Twisted TestCase to silence debug output"""
        saved_dbg = None
        if not self.debug:
            saved_dbg = util.DEBUG
            util.DEBUG = False
        super(TestCase, self).run(*args, **kwargs)
        if saved_dbg is not None:
            util.DEBUG = saved_dbg
