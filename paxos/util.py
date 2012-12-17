"""Utility module.

Various utility functions, at the moment just title and dbprint
"""

DEBUG = 1


def title(s):
    """capitalizes only first character of a string"""
    if len(s) < 2:
        return s.capitalize()
    return s[0].capitalize() + s[1:]


def dbprint(s, level=5):
    if DEBUG and level >= DEBUG:
        print s
