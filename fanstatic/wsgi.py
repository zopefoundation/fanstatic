from paste.util.converters import asbool

import fanstatic
from fanstatic import Inject, Delegator, Publisher, library_registry

def Fanstatic(app,
              publisher_signature=fanstatic.DEFAULT_SIGNATURE,
              **config):
    """Fanstatic WSGI framework component.

    :param app: The WSGI app to wrap with Fanstatic.
    
    :param publisher_signature: Optional argument to define the
      signature of the publisher in a URL. The default is ``fanstatic``.
      
    :param ``**config``: Optional keyword arguments. These are
      those passed to :py:class:`NeededInclusions`.
    """
    # wrap the app inside the inject middleware, inside the publisher
    # middleware.
    return Delegator(Inject(app, **config),
                     Publisher(library_registry.values()),
                     publisher_signature=publisher_signature)

def make_fanstatic(app, global_config, **local_config):
    devmode = local_config.get('devmode')
    if devmode is not None:
        local_config['devmode'] = asbool(devmode)
    rollup = local_config.get('rollup')
    if rollup is not None:
        local_config['rollup'] = asbool(rollup)
    bottom = local_config.get('bottom')
    if bottom is not None:
        local_config['bottom'] = asbool(bottom)
    return Fanstatic(app, **local_config)
