"""
The package that contains a module for unit testing.
"""

from __future__ import unicode_literals

from builtins import str


def _bytes(obj):
    """
    Convert str in complex object to bytes.

    :param object obj: the object includes str.
    :return: return a new object includes converted bytes objects.
    :rtype: object
    """

    def _b(s):
        if isinstance(s, str):
            return s.encode()
        else:
            return s

    if isinstance(obj, dict):
        t = {}
        for k, v in obj.items():
            if isinstance(k, str):
                k = _b(k)
            t[k] = _bytes(v)
        return t

    elif isinstance(obj, list):
        t = []
        for e in obj:
            t.append(_bytes(e))
        return t

    elif isinstance(obj, str):
        return _b(obj)

    else:
        return obj
