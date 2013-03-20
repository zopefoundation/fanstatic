import os.path

mtime = os.path.getmtime


class Compiler(object):

    name = NotImplemented
    source_extension = NotImplemented

    def __call__(self, resource, force=False):
        source = self.source_path(resource)
        target = self.target_path(resource)
        if force or self.should_process(source, target):
            self.process(source, target)

    @property
    def available(self):
        return False  # Override in subclass

    def process(self, source, target):
        pass  # Override in subclass

    def should_process(self, source, target):
        """
        Determine whether to process the resource, based on the mtime of the
        target and source.
        """
        return not os.path.isfile(target) or mtime(source) > mtime(target)

    def source_path(self, resource):
        if resource.source:
            return resource.fullpath(resource.source)
        return os.path.splitext(resource.fullpath())[0] + self.source_extension

    def target_path(self, resource):
        return resource.fullpath()


class Minifier(Compiler):

    target_extension = NotImplemented

    def source_path(self, resource):
        return resource.fullpath()

    def target_path(self, resource):
        if resource.minified:
            return resource.fullpath(resource.minified)
        return resource.fullpath(
            os.path.splitext(resource.relpath)[0] + self.target_extension)


class NullCompiler(Compiler):
    """Null object (no-op compiler), that will be used when compiler/minifier
    on a Resource is set to None.
    """

    name = None

    def source_path(self, resource):
        return None

    def target_path(self, resource):
        return None
