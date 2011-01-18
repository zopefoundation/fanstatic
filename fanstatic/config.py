from paste.util.converters import asbool
from fanstatic import DEBUG, MINIFIED

BOOL_CONFIG = set(['versioning', 'recompute_hashes', DEBUG, MINIFIED,
                   'bottom', 'force_bottom', 'rollup'])

def convert_config(config):
    result = {}
    for key, value in config.items():
        if key in BOOL_CONFIG:
            result[key] = asbool(value)
        else:
            result[key] = value
    return result
