from fanstatic import Library
from fanstatic import Resource


bar = Library('bar', 'resources')

style = Resource(bar, 'style.css', minifier='dummy')
