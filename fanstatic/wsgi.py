import fanstatic

class Fanstatic():
    pass

def make_fanstatic(app, global_config, **local_config):
    # Wrap app inside the inject middleware, inside the publisher
    # middleware for the integrated solution.
    return fanstatic.make_publisher(
        fanstatic.make_inject(app, global_conf, **local_config),
        global_config, **local_config)

