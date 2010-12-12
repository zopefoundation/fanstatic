from fanstatic.config import convert_config
import fanstatic
from fanstatic import Injector, Delegator, Publisher, get_library_registry

def Fanstatic(app,
              publisher_signature=fanstatic.DEFAULT_SIGNATURE,
              **config):
    """Fanstatic WSGI framework component.

    :param app: The WSGI app to wrap with Fanstatic.

    :param publisher_signature: Optional argument to define the
      signature of the publisher in a URL. The default is ``fanstatic``.

    :param ``**config``: Optional keyword arguments. These are
      passed to :py:class:`NeededInclusions` when it is constructed.
    """
    # Wrap the app inside the injector middleware, inside the
    # delegator middleware.
    injector = Injector(
        app,
        publisher_signature=publisher_signature,
        **config)

    publisher = Publisher(get_library_registry())

    return Delegator(
        injector,
        publisher,
        publisher_signature=publisher_signature)

def make_fanstatic(app, global_config, **local_config):
    local_config = convert_config(local_config)
    return Fanstatic(app, **local_config)
