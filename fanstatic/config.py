from paste.util.converters import asbool

from fanstatic import DEBUG, MINIFIED, compat

BOOL_CONFIG = set(['versioning', 'recompute_hashes', DEBUG, MINIFIED,
                   'bottom', 'force_bottom', 'bundle', 'rollup',
                   'versioning_use_md5'])


def convert_config(config):
    result = {}
    for key, value in compat.iteritems(config):
        if key in BOOL_CONFIG:
            result[key] = asbool(value)
        else:
            result[key] = value
    return result
