import fnmatch
import os.path
import time

import webob.dec
import webob.exc
import webob.static

import fanstatic


MINUTE_IN_SECONDS = 60
HOUR_IN_SECONDS = MINUTE_IN_SECONDS * 60
DAY_IN_SECONDS = HOUR_IN_SECONDS * 24
YEAR_IN_SECONDS = DAY_IN_SECONDS * 365

# arbitrarily define forever as 10 years in the future
FOREVER = YEAR_IN_SECONDS * 10


class BundleApp(webob.static.FileApp):

    def __init__(self, rootpath, bundle, filenames):
        # Let FileApp determine content_type and encoding based on bundlename.
        super().__init__(bundle)
        self.filenames = []
        for filename in filenames:
            fullpath = os.path.join(rootpath, filename)
            if not os.path.abspath(fullpath).startswith(rootpath):
                # Raising forbidden here would expose private information.
                raise webob.exc.HTTPNotFound()  # pragma: no cover
            if not os.path.exists(fullpath):
                raise webob.exc.HTTPNotFound()
            self.filenames.append(fullpath)

    @webob.dec.wsgify
    def __call__(self, req):
        if req.method not in ('GET', 'HEAD'):
            return webob.exc.HTTPMethodNotAllowed()
        mtime = 0
        contents = []
        for filename in self.filenames:
            mtime = max(mtime, os.path.getmtime(filename))
            fh = open(filename, 'rb')
            contents.append(fh.read())
            fh.close()
        return webob.Response(
            body=b'\n'.join(contents),
            last_modified=mtime,
            **self.kw
        ).conditional_response_app


class LibraryPublisher(webob.static.DirectoryApp):
    """Fanstatic directory publisher WSGI application.

    This WSGI application serves a directory of static resources to
    the web.

    This WSGI component is used automatically by the
    :py:func:`Fanstatic` WSGI framework component, but can also be
    used independently if you need more control.

    :param library: The fanstatic library instance.
    """

    def __init__(self, library):
        self.ignores = library.ignores
        self.library = library
        self.cached_apps = {}
        super().__init__(library.path)

    @webob.dec.wsgify
    def __call__(self, req):
        for ignore in self.ignores:
            if fnmatch.filter(req.path.split('/'), ignore):
                raise webob.exc.HTTPNotFound()

        app = self.cached_apps.get(req.path)
        if app is None:
            path = os.path.abspath(
                os.path.join(self.path, req.path_info.lstrip('/')))
            if not path.startswith(self.path):
                raise webob.exc.HTTPForbidden()
            elif fanstatic.BUNDLE_PREFIX in path:

                # We are handling a bundle request.
                subdir, bundle = req.path_info.split(
                    fanstatic.BUNDLE_PREFIX, 1)
                subdir = subdir.lstrip('/')
                dependency_nr = 0
                filenames = []
                # Check for duplicate filenames (`dirty bundles`) and check
                # whether the filenames belong to a Resource definition.
                for filename in bundle.split(';'):
                    resource = self.library.known_resources.get(
                        subdir + filename)
                    if resource is None:
                        raise webob.exc.HTTPNotFound()
                    if resource.dependency_nr < dependency_nr:
                        # Invalid bundle, resources in a bundle should be
                        # sorted by dependency_nr.
                        raise webob.exc.HTTPNotFound()
                    dependency_nr = resource.dependency_nr
                    if filename in filenames:
                        # We have a `dirty bundle` request.
                        raise webob.exc.HTTPNotFound()
                    else:
                        filenames.append(filename)
                # normpath in order to correct the dirname on Windoze.
                base = os.path.abspath(os.path.join(self.path, subdir))
                app = BundleApp(base, bundle, filenames)
            elif os.path.isfile(path):
                app = self.make_fileapp(path)
            else:
                raise webob.exc.HTTPNotFound()
            # Cache the app under the original req.path
            self.cached_apps[req.path] = app
        return app


class Publisher:
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

    :param registry: an instance of
      :py:class:`LibraryRegistry` with those resource libraries that
      should be published.
    """

    def __init__(self, registry):
        self.registry = registry
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
            library = self.registry.get(library_name)
            if library is None:
                # unknown library
                raise webob.exc.HTTPNotFound()
            self.registry.prepare()
            directory_publisher = self.directory_publishers[library_name] = \
                LibraryPublisher(library)

        # now delegate publishing to the directory publisher
        response = request.get_response(directory_publisher)
        # set caching when needed and for successful responses
        if need_caching and response.status.startswith('20'):
            response.cache_control.max_age = FOREVER
            response.expires = time.time() + FOREVER
        return response


class Delegator:
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

    def __call__(self, environ, start_response):
        request = webob.Request(environ)
        if not self.is_resource(request):
            # the trigger segment is not in the URL, so we delegate
            # to the original application
            return self.app(environ, start_response)
        # the trigger is in there, so let whatever is behind the
        # trigger be handled by the publisher
        ignored = request.path_info_pop()
        while ignored != self.publisher_signature:
            ignored = request.path_info_pop()
        return self.publisher(environ, start_response)


def make_publisher(global_config):
    registry = fanstatic.get_library_registry()
    return Publisher(registry)
