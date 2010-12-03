from fanstatic import generate_code, Library, ResourceInclusion

def test_generate_source():
    foo = Library('foo', '')
    i1 = ResourceInclusion(foo, 'i1.js')
    i2 = ResourceInclusion(foo, 'i2.js', depends=[i1])
    i3 = ResourceInclusion(foo, 'i3.js', depends=[i2])
    i4 = ResourceInclusion(foo, 'i4.js', depends=[i1])
    i5 = ResourceInclusion(foo, 'i5.js', depends=[i4, i3])

    assert generate_code(i1=i1, i2=i2, i3=i3, i4=i4, i5=i5) == '''\
from fanstatic import Library, ResourceInclusion

foo = Library('foo', '')

i1 = ResourceInclusion(foo, 'i1.js')
i2 = ResourceInclusion(foo, 'i2.js', depends=[i1])
i3 = ResourceInclusion(foo, 'i3.js', depends=[i2])
i4 = ResourceInclusion(foo, 'i4.js', depends=[i1])
i5 = ResourceInclusion(foo, 'i5.js', depends=[i4, i3])'''

def test_generate_source_with_modes_and_rollup():
    foo = Library('foo', '')
    j1 = ResourceInclusion(foo, 'j1.js', debug='j1-debug.js')
    j2 = ResourceInclusion(foo, 'j2.js', debug='j2-debug.js')
    giantj = ResourceInclusion(foo, 'giantj.js', supersedes=[j1, j2],
                               debug='giantj-debug.js')

    assert generate_code(j1=j1, j2=j2, giantj=giantj) == '''\
from fanstatic import Library, ResourceInclusion

foo = Library('foo', '')

j1 = ResourceInclusion(foo, 'j1.js', debug='j1-debug.js')
j2 = ResourceInclusion(foo, 'j2.js', debug='j2-debug.js')
giantj = ResourceInclusion(foo, 'giantj.js', supersedes=[j1, j2], debug='giantj-debug.js')'''

def test_generate_source_control_name():
    foo = Library('foo', '')
    i1 = ResourceInclusion(foo, 'i1.js')
    i2 = ResourceInclusion(foo, 'i2.js', depends=[i1])
    i3 = ResourceInclusion(foo, 'i3.js', depends=[i2])
    i4 = ResourceInclusion(foo, 'i4.js', depends=[i1])
    i5 = ResourceInclusion(foo, 'i5.js', depends=[i4, i3])

    assert generate_code(hoi=i1) == '''\
from fanstatic import Library, ResourceInclusion

foo = Library('foo', '')

hoi = ResourceInclusion(foo, 'i1.js')'''

    assert generate_code(hoi=i1, i2=i2) == '''\
from fanstatic import Library, ResourceInclusion

foo = Library('foo', '')

hoi = ResourceInclusion(foo, 'i1.js')
i2 = ResourceInclusion(foo, 'i2.js', depends=[hoi])'''
