import pkg_resources

ENTRY_POINT = 'fanstatic.libraries'

class LibraryRegistry(dict):
    """A dictionary-like registry of libraries.

    This is a dictionary that mains libraries. A value is
    a :py:class:`Library` instance, and a key is its
    library ``name``.

    Normally there is only a single global LibraryRegistry,
    the ``library_registry`` instance.

    :param libraries: a sequence of libraries
    """    
    def __init__(self, libraries):
        if libraries is None:
            return
        for library in libraries:
            self[library.name] = library

    def add(self, library):
        """Add a Library instance to the registry.

        :param add: add a library to the registry.
        """
        self[library.name] = library

def get_libraries_from_entry_points():
    libraries = []
    for entry_point in pkg_resources.iter_entry_points(ENTRY_POINT):
        libraries.append(entry_point.load())
    return libraries
    
library_registry = LibraryRegistry(get_libraries_from_entry_points())
'''The global :py:class:`LibraryRegistry`.

It gets filled with the libraries registered using the fanstatic entry point.

You can also add libraries to it later.
'''
