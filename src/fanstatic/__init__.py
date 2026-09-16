from fanstatic.compiler import Compiler
from fanstatic.compiler import Minifier
from fanstatic.core import BUNDLE_PREFIX
from fanstatic.core import DEBUG
from fanstatic.core import DEFAULT_SIGNATURE
from fanstatic.core import MINIFIED
from fanstatic.core import NEEDED
from fanstatic.core import VERSION_PREFIX
from fanstatic.core import ConfigurationError
from fanstatic.core import Group
from fanstatic.core import GroupResource
from fanstatic.core import Library
from fanstatic.core import LibraryDependencyCycleError
from fanstatic.core import NeededResources
from fanstatic.core import Resource
from fanstatic.core import Slot
from fanstatic.core import SlotError
from fanstatic.core import UnknownResourceError
from fanstatic.core import UnknownResourceExtension  # BBB
from fanstatic.core import UnknownResourceExtensionError
from fanstatic.core import clear_needed
from fanstatic.core import del_needed
from fanstatic.core import get_needed
from fanstatic.core import init_needed
from fanstatic.core import register_inclusion_renderer
from fanstatic.core import set_auto_register_library
from fanstatic.core import set_resource_file_existence_checking
from fanstatic.inclusion import Inclusion
from fanstatic.inclusion import bundle_resources
from fanstatic.inclusion import sort_resources
from fanstatic.injector import Injector
from fanstatic.injector import make_injector
from fanstatic.publisher import Delegator
from fanstatic.publisher import LibraryPublisher
from fanstatic.publisher import Publisher
from fanstatic.publisher import make_publisher
from fanstatic.registry import CompilerRegistry
from fanstatic.registry import LibraryRegistry
from fanstatic.registry import MinifierRegistry
from fanstatic.registry import get_library_registry
from fanstatic.wsgi import Fanstatic
from fanstatic.wsgi import Serf
from fanstatic.wsgi import make_fanstatic
from fanstatic.wsgi import make_serf


# sdist_compile is resolved lazily by __getattr__ below, so it is not part of
# the module namespace that ``import *`` would pick up by itself.
__all__ = [name for name in globals() if not name.startswith('_')]
__all__.append('sdist_compile')


def __getattr__(name):
    # Imported lazily, because it is only useful from a setup.py and we do
    # not want importing fanstatic to import setuptools.
    if name == 'sdist_compile':
        try:
            from fanstatic.sdist import sdist_compile
        except ImportError as e:
            # __getattr__ must raise AttributeError, otherwise hasattr() and
            # getattr() with a default propagate this instead of reporting a
            # missing attribute.
            raise AttributeError(
                'sdist_compile requires setuptools to be installed') from e
        return sdist_compile
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def __dir__():
    return sorted([*globals(), 'sdist_compile'])
