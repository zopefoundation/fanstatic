class NullCompiler(object):
    """Null object (no-op compiler), that will be used when compiler/minifier
    on a Resource is set to None.
    """

    def __call__(self, resource):
        pass
