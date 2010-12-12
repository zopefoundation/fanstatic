from fanstatic import generate_code, Library, Resource

def test_generate_source():
    foo = Library('foo', '')
    i1 = Resource(foo, 'i1.js')
    i2 = Resource(foo, 'i2.js', depends=[i1])
    i3 = Resource(foo, 'i3.js', depends=[i2])
    i4 = Resource(foo, 'i4.js', depends=[i1])
    i5 = Resource(foo, 'i5.js', depends=[i4, i3])

    assert generate_code(i1=i1, i2=i2, i3=i3, i4=i4, i5=i5) == '''\
from fanstatic import Library, Resource

foo = Library('foo', '')

i1 = Resource(foo, 'i1.js')
i2 = Resource(foo, 'i2.js', depends=[i1])
i3 = Resource(foo, 'i3.js', depends=[i2])
i4 = Resource(foo, 'i4.js', depends=[i1])
i5 = Resource(foo, 'i5.js', depends=[i4, i3])'''

def test_generate_source_with_modes_and_rollup():
    foo = Library('foo', '')
    bar = Library('bar', '')
    j1 = Resource(foo, 'j1.js', debug='j1-debug.js')
    j2 = Resource(foo, 'j2.js', debug='j2-debug.js')
    giantj = Resource(foo, 'giantj.js', supersedes=[j1, j2],
                               debug='giantj-debug.js')
    non_inlinable = Resource(foo, 'j3.js', debug=Resource(bar,
                                                          'j4.js'))
    
    assert generate_code(j1=j1, j2=j2, giantj=giantj,
                         non_inlinable=non_inlinable) == '''\
from fanstatic import Library, Resource

bar = Library('bar', '')
foo = Library('foo', '')

j1 = Resource(foo, 'j1.js', debug='j1-debug.js')
j2 = Resource(foo, 'j2.js', debug='j2-debug.js')
giantj = Resource(foo, 'giantj.js', supersedes=[j1, j2], debug='giantj-debug.js')
non_inlinable = Resource(foo, 'j3.js', debug=Resource(bar, 'j4.js'))'''

def test_generate_source_control_name():
    foo = Library('foo', '')
    i1 = Resource(foo, 'i1.js')
    i2 = Resource(foo, 'i2.js', depends=[i1])

    assert generate_code(hoi=i1) == '''\
from fanstatic import Library, Resource

foo = Library('foo', '')

hoi = Resource(foo, 'i1.js')'''

    assert generate_code(hoi=i1, i2=i2) == '''\
from fanstatic import Library, Resource

foo = Library('foo', '')

hoi = Resource(foo, 'i1.js')
i2 = Resource(foo, 'i2.js', depends=[hoi])'''
