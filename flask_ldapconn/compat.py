from __future__ import print_function
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    unicode_ = str
    bytes_ = bytes

    def to_bytes(s):
        if isinstance(s, str):
            return s.encode()
        raise NotImplementedError()
else:
    unicode_ = unicode
    bytes_ = str

    def to_bytes(s):
        if isinstance(s, str):
            return s
        raise NotImplementedError()