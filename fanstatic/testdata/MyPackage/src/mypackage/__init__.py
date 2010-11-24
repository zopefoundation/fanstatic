from fanstatic import Library, ResourceInclusion

foo = Library('foo', 'resources')

style = ResourceInclusion(foo, 'style.css')
