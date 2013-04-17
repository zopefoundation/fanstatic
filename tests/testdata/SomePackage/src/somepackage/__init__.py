from fanstatic import Library, Resource, Minifier, compat


class DummyMinifier(Minifier):

    name = 'dummy'
    available = True
    target_extension = '.min.css'

    def process(self, source, target):
        with open(target, 'wb') as output:
            output.write(compat.as_bytestring('dummy'))

DUMMY = DummyMinifier()
