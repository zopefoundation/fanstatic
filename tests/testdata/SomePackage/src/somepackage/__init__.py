from fanstatic import Library, Resource, Minifier


class DummyMinifier(Minifier):

    name = 'dummy'
    available = True
    target_extension = '.min.css'

    def process(self, source, target):
        with open(target, 'wb') as output:
            output.write('dummy')

DUMMY = DummyMinifier()
