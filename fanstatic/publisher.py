import webob
import webob.dec
import webob.exc
import time
from paste.fileapp import DirectoryApp

import fanstatic

MINUTE_IN_SECONDS = 60
HOUR_IN_SECONDS = MINUTE_IN_SECONDS * 60
DAY_IN_SECONDS = HOUR_IN_SECONDS * 24
YEAR_IN_SECONDS = DAY_IN_SECONDS * 365

# arbitrarily define forever as 10 years in the future
FOREVER = YEAR_IN_SECONDS * 10

class DirectoryPublisher(DirectoryApp):
    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        for segment in path_info.split('/'):
            if segment.startswith('.'):
                return HTTPNotFound()(environ, start_response)
        return DirectoryApp.__call__(self, environ, start_response)
    
class Publisher(object):
    def __init__(self, libraries):
        directory_publishers = {}
        for library in libraries:
            directory_publishers[library.name] = DirectoryPublisher(
                library.path)
        self.directory_publishers = directory_publishers

    @webob.dec.wsgify
    def __call__(self, request):
        library_name = request.path_info_pop()
        # don't allow requests on just publisher
        if library_name == '':
            raise webob.exc.HTTPForbidden()
        # pop hash if it's there
        potential_hash = request.path_info_peek()
        if potential_hash is not None and potential_hash.startswith(':hash:'):
            request.path_info_pop()
            need_caching = True
        else:
            need_caching = False
        directory_publisher = self.directory_publishers.get(library_name)
        # unknown library
        if directory_publisher is None:
            raise webob.exc.HTTPNotFound()
        # we found the library, but we are not looking for a resource in it
        if request.path_info == '':
            raise webob.exc.HTTPForbidden()
        # now delegate publishing to the directory publisher
        response = request.copy().get_response(directory_publisher)
        # set caching when needed and for successful responses
        if need_caching and response.status.startswith('20'):
            response.cache_control.max_age = FOREVER
            response.expires = time.time() + FOREVER
        return response

class Delegator(object):
    def __init__(self, app, publisher,
                 publisher_signature=fanstatic.DEFAULT_SIGNATURE):
        self.app = app
        self.publisher = publisher
        self.trigger = '/%s/' % publisher_signature
        
    @webob.dec.wsgify
    def __call__(self, request):
        chunks = request.path_info.split(self.trigger, 1)
        if len(chunks) == 1:
            # the trigger segment is not in the URL, so we delegate
            # to the original application
            return request.get_response(self.app)
        # the trigger is in there, so let whatever is behind the
        # trigger be handled by the publisher
        request = request.copy()
        request.path_info = chunks[1]
        return request.get_response(self.publisher)

# XXX needs to be adjusted so it gets publisher as argument
def make_publisher(app, global_config, **local_config):
    return Delegator(app, **local_config)

