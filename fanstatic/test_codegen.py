from fanstatic import generate_code, Library, Resource


def test_generate_source():
    foo = Library('foo', '')
    i1 = Resource(foo, 'i1.js')
    i2 = Resource(foo, 'i2.js', depends=[i1])
    i3 = Resource(foo, 'i3.js', depends=[i2])
    i5 = Resource(foo, 'i5.js', depends=[i3])

    assert generate_code(i1=i1, i2=i2, i3=i3, i5=i5) == '''\
from fanstatic import Library, Resource

# This code is auto-generated and not PEP8 compliant

foo = Library('foo', '')

i1 = Resource(foo, 'i1.js')
i2 = Resource(foo, 'i2.js', depends=[i1])
i3 = Resource(foo, 'i3.js', depends=[i2])
i5 = Resource(foo, 'i5.js', depends=[i3])''' 

def test_generate_source_control_name():
    foo = Library('foo', '')
    i1 = Resource(foo, 'i1.js')
    i2 = Resource(foo, 'i2.js', depends=[i1])

    assert generate_code(hoi=i1) == '''\
from fanstatic import Library, Resource

# This code is auto-generated and not PEP8 compliant

foo = Library('foo', '')

hoi = Resource(foo, 'i1.js')'''

    assert generate_code(hoi=i1, i2=i2) == '''\
from fanstatic import Library, Resource

# This code is auto-generated and not PEP8 compliant

foo = Library('foo', '')

hoi = Resource(foo, 'i1.js')
i2 = Resource(foo, 'i2.js', depends=[hoi])'''
