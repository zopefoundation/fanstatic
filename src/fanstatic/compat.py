"""Python 2/3 compatibility module."""

import sys


if sys.version_info[0] < 3:  # PY2
    def iteritems(x): return x.iteritems()
    def iterkeys(x): return x.iterkeys()
    def itervalues(x): return x.itervalues()
    def dict_items(x): return x.items()
    def dict_keys(x): return x.keys()
    def dict_values(x): return x.values()
    def u(x): return unicode(x)  # noqa: F821 undefined name
    def as_bytestring(x): return x
    maxsize = sys.maxsize
    basestring = basestring  # noqa: F821 undefined name
else:
    def iteritems(x): return x.items()
    def iterkeys(x): return x.keys()
    def itervalues(x): return x.values()
    def dict_items(x): return list(x.items())
    def dict_keys(x): return list(x.keys())
    def dict_values(x): return list(x.values())
    def as_bytestring(x): return x.encode('utf-8')
    def u(x): return x
    maxsize = sys.maxsize
    basestring = str
