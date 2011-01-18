import os
import sys
import threading

from fanstatic.checksum import checksum

DEFAULT_SIGNATURE = 'fanstatic'

VERSION_PREFIX  = ':version:'

NEEDED = 'fanstatic.needed'

DEBUG = 'debug'
MINIFIED = 'minified'

class UnknownResourceExtension(Exception):
    """Unknown resource extension"""

class ConfigurationError(Exception):
    pass

class Library(object):
    """The resource library.

    This object defines which directory is published and can be
    referred to by :py:class:`Resource` objects to describe
    these resources.

    :param name: A string that uniquely identifies this library.

    :param rootpath: An absolute or relative path to the directory
      that contains the static resources this library publishes. If
      relative, it will be relative to the directory of the module
      that initializes the library.

    :param ignores: A list of globs used to determine which files
      and directories not to publish.
    """

    path = None
    """
    The absolute path to the directory which contains the static resources
    this library publishes.
    """

    _signature = None

    def __init__(self, name, rootpath, ignores=None, version=None):
        self.name = name
        self.rootpath = rootpath
        self.ignores = ignores or []
        self.path = os.path.join(caller_dir(), rootpath)
        self.version = version

    def signature(self, recompute_hashes=False):
        """Get a unique signature for this Library.

        If a version has been defined, we return the version.

        If no version is defined, a hash of the contents of the directory
        indicated by ``path`` is calculated.
        If ``recompute_hashes`` is set to ``True``, the signature will be
        recalculated each time, which is useful during development when
        changing Javascript/css code and images.
        """
        if self.version is not None:
            return VERSION_PREFIX + self.version

        if recompute_hashes:
            # Always re-compute.
            sig = checksum(self.path)
        elif self._signature is None:
            # Only compute if not computed before.
            sig = self._signature = checksum(self.path)
        else:
            # Use cached value.
            sig = self._signature
        return VERSION_PREFIX + sig

# Total hack to be able to get the dir the resources will be in.
def caller_dir():
    return os.path.dirname(sys._getframe(2).f_globals['__file__'])

class InclusionRenderers(dict):

    _default_order = 0

    def register(self, extension, renderer, order=None):
        """Register a renderer function for a given filename extension.

        :param extension: the filename extension to register the
          renderer for.

        :param renderer: a callable that should accept a URL argument
          and return a rendered HTML snippet for this resource.

        :param order: optionally, to control the order in which the
          snippets are included in the HTML document. If no order is
          given, the resource will be included after all other resource
          inclusions. The lower the order number, the earlier in the
          rendering the inclusion will appear.
        """

        if order is None:
            order = self._default_order
        else:
            self._default_order = max(self._default_order, order+1)
        self[extension] = (order, renderer)

inclusion_renderers = InclusionRenderers()

register_inclusion_renderer = inclusion_renderers.register

def render_ico(url):
    return ('<link rel="shortcut icon" type="image/x-icon" href="%s"/>' %
            url)

def render_css(url):
    return ('<link rel="stylesheet" type="text/css" href="%s" />' %
            url)

def render_js(url):
    return ('<script type="text/javascript" src="%s"></script>' %
            url)

register_inclusion_renderer('.css', render_css, 10)

register_inclusion_renderer('.js', render_js, 20)

register_inclusion_renderer('.ico', render_ico, 30)

class Resource(object):
    """A resource.

    A resource specifies a single resource in a library so that it can
    be included in a web page. This is useful for Javascript and CSS
    resources in particular. Some static resources such as images are
    not included in this way and therefore do not have to be defined
    this way.

    :param library: the :py:class:`Library` this resource is in.

    :param relpath: the relative path (from the root of the library
      path) that indicates the actual resource file.

    :param depends: optionally, a list of resources that this resource
      depends on. Entries in the list can be :py:class:`Resource`
      instances, or, as a shortcut, strings that are paths to
      resources. If a string is given, a :py:class:`Resource` instance
      is constructed that has the same library as this resource.

    :param supersedes: optionally, a list of :py:class:`Resource`
      instances that this resource supersedes as a rollup
      resource. If all these resources are required for render a page,
      the superseding resource will be included instead.

    :param eager_superseder: normally superseding resources will only
      show up if all resources that the resource supersedes are
      required in a page. If this flag is set, even if only part of the
      requirements are met, the superseding resource will show up.

    :param bottom: indicate that this resource is "bottom safe": it
      can be safely included on the bottom of the page (just before
      ``</body>``). This can be used to improve the performance of
      page loads when Javascript resources are in use. Not all
      Javascript-based resources can however be safely included that
      way, so you have to set this explicitly (or use the
      ``force_bottom`` option on :py:class:`NeededResources`).

    :param renderer: optionally, a callable that accepts an URL
      argument and returns a rendered HTML snippet for this
      resource. If no renderer is provided, a renderer is looked up
      based on the resource's filename extension.

    :param debug: optionally, a debug version of the resource.
      The argument is a :py:class:`Resource` instance, or a string that
      indicates a relative path to the resource. In the latter case
      a :py:class:`Resource` instance is constructed that has the same
      library as the resource.

    :param minified: optionally, a minified version of the resource.
      The argument is a :py:class:`Resource` instance, or a string that
      indicates a relative path to the resource. In the latter case
      a :py:class:`Resource` instance is constructed that has the same
      library as the resource.
    """

    def __init__(self, library, relpath,
                 depends=None,
                 supersedes=None, eager_superseder=False,
                 bottom=False,
                 renderer=None,
                 debug=None,
                 minified=None):
        self.library = library
        self.relpath = relpath
        self.bottom = bottom

        self.ext = os.path.splitext(self.relpath)[1]

        if renderer is None:
            # No custom, ad-hoc renderer for this Resource, so lookup
            # the default renderer by resource filename extension.
            if self.ext not in inclusion_renderers:
                raise UnknownResourceExtension(
                    "Unknown resource extension %s for resource: %s" %
                    (self.ext, repr(self)))
            self.order, self.renderer = inclusion_renderers[self.ext]
        else:
            # Use the custom renderer.
            self.renderer = renderer
            # If we do not know about the filename extension inclusion
            # order, we render the resource after all others.
            self.order, _ = inclusion_renderers.get(
                self.ext, (sys.maxint, None))

        assert not isinstance(depends, basestring)
        depends = depends or []
        self.depends = normalize_resources(library, depends)

        self.modes = {}
        if debug is not None:
            self.modes[DEBUG] = normalize_resource(library, debug)
        if minified is not None:
            self.modes[MINIFIED] = normalize_resource(library, minified)

        assert not isinstance(supersedes, basestring)
        self.supersedes = supersedes or []
        self.eager_superseder = eager_superseder

        self.rollups = []
        # create a reference to the superseder in the superseded resource
        for resource in self.supersedes:
            resource.rollups.append(self)
        # also create a reference to the superseding mode in the superseded
        # mode
        # XXX what if mode is full-fledged resource which lists
        # supersedes itself?
        for mode_name, mode in self.modes.items():
            for resource in self.supersedes:
                superseded_mode = resource.mode(mode_name)
                # if there is no such mode, let's skip it
                if superseded_mode is resource:
                    continue
                mode.supersedes.append(superseded_mode)
                superseded_mode.rollups.append(mode)

    def render(self, library_url):
        return self.renderer('%s/%s' % (library_url, self.relpath))

    def __repr__(self):
        return "<Resource '%s' in library '%s'>" % (
            self.relpath, self.library.name)

    def mode(self, mode):
        """Get Resource in another mode.

        If the mode is ``None`` or if the mode cannot be found, this
        ``Resource`` instance is returned instead.

        :param mode: a string indicating the mode, or ``None``.
        """
        if mode is None:
            return self
        # try getting the alternative
        try:
            return self.modes[mode]
        except KeyError:
            # fall back on the default mode if mode not found
            return self

    def key(self):
        """A unique key that identifies this Resource.
        """
        return self.library.name, self.relpath

    def need(self):
        """Declare that the application needs this resource.

        If you call ``.need()`` on ``Resource`` sometime during the
        rendering process of your web page, this resource and all its
        dependencies will be inserted as inclusions into the web page.
        """
        needed = get_needed()
        needed.need(self)

    def resources(self):
        """Get all resources needed by this resource, including itself.
        """
        result = []
        for depend in self.depends:
            result.extend(depend.resources())
        result.append(self)
        return result

class GroupResource(object):
    """A resource used to group resources together.

    It doesn't define a resource file itself, but instead depends on
    other resources. When a GroupResources is depended on, all the
    resources grouped together will be included.

   :param depends: a list of resources that this resource depends
     on. Entries in the list can be :py:class:`Resource` instances, or
     :py:class:`GroupResource` instances.
    """
    def __init__(self, depends):
        self.depends = depends

    def need(self):
        """Need this group resource.

        If you call ``.need()`` on ``GroupResource`` sometime
        during the rendering process of your web page, all dependencies
        of this group resources will be inserted into the web page.
        """
        needed = get_needed()
        needed.need(self)

    def resources(self):
        """Get all resources needed by this resource.
        """
        result = []
        for depend in self.depends:
            result.extend(depend.resources())
        return result

def normalize_resources(library, resources):
    return [normalize_resource(library, resource)
            for resource in resources]

def normalize_resource(library, resource):
    if isinstance(resource, basestring):
        return Resource(library, resource)
    return resource

class NeededResources(object):
    """The current selection of needed resources..

    The ``NeededResources`` instance maintains a set of needed
    resources for a particular web page.

    :param versioning: If ``True``, Fanstatic will automatically include
      a version identifier in all URLs pointing to resources.
      Since the version identifier will change when you update a resource,
      the URLs can both be infinitely cached and the resources will always
      be up to date. See also the ``recompute_hashes`` parameter.

    :param recompute_hashes: If ``True`` and versioning is enabled, Fanstatic
      will recalculate hash URLs on the fly whenever you make changes, even
      without restarting the server. This is useful during development,
      but slower, so should be turned off during deployment.
      If set to ``False``, the hash URLs will only be
      calculated once after server startup.

    :param bottom: If set to ``True``, Fanstatic will include any
      resource that has been marked as "bottom safe" at the bottom of
      the web page, at the end of ``<body>``, as opposed to in the
      ``<head>`` section. This is useful for optimizing the load-time
      of Javascript resources.

    :param force_bottom: If set to ``True`` and ``bottom`` is set to
      ``True`` as well, all Javascript resources will be included at
      the bottom of a web page, even if they aren't marked bottom
      safe.

    :param minified: If set to ``True``, Fanstatic will include all
      resources in ``minified`` form. If a Resource instance does not
      provide a ``minified`` mode, the "main" (non-named) mode is used.

    :param debug: If set to ``True``, Fanstatic will include all
      resources in ``debug`` form. If a Resource instance does not
      provide a ``debug`` mode, the "main" (non-named) mode is used.
      An exception is raised when both the ``debug`` and ``minified``
      parameters are ``True``.

    :param rollup: If set to True (default is False) rolled up
      combined resources will be served if they exist and supersede
      existing resources that are needed.

    :param base_url: This URL will be prefixed in front of all resource
      URLs. This can be useful if your web framework wants the resources
      to be published on a sub-URL. Note that this can also be set
      as an attribute on an ``NeededResources`` instance.

    :param publisher_signature: The name under which resource libraries
      should be served in the URL. By default this is ``fanstatic``, so
      URLs to resources will start with ``/fanstatic/``.

    :param resources: Optionally, a list of resources we want to
      include. Normally you specify resources to include by calling
      ``.need()`` on them, or alternatively by calling ``.need()``
      on an instance of this class.

    """

    base_url = None
    """The base URL.

    This URL will be prefixed in front of all resource
    URLs. This can be useful if your web framework wants the resources
    to be published on a sub-URL. It is allowed for a web framework
    to change this attribute directly on an already existing
    ``NeededResources`` object.
    """
    _mode = None

    def __init__(self,
                 versioning=False,
                 recompute_hashes=True,
                 bottom=False,
                 force_bottom=False,
                 minified=False,
                 debug=False,
                 rollup=False,
                 base_url=None,
                 publisher_signature=DEFAULT_SIGNATURE,
                 resources=None,
                 ):
        self._versioning = versioning
        self._recompute_hashes = recompute_hashes
        self._bottom = bottom
        self._force_bottom = force_bottom
        self.base_url = base_url
        self._publisher_signature = publisher_signature
        self._rollup = rollup
        self._resources = resources or []

        if (debug and minified):
            raise ConfigurationError('Choose *one* of debug and minified')
        if debug is True:
            self._mode = DEBUG
        if minified is True:
            self._mode = MINIFIED

    def has_resources(self):
        """Returns True if any resources are needed.
        """
        return bool(self._resources)

    def need(self, resource):
        """Add a particular resource to the needed resources.

        This is an alternative to calling ``.need()`` on the resource
        directly.

        :param resource: A :py:class:`Resource` instance.
        """
        self._resources.append(resource)

    def resources(self):
        """Retrieve the list of resources needed.

        This returns the needed :py:class:`Resource`
        instances.  Resources are guaranteed to come earlier in the
        list than those resources that depend on them.

        Resources are also sorted by extension.
        """
        resources = []
        for resource in self._resources:
            resources.extend(resource.resources())

        resources = [resource.mode(self._mode) for resource in resources]

        if self._rollup:
            resources = consolidate(resources)
        # sort only by extension, not dependency, as we can rely on
        # python's stable sort to keep resource inclusion order intact
        resources = sort_resources(resources)
        resources = remove_duplicates(resources)

        return resources

    def clear(self):
        # Clear out any resources "needed" thusfar.
        # XXX or should we rather revert to the list with resources
        # that potentially was passed as an argument when creating
        # this NeededResources instance?
        self._resources = []

    def library_url(self, library):
        """Construct URL to library.

        This constructs a URL to a library, obey ``versioning`` and
        ``base_url`` configuration.

        :param library: A :py:class:`Library` instance.
        """
        if self.base_url is None:
            raise ConfigurationError(
                'No base_url: Set a base_url at configuration time or '
                'at request-time in your framework.')
        path = [self.base_url]
        if self._publisher_signature:
            path.append(self._publisher_signature)
        path.append(library.name)
        if self._versioning:
            path.append(
                library.signature(recompute_hashes=self._recompute_hashes))
        return '/'.join(path)

    def render(self):
        """Render needed resource inclusions.

        This returns a string with the rendered resource inclusions
        (``<script>`` and ``<link>`` tags), suitable for including
        in the ``<head>`` section of a web page.
        """
        return self.render_inclusions(self.resources())

    def render_inclusions(self, resources):
        """Render a set of resources as inclusions.

        This renders the listed inclusions and their dependencies as
        HTML ((``<script>`` and ``<link>`` tags), suitable for
        inclusion on a web page.

        :param inclusions: A list of :py:class:`Resource` instances.
        """
        result = []
        url_cache = {} # prevent multiple computations for a library in one request
        for resource in resources:
            library = resource.library
            library_url = url_cache.get(library.name)
            if library_url is None:
                library_url = url_cache[library.name] = self.library_url(
                    library)
            result.append(resource.render(library_url))
        return '\n'.join(result)

    def render_into_html(self, html):
        """Render needed resource inclusions into HTML.

        :param html: A string with HTML to render the resource
          inclusions into. This string must have a ``<head>`` section.
        """
        to_insert = self.render()
        return html.replace('<head>', '<head>\n    %s\n' % to_insert, 1)

    def render_topbottom(self):
        """Render resource inclusions separately into top and bottom fragments.

        Returns a tuple of two HTML snippets, top and bottom.  The top
        one is to be included in a ``<head>`` section, and the bottom
        one is to be included at the end of the ``<body>`` section. Only
        bottom safe resources are included in the bottom section,
        unless ``force_bottom`` is enabled, in which case all Javascript
        resources will be included in the bottom.
        """
        resources = self.resources()

        # seperate inclusions in top and bottom inclusions if this is needed
        if self._bottom:
            top_resources = []
            bottom_resources = []
            if not self._force_bottom:
                for resource in resources:
                    if resource.bottom:
                        bottom_resources.append(resource)
                    else:
                        top_resources.append(resource)
            else:
                for resource in resources:
                    if resource.ext == '.js':
                        bottom_resources.append(resource)
                    else:
                        top_resources.append(resource)
        else:
            top_resources = resources
            bottom_resources = []

        return (self.render_inclusions(top_resources),
                self.render_inclusions(bottom_resources))

    def render_topbottom_into_html(self, html):
        """Render needed resource inclusions into HTML.

        Only bottom safe resources are included in the bottom section,
        unless ``force_bottom`` is enabled, in which case all
        Javascript resources will be included in the bottom, just
        before the ``</body>`` tag.

        :param html: The HTML string in which to insert the rendered
          resource inclusions.  This string must have a ``<head>`` and
          a ``<body>`` section.
        """
        top, bottom = self.render_topbottom()
        if top:
            html = html.replace('<head>', '<head>\n    %s\n' % top, 1)
        if bottom:
            html = html.replace('</body>', '%s</body>' % bottom, 1)
        return html


class DummyNeededResources(object):
    """A dummy implementation of the needed resources.

    This class implements the same API as the NeededResources class,
    but refuses to do anything but need() resources. Resources that are
    needed are dropped to the floor.
    """

    base_url = None

    def need(self, resource):
        pass

    def has_resources(self):
        return False

    def _not_implented_here(self, *args, **kwargs):
        raise NotImplementedError('''
            This functionality is not implemented by objects of the %s class.
            You probably want a NeededResources object.'''\
            % self.__class__.__name__)

    clear = _not_implented_here
    library_url = render = render_inclusions = _not_implented_here
    render_into_html = render_topbottom = _not_implented_here
    resources = render_topbottom_into_html = _not_implented_here


thread_local_needed_data = threading.local()

def init_needed(*args, **kw):
    needed = NeededResources(*args, **kw)
    thread_local_needed_data.__dict__[NEEDED] = needed
    return needed

def get_needed():
    needed = thread_local_needed_data.__dict__.get(NEEDED)
    if needed is None:
        # When no NeededResources have been set up, we inject a
        # DummyNeededResources object here.
        # We do this in order not to tax other code that may need()
        # a resource here and there but has not set up NeededResources.
        return DummyNeededResources()
    return needed

def clear_needed():
    needed = get_needed()
    needed.clear()

def remove_duplicates(resources):
    """Given a set of resources, consolidate them so each only occurs once.
    """
    seen = set()
    result = []
    for resource in resources:
        key = resource.key()
        if key in seen:
            continue
        seen.add(key)
        result.append(resource)
    return result

def consolidate(resources):
    # keep track of rollups: rollup key -> set of resource keys
    potential_rollups = {}
    for resource in resources:
        for rollup in resource.rollups:
            s = potential_rollups.setdefault(rollup.key(), set())
            s.add(resource.key())

    # now go through resources, replacing them with rollups if
    # conditions match
    result = []
    for resource in resources:
        eager_superseders = []
        exact_superseders = []
        for rollup in resource.rollups:
            s = potential_rollups[rollup.key()]
            if rollup.eager_superseder:
                eager_superseders.append(rollup)
            if len(s) == len(rollup.supersedes):
                exact_superseders.append(rollup)
        if eager_superseders:
            # use the eager superseder that rolls up the most
            eager_superseders = sorted(eager_superseders,
                                       key=lambda i: len(i.supersedes))
            result.append(eager_superseders[-1])
        elif exact_superseders:
            # use the exact superseder that rolls up the most
            exact_superseders = sorted(exact_superseders,
                                       key=lambda i: len(i.supersedes))
            result.append(exact_superseders[-1])
        else:
            # nothing to supersede resource so use it directly
            result.append(resource)
    return result

def sort_resources(resources):
    def key(resource):
        return resource.order
    return sorted(resources, key=key)

def sort_resources_topological(resources):
    """Sort resources by dependency and supersedes.
    """
    dead = {}
    result = []
    for resource in resources:
        dead[resource.key()] = False

    for resource in resources:
        _visit(resource, result, dead)
    return result

def _visit(resource, result, dead):
    if dead[resource.key()]:
        return
    dead[resource.key()] = True
    for depend in resource.depends:
        _visit(depend, result, dead)
    for depend in resource.supersedes:
        _visit(depend ,result, dead)
    result.append(resource)
