import threading

import pkg_resources

from fanstatic.compiler import NullCompiler


prepare_lock = threading.Lock()


class Registry(dict):

    ENTRY_POINT = NotImplemented

    def __init__(self, items=()):
        for item in items:
            self.add(item)

    def add(self, item):
        self[item.name] = item

    def load_items_from_entry_points(self):
        for entry_point in pkg_resources.iter_entry_points(self.ENTRY_POINT):
            self.add(self.make_item_from_entry_point(entry_point))

    def make_item_from_entry_point(self, entry_point):
        return entry_point.load()

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is not None:
            return cls._instance
        cls._instance = cls()
        cls._instance.load_items_from_entry_points()
        return cls._instance


class LibraryRegistry(Registry):
    """A dictionary-like registry of libraries.

    This is a dictionary that maintains libraries. A value is a
    :py:class:`Library` instance, and a key is its library ``name``.

    Normally there is only a single global LibraryRegistry,
    obtained by calling ``get_library_registry()``.

    :param libraries: a sequence of libraries
    """

    ENTRY_POINT = 'fanstatic.libraries'

    prepared = False

    def prepare(self):
        if self.prepared:
            return
        prepare_lock.acquire()
        try:
            if self.prepared:
                return
            for library in self.values():
                library.init_library_nr()
            for library in sorted(self.values(), key=lambda l_: l_.library_nr):
                for asset in library.known_assets:
                    asset.init_dependency_nr()
            self.prepared = True
        finally:
            prepare_lock.release()

    def __setitem__(self, key, value):
        if self.prepared:
            raise ValueError('Registry initialized.')
        super().__setitem__(key, value)

    def clear(self):
        super().clear()
        self.prepared = False

    def make_item_from_entry_point(self, entry_point):
        item = super().make_item_from_entry_point(
            entry_point)
        if not entry_point.dist.parsed_version.is_devrelease:
            item.version = entry_point.dist.version  # pragma: no cover
        return item


# BBB
"""Get the global :py:class:`LibraryRegistry`.

It gets filled with the libraries registered using the fanstatic
entry point.

You can also add libraries to it later.
"""
get_library_registry = LibraryRegistry.instance


class CompilerRegistry(Registry):

    ENTRY_POINT = 'fanstatic.compilers'

    def __init__(self, items=()):
        super().__init__(items)
        self.add(NullCompiler())


class MinifierRegistry(Registry):

    ENTRY_POINT = 'fanstatic.minifiers'

    def __init__(self, items=()):
        super().__init__(items)
        self.add(NullCompiler())


class InjectorRegistry(Registry):

    ENTRY_POINT = 'fanstatic.injectors'
