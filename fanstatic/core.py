import os
import sys
import pkg_resources
import threading
import UserDict

from fanstatic.checksum import checksum

DEFAULT_SIGNATURE = 'fanstatic'

EXTENSIONS = ['.css', '.kss', '.js']

NEEDED = 'fanstatic.needed'

# Total hack to be able to get the dir the resources will be in.
def caller_dir():
    return os.path.dirname(sys._getframe(2).f_globals['__file__'])

class UnknownResourceExtension(Exception):
    """Unknown resource extension"""

class Library(object):
    """The resource library.

    This object defines which directory is published and can be
    referred to by :py:class:`ResourceInclusion` objects to describe
    these resources.

    :param name: A string that uniquely identifies this library.
    
    :param rootpath: An absolute or relative path to the directory
      that contains the static resources this library publishes. If
      relative, it will be relative to the directory of the module
      that initializes the library.
    """
    
    _signature = None

    name = None
    """
    A string that uniquely identifies this library.
    """

    rootpath = None
    """
    The (relative or absolute) path to the directory that contains the
    static resources.
    """

    path = None
    """
    The absolute path to the directory which contains the static
    resources this library publishes.
    """
    
    def __init__(self, name, rootpath):
        self.name = name
        self.rootpath = rootpath
        self.path = os.path.join(caller_dir(), rootpath)

    def signature(self, devmode=False):
        """Get a unique signature for this Library.

        This is calculated by hashing the contents of the directory
        indicated by ``path``. If ``devmode`` is set to ``True``, the
        signature will be recalculated each time, which is useful
        during development when changing Javascript code.
        """
        if devmode:
            # Always re-compute.
            sig = checksum(self.path)
        elif self._signature is None:
            # Only compute if not conputed before.
            sig = self._signature = checksum(self.path)
        else:
            # Use cached value.
            sig = self._signature
        return ':hash:%s' % sig

class LibraryRegistry(UserDict.DictMixin):

    def __init__(self):
        self._entry_points = {}
        self._libraries = {}
        self.reset()

    def reset(self):
        # Load all fanstatic.libraries entry points.
        for entry_point in pkg_resources.iter_entry_points(
            'fanstatic.libraries'):
            self._entry_points[entry_point.name] = entry_point
            self._libraries[entry_point.name] = None

    def __getitem__(self, name):
        library = self._libraries.get(name)
        if library is None:
            library = self._entry_points[name].load()
            self._libraries[name] = library
        return library

    def __setitem__(self, name, value):
        self._libraries[name] = value

    def keys(self):
        return self._libraries.keys()

    def add(self, library):
        self[library.name] = library

library_registry = LibraryRegistry()

class InclusionBase(object):
    pass

class ResourceInclusion(InclusionBase):
    """A resource inclusion.

   A resource inclusion specifies how to include a single resource in
   a library in a web page. This is useful for Javascript and CSS
   resources in particular. Some static resources such as images are
   not included in this way and therefore do not have to be defined
   this way.

   :param library: the :py:class:`Library` this resource is in.

   :param relpath: the relative path (from the root of the library
     path) that indicates the actual resource file.

   :param depends: optionally, a list of resources that this resource
     depends on. Entries in the list can be
     :py:class:`ResourceInclusion` instances, or, as a shortcut,
     strings that are paths to resources. If a string is given, a
     :py:class:`ResourceInclusion` instance is constructed that has
     the same library as this inclusion.
     
   :param supersedes: optionally, a list of
     :py:class:`ResourceInclusion` instances that this resource
     inclusion supersedes as a rollup resource. If all these resources
     are required for render a page, the superseding resource will be
     included instead.
     
   :param eager_superseder: normally superseding resources will only
     show up if all resources that the resource supersedes are
     required in a page. If this flag is set, even if only part of the
     requirements are met, the superseding resource will show up.

   :param bottom: indicate that this resource inclusion is "bottom
     safe": it can be safely included on the bottom of the page (just
     before ``</body>``). This can be used to improve the performance
     of page loads when Javascript resources are in use. Not all
     Javascript-based resources can however be safely included that
     way, so you have to set this explicitly (or use the
     ``force_bottom`` option on :py:class:`NeededInclusions`).

   :param ``**kw``: keyword parameters can be supplied to indicate
     alternate resource inclusions. An alternate inclusion is for
     instance a minified version of this resource. The name of the
     parameter indicates the type of alternate resource (``debug``,
     ``minified``, etc), and the value is a
     :py:class:`ResourceInclusion` instance.

     As a shortcut, a string can be supplied as value that indicates
     the relative path to a resource in the library (for instance the
     minified file). In this case :py:class:`ResourceInclusion`
     instance is constructed that has the same library as this
     inclusion.
   """

    def __init__(self, library, relpath, depends=None,
                 supersedes=None, eager_superseder=False,
                 bottom=False, **kw):
        self.library = library
        self.relpath = relpath
        self.bottom = bottom

        assert not isinstance(depends, basestring)
        depends = depends or []
        self.depends = normalize_inclusions(library, depends)

        self.rollups = []

        normalized_modes = {}
        for mode_name, inclusion in kw.items():
            normalized_modes[mode_name] = normalize_inclusion(
                library, inclusion)
        self.modes = normalized_modes

        assert not isinstance(supersedes, basestring)
        self.supersedes = supersedes or []
        self.eager_superseder = eager_superseder

        # create a reference to the superseder in the superseded inclusion
        for inclusion in self.supersedes:
            inclusion.rollups.append(self)
        # also create a reference to the superseding mode in the superseded
        # mode
        # XXX what if mode is full-fledged resource inclusion which lists
        # supersedes itself?
        for mode_name, mode in self.modes.items():
            for inclusion in self.supersedes:
                superseded_mode = inclusion.mode(mode_name)
                # if there is no such mode, let's skip it
                if superseded_mode is inclusion:
                    continue
                mode.supersedes.append(superseded_mode)
                superseded_mode.rollups.append(mode)

    def __repr__(self):
        return "<ResourceInclusion '%s' in library '%s'>" % (
            self.relpath, self.library.name)

    def ext(self):
        """The extension of this resource inclusion.

        An extension starts with a period. Examples ``.js``, ``.css``.
        """
        name, ext = os.path.splitext(self.relpath)
        return ext

    def mode(self, mode):
        """Get ResourceInclusion in another mode.

        If the mode is ``None`` or if the mode cannot be found, this
        ``ResourceInclusion`` instance is returned instead.

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
        """A unique key that identifies this ResourceInclusion.
        """
        return self.library.name, self.relpath

    def need(self):
        """Need this resource inclusion.

        If you call ``.need()`` on ``ResourceInclusion`` sometime
        during the rendering process of your web page, this resource
        inclusion and all its dependencies will be inserted into the
        web page.
        """
        needed = get_current_needed_inclusions()
        needed.need(self)

    def inclusions(self):
        """Get all inclusions needed by this inclusion, including itself.
        """
        result = []
        for depend in self.depends:
            result.extend(depend.inclusions())
        result.append(self)
        return result

class GroupInclusion(InclusionBase):
    """An inclusion used to group resources together.

    It doesn't define a resource inclusion itself, but instead depends on other
    resource inclusions. When a GroupInclusion is depended on, all the
    resources grouped together will be included.

   :param depends: a list of resources that this resource depends
     on. Entries in the list can be :py:class:`ResourceInclusion`
     instances, or :py:class:`GroupInclusion` instances.
    """
    def __init__(self, depends):
        self.depends = depends

    def need(self):
        """Need this group inclusion.

        If you call ``.need()`` on ``GroupInclusion`` sometime
        during the rendering process of your web page, all dependencies
        of this group inclusion will be inserted into the web page.
        """
        needed = get_current_needed_inclusions()
        needed.need(self)

    def inclusions(self):
        """Get all inclusions needed by this inclusion.
        """
        result = []
        for depend in self.depends:
            result.extend(depend.inclusions())
        return result

def normalize_inclusions(library, inclusions):
    return [normalize_inclusion(library, inclusion)
            for inclusion in inclusions]

def normalize_inclusion(library, inclusion):
    if isinstance(inclusion, InclusionBase):
        return inclusion
    assert isinstance(inclusion, basestring)
    return ResourceInclusion(library, inclusion)

class NeededInclusions(object):
    """The current selection of needed inclusions.
    
    The ``NeededInclusions`` instance maintains a set of needed
    inclusions for a particular web page.
    
    :param hashing: If ``True``, Fanstatic will automatically include
      a hash in all URLs pointing to resources. Since the hash will change
      when you update a resource, the URLs can both be infinitely cached
      and the resources will always be up to date. See also the ``devmode``
      parameter.

    :param devmode: If ``True`` and hashing is enabled, Fanstatic will
      recalculate hash URLs on the fly whenever you make changes, even
      without restarting the server. This is useful during
      development, but slower, so should be turned off during
      deployment. If set to ``False``, the hash URLs will only be
      calculated once after server startup.
    
    :param bottom: If set to ``True``, Fanstatic will include any
      resource inclusion that has been marked as "bottom safe" at the
      bottom of the web page, at the end of ``<body>``, as opposed to
      in the ``<head>`` section. This is useful for optimizing the
      load-time of Javascript resources.
      
    :param force_bottom: If set to ``True`` and ``bottom`` is set to
      ``True`` as well, all Javascript resources will be included at
      the bottom of a web page, even if they aren't marked bottom
      safe.

    :param mode: A string that indicates the mode. A resource may
      exist in certain different alternative forms, such as ``minified``,
      ``debug``, etc. This specifies which alternative to prefer (if
      available). By default and if not available the "main" (non-named)
      mode alternative of the resource will be served.
      
    :param rollup: If set to True (default is False) rolled up
      combined resources will be served if they exist and supersede
      existing resources that are needed.
    
    :param base_url: This URL will be prefixed in front of all resource
      URLs. This can be useful if your web framework wants the resources
      to be published on a sub-URL. Note that this can also be set
      as an attribute on an ``NeededInclusions`` instance.

    :param publisher_signature: The name under which resource libraries
      should be served in the URL. By default this is ``fanstatic``, so
      URLs to resources will start with ``/fanstatic/``.

    :param inclusions: Optionally, a list of resources we want to
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
    ``NeededInclusions`` object.
    """
    
    def __init__(self,
                 hashing=False,
                 devmode=False,
                 bottom=False,
                 force_bottom=False,
                 mode=None,
                 rollup=False,
                 base_url='',
                 publisher_signature=DEFAULT_SIGNATURE,
                 inclusions=None,
                 ):
        self._hashing = hashing
        self._devmode = devmode
        self._bottom = bottom
        self._force_bottom = force_bottom
        self._mode = mode
        self.base_url = base_url
        self._publisher_signature = publisher_signature
        self._rollup = rollup

        self._inclusions = inclusions or []
              
    def has_inclusions(self):
        """Returns True if any inclusions are needed.
        """
        return bool(self._inclusions)

    def need(self, inclusion):
        """Add a particular inclusion to the needed inclusions.

        This is an alternative to calling ``.need()`` on the resource
        inclusion directly.

        :param inclusion: A :py:class:`ResourceInclusion` instance.
        """
        self._inclusions.append(inclusion)

    def _sorted_inclusions(self):
        return reversed(sorted(self._inclusions, key=lambda i: i.depth()))

    def inclusions(self):
        """Retrieve the list of resource inclusions needed.

        This returns the needed :py:class:`ResourceInclusion`
        instances.  Inclusions are guaranteed to come earlier in the
        list than those inclusions that depend on them.

        Inclusions are also sorted by extension.
        """
        inclusions = []
        for inclusion in self._inclusions:
            inclusions.extend(inclusion.inclusions())

        inclusions = apply_mode(inclusions, self._mode)
        if self._rollup:
            inclusions = consolidate(inclusions)
        # sort only by extension, not dependency, as we can rely on
        # python's stable sort to keep inclusion order intact
        inclusions = sort_inclusions_by_extension(inclusions)
        inclusions = remove_duplicates(inclusions)

        return inclusions

    def library_url(self, library):
        """Construct URL to library.

        This constructs a URL to a library, obey ``hashing`` and
        ``base_url`` configuration.
        
        :param library: A :py:class:`Library` instance.
        """
        segments = [self.base_url, self._publisher_signature]
        segments.append(library.name)
        if self._hashing:
            segments.append(library.signature(devmode=self._devmode))
        result = segments.pop(0)
        for segment in segments:
            if not result.endswith('/'):
                result += '/'
            result += segment
        return result

    def render(self):
        """Render needed inclusions.

        This returns a string with the rendered inclusions
        (``<script>`` and ``<link>`` tags), suitable for including
        in the ``<head>`` section of a web page.
        """
        return self.render_inclusions(self.inclusions())

    def render_inclusions(self, inclusions):
        """Render a set of inclusions.

        This renders the listed inclusions and their dependencies as
        HTML ((``<script>`` and ``<link>`` tags), suitable for
        inclusion on a web page.
        
        :param inclusions: A list of :py:class:`ResourceInclusion` instances.
        """
        result = []
        url_cache = {} # prevent multiple computations for a library in one request
        for inclusion in inclusions:
            library = inclusion.library
            library_url = url_cache.get(library.name)
            if library_url is None:
                library_url = url_cache[library.name] = self.library_url(
                    library)
            result.append(
                render_inclusion(
                    inclusion, '%s/%s' %(library_url, inclusion.relpath)))
        return '\n'.join(result)

    def render_into_html(self, html):
        """Render needed inclusions into HTML.

        :param html: A string with HTML to render the inclusions into. This
          string must have a ``<head>`` section.
        """
        to_insert = self.render()
        return html.replace('<head>', '<head>\n    %s\n' % to_insert, 1)

    def render_topbottom(self):
        """Render inclusions separately into top and bottom fragments.

        Returns a tuple of two HTML snippets, top and bottom.  The top
        one is to be included in a ``<head>`` section, and the bottom
        one is to be included at the end of the ``<body>`` section. Only
        bottom safe resources are included in the bottom section,
        unless ``force_bottom`` is enabled, in which case all Javascript
        resources will be included in the bottom.
        """
        inclusions = self.inclusions()

        # seperate inclusions in top and bottom inclusions if this is needed
        if self._bottom:
            top_inclusions = []
            bottom_inclusions = []
            if not self._force_bottom:
                for inclusion in inclusions:
                    if inclusion.bottom:
                        bottom_inclusions.append(inclusion)
                    else:
                        top_inclusions.append(inclusion)
            else:
                for inclusion in inclusions:
                    if inclusion.ext() == '.js':
                        bottom_inclusions.append(inclusion)
                    else:
                        top_inclusions.append(inclusion)
        else:
            top_inclusions = inclusions
            bottom_inclusions = []

        return (self.render_inclusions(top_inclusions),
                self.render_inclusions(bottom_inclusions))

    def render_topbottom_into_html(self, html):
        """Render needed inclusions into HTML.

        Only bottom safe resources are included in the bottom section,
        unless ``force_bottom`` is enabled, in which case all
        Javascript resources will be included in the bottom, just
        before the ``</body>`` tag.
        
        :param html: A string with HTML to render the inclusions into. This
          string must have a ``<head>`` and a ``<body>`` section.
        """
        top, bottom = self.render_topbottom()
        if top:
            html = html.replace('<head>', '<head>\n    %s\n' % top, 1)
        if bottom:
            html = html.replace('</body>', '%s</body>' % bottom, 1)
        return html

class NoNeededInclusions(Exception):
    pass

thread_local_needed_data = threading.local()

def init_current_needed_inclusions(*args, **kw):
    needed = NeededInclusions(*args, **kw)
    thread_local_needed_data.__dict__[NEEDED] = needed
    return needed

def get_current_needed_inclusions():
    needed = thread_local_needed_data.__dict__.get(NEEDED)
    if needed is None:
        raise NoNeededInclusions('No NeededInclusions object initialized.')
    return needed

def apply_mode(inclusions, mode):
    return [inclusion.mode(mode) for inclusion in inclusions]

def remove_duplicates(inclusions):
    """Given a set of inclusions, consolidate them so each only occurs once.
    """
    seen = set()
    result = []
    for inclusion in inclusions:
        if inclusion.key() in seen:
            continue
        seen.add(inclusion.key())
        result.append(inclusion)
    return result

def consolidate(inclusions):
    # keep track of rollups: rollup key -> set of inclusion keys
    potential_rollups = {}
    for inclusion in inclusions:
        for rollup in inclusion.rollups:
            s = potential_rollups.setdefault(rollup.key(), set())
            s.add(inclusion.key())

    # now go through inclusions, replacing them with rollups if
    # conditions match
    result = []
    for inclusion in inclusions:
        eager_superseders = []
        exact_superseders = []
        for rollup in inclusion.rollups:
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
            result.append(inclusion)
    return result

def sort_inclusions_by_extension(inclusions):

    def key(inclusion):
        return EXTENSIONS.index(inclusion.ext())

    return sorted(inclusions, key=key)

def sort_inclusions_topological(inclusions):
    """Sort inclusions by dependency and supersedes.
    """
    dead = {}
    result = []
    for inclusion in inclusions:
        dead[inclusion.key()] = False

    for inclusion in inclusions:
        _visit(inclusion, result, dead)
    return result

def _visit(inclusion, result, dead):
    if dead[inclusion.key()]:
        return
    dead[inclusion.key()] = True
    for depend in inclusion.depends:
        _visit(depend, result, dead)
    for depend in inclusion.supersedes:
        _visit(depend ,result, dead)
    result.append(inclusion)

def render_css(url):
    return ('<link rel="stylesheet" type="text/css" href="%s" />' %
            url)

def render_kss(url):
    raise NotImplementedError

def render_js(url):
    return ('<script type="text/javascript" src="%s"></script>' %
            url)

inclusion_renderers = {
    '.css': render_css,
    '.kss': render_kss,
    '.js': render_js,
    }

def render_inclusion(inclusion, url):
    renderer = inclusion_renderers.get(inclusion.ext(), None)
    if renderer is None:
        raise UnknownResourceExtension(
            "Unknown resource extension %s for resource inclusion: %s" %
            (inclusion.ext(), repr(inclusion)))
    return renderer(url)

