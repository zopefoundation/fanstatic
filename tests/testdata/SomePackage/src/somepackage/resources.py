from fanstatic import Library, Resource


bar = Library('bar', 'resources')

style = Resource(bar, 'style.css', minifier='dummy')
