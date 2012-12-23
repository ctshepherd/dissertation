"""Utility module.

Various utility functions, at the moment just title and dbprint
"""

DEBUG = 1


def title(s):
    """capitalizes only first character of a string"""
    if len(s) < 2:
        return s.capitalize()
    return s[0].capitalize() + s[1:]


def cb(f, args=()):
    def g(r):
        f(*args)
    return g


def dbprint(s, level=5):
    if DEBUG and level >= DEBUG:
        print s


class PaxosException(Exception):
    """Superclass for all exceptions raised by the Paxos module."""
    pass
