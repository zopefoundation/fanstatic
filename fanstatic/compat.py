"""Python 2/3 compatibility module."""

import sys


if sys.version_info[0] < 3:
    iteritems = lambda x: x.iteritems()
    iterkeys = lambda x: x.iterkeys()
    itervalues = lambda x: x.itervalues()
    dict_items = lambda x: x.items()
    dict_keys = lambda x: x.keys()
    dict_values = lambda x: x.values()
    u = lambda x: unicode(x)
    as_bytestring = lambda x: x
    maxsize = sys.maxint
    basestring = basestring
else:
    iteritems = lambda x: x.items()
    iterkeys = lambda x: x.keys()
    itervalues = lambda x: x.values()
    dict_items = lambda x: list(x.items())
    dict_keys = lambda x: list(x.keys())
    dict_values = lambda x: list(x.values())
    as_bytestring = lambda x: x.encode('utf-8')
    u = lambda x: x
    maxsize = sys.maxsize
    basestring = str
