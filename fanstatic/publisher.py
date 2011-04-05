import os
import fnmatch
import webob
import webob.dec
import webob.exc
import time
import os.path
from paste.fileapp import DirectoryApp, FileApp, DataApp
from paste.httpheaders import CACHE_CONTROL

import fanstatic

MINUTE_IN_SECONDS = 60
HOUR_IN_SECONDS = MINUTE_IN_SECONDS * 60
DAY_IN_SECONDS = HOUR_IN_SECONDS * 24
YEAR_IN_SECONDS = DAY_IN_SECONDS * 365

# arbitrarily define forever as 10 years in the future
FOREVER = YEAR_IN_SECONDS * 10

def check_ignore(ignores, filename):
    for ignore in ignores:
        if fnmatch.filter(filename.split('/'), ignore):
            raise webob.exc.HTTPNotFound()


class BundleApp(FileApp):
    def __init__(self, rootpath, bundlename, ignores):
        # Let FileApp determine content_type and encoding based on bundlename.
        FileApp.__init__(self, bundlename)

        self.filenames = []
        # Check for ignores and rogue paths.
        for filename in bundlename.split(';'):
            check_ignore(ignores, filename)
            fullpath = os.path.join(rootpath, filename)
            if not os.path.normpath(fullpath).startswith(rootpath):
                # Raising forbidden here would expose private information.
                raise webob.exc.HTTPNotFound()
            if not os.path.exists(fullpath):
                raise webob.exc.HTTPNotFound()
            self.filenames.append(fullpath)

    # XXX see the fileapp/dataapp for returning a filewrapper/fileiter / 206
    def update(self, force=False):
        mtime = max([os.stat(fn).st_mtime for fn in self.filenames])
        if not force and mtime == self.last_modified:
            return
        self.last_modified = mtime

        contents = []
        for filename in self.filenames:
            fh = open(filename,"rb")
            contents.append(fh.read())
            fh.close()
        self.set_content('\n'.join(contents), mtime)

    def get(self, environ, start_response):
        if 'max-age=0' in CACHE_CONTROL(environ).lower():
            self.update(force=True) # RFC 2616 13.2.6
        else:
            self.update()
        return DataApp.get(self, environ, start_response)

class DirectoryPublisher(DirectoryApp):
    """Fanstatic directory publisher WSGI application.

    This WSGI application serves a directory of static resources to
    the web.

    This WSGI component is used automatically by the
    :py:func:`Fanstatic` WSGI framework component, but can also be
    used independently if you need more control.

    :param path: The path to the library's directory on the filesystem.

    :param ignores: A list of globs to match the requests against. If
      we have a match, the request will not be served.
    """
    def __init__(self, path, ignores):
        self.ignores = ignores
        super(DirectoryPublisher, self).__init__(path)

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        check_ignore(self.ignores, path_info)

        # Copied from DirectoryApp:
        app = self.cached_apps.get(path_info)
        if app is None:
            path = os.path.join(self.path, path_info.lstrip('/'))
            if not os.path.normpath(path).startswith(self.path):
                raise webob.exc.HTTPForbidden()
            elif fanstatic.BUNDLE_PREFIX in path:
                base, bundle = path.split(fanstatic.BUNDLE_PREFIX, 1)
                app = BundleApp(base, bundle, self.ignores)
                self.cached_apps[path_info] = app
            elif os.path.isfile(path):
                app = self.make_fileapp(path)
                self.cached_apps[path_info] = app
            else:
                raise webob.exc.HTTPNotFound()
        return app(environ, start_response)

class Publisher(object):
    """Fanstatic publisher WSGI application.

    This WSGI application serves Fanstatic :py:class:`Library`
    instances. Libraries are published as
    ``<library_name>/<optional_version>/path/to/resource.js``.

    All static resources contained in the libraries will be published
    to the web. If a step prefixed with ``:version:`` appears in the URL,
    this will be automatically skipped, and the HTTP response will
    indicate the resource can be cached forever.

    This WSGI component is used automatically by the
    :py:func:`Fanstatic` WSGI framework component, but can also be
    used independently if you need more control.

    :param library_registry: an instance of
      :py:class:`LibraryRegistry` with those resource libraries that
      should be published.
    """
    def __init__(self, library_registry):
        self.library_registry = library_registry
        self.directory_publishers = {}

    @webob.dec.wsgify
    def __call__(self, request):
        first = request.path_info_peek()
        # Don't allow requests on just publisher
        if first is None:
            raise webob.exc.HTTPNotFound()

        library_name = request.path_info_pop()
        # don't allow requests on just publisher
        if library_name == '':
            raise webob.exc.HTTPNotFound()

        # pop version if it's there
        potential_version = request.path_info_peek()
        if potential_version is not None and \
            potential_version.startswith(fanstatic.VERSION_PREFIX):
            request.path_info_pop()
            need_caching = True
        else:
            need_caching = False

        if request.path_info == '':
            raise webob.exc.HTTPNotFound()

        directory_publisher = self.directory_publishers.get(library_name)
        if directory_publisher is None:
            library = self.library_registry.get(library_name)
            if library is None:
                # unknown library
                raise webob.exc.HTTPNotFound()
            directory_publisher = self.directory_publishers.setdefault(
                library_name, DirectoryPublisher(library.path, library.ignores))

        # now delegate publishing to the directory publisher
        response = request.get_response(directory_publisher)
        # set caching when needed and for successful responses
        if need_caching and response.status.startswith('20'):
            response.cache_control.max_age = FOREVER
            response.expires = time.time() + FOREVER
        return response


class Delegator(object):
    """Fanstatic delegator WSGI framework component.

    This WSGI component recognizes URLs that point to Fanstatic
    libraries, and delegates them to the :py:class:`Publisher` WSGI
    application.

    In order to recognize such URLs it looks for occurrences of the
    ``publisher_signature`` parameter as a URL step. By default
    it looks for ``/fanstatic/``.

    This WSGI component is used automatically by the
    :py:func:`Fanstatic` WSGI framework component, but can also be
    used independently if you need more control.

    :param app: The WSGI app to wrap with the delegator.

    :param publisher: An instance of the :py:class:`Publisher` component.

    :param publisher_signature: Optional argument to define the
      signature of the publisher in a URL. The default is ``fanstatic``.
    """
    def __init__(self, app, publisher,
                 publisher_signature=fanstatic.DEFAULT_SIGNATURE):
        self.app = app
        self.publisher = publisher
        self.publisher_signature = publisher_signature
        self.trigger = '/%s/' % self.publisher_signature

    def is_resource(self, request):
        return len(request.path_info.split(self.trigger)) > 1

    @webob.dec.wsgify
    def __call__(self, request):
        if not self.is_resource(request):
            # the trigger segment is not in the URL, so we delegate
            # to the original application
            return request.get_response(self.app)
        # the trigger is in there, so let whatever is behind the
        # trigger be handled by the publisher
        ignored = request.path_info_pop()
        while ignored != self.publisher_signature:
            ignored = request.path_info_pop()
        return request.get_response(self.publisher)


def make_publisher(app, global_config,
                   publisher_signature=fanstatic.DEFAULT_SIGNATURE):
    publisher = Publisher(fanstatic.get_library_registry())
    return Delegator(app, publisher, publisher_signature=publisher_signature)
