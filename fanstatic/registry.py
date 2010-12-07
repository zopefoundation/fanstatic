import pkg_resources

ENTRY_POINT = 'fanstatic.libraries'

class LibraryRegistry(dict):
    def __init__(self, libraries):
        if libraries is None:
            return
        for library in libraries:
            self[library.name] = library

    def add(self, library):
        self[library.name] = library

def get_libraries_from_entry_points():
    libraries = []
    for entry_point in pkg_resources.iter_entry_points(ENTRY_POINT):
        libraries.append(entry_point.load())
    return libraries
    
library_registry = LibraryRegistry(get_libraries_from_entry_points())
