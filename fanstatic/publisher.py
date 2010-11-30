import webob
from paste.request import path_info_pop, path_info_split
from paste.fileapp import DirectoryApp, CACHE_CONTROL, EXPIRES
from paste.httpexceptions import HTTPNotFound

import fanstatic

class FilterHiddenDirectoryApp(DirectoryApp):
    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        for segment in path_info.split('/'):
            if segment.startswith('.'):
                return HTTPNotFound()(environ, start_response)
        return DirectoryApp.__call__(self, environ, start_response)

class Publisher(object):

    def __init__(self):
        self.directory_apps = {}
        for library in fanstatic.libraries():
            app = FilterHiddenDirectoryApp(library.path)
            self.directory_apps[library.name] = app

    def __call__(self, environ, start_response):
        # Pop the hash, if it exists.
        path_info = environ['PATH_INFO']
        if path_info.startswith('/:hash:'):
            path_info_pop(environ)
            # Overwrite the start_response callable with one that will
            # apply expiry headers for 20* responses.
            _start_response = start_response
            def start_response(status, headers, exc_info=None):
                # Only set the cache control for succesful requests
                # (200, 206).
                if status.startswith('20'):
                    expires = CACHE_CONTROL.apply(
                        headers, max_age=10*CACHE_CONTROL.ONE_YEAR)
                    EXPIRES.update(headers, delta=expires)
                return _start_response(status, headers, exc_info)

        # Pop first name, being library name.
        library_name = path_info_pop(environ)
        directory_app = self.directory_apps.get(library_name)
        if directory_app is None:
            return HTTPNotFound()(environ, start_response)
        return directory_app(environ, start_response)

class Delegator(object):

    def __init__(self, app, publisher_signature=fanstatic.DEFAULT_SIGNATURE):
        self.application = app
        self.publisher_signature = publisher_signature
        self.resource_publisher = Publisher()

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        trigger = '/%s/' % self.publisher_signature
        chunks = path_info.split(trigger, 1)
        if len(chunks) == 1:
            # The trigger is not in the URL at all, we delegate to the
            # original application.
            return self.application(environ, start_response)
        environ = environ.copy()
        environ['PATH_INFO'] = '/%s' % chunks[1]
        return self.resource_publisher(environ, start_response)

def make_publisher(app, global_config, **local_config):
    return Delegator(app, **local_config)

