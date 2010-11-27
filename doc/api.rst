API Overview
============

.. py:module:: fanstatic

Library
-------

.. py:class:: Library

  The resource library. This object defines which directory is
  published and can be referred to by :py:class:`ResourceInclusion`
  objects to describe these resources.

  .. py:method:: __init__(name, rootpath):
  
    :param name: A string that uniquely identifies this library.
    
    :param rootpath: An absolute or relative path to the directory
      that contains the static resources this library publishes. If
      relative, it will be relative to the directory of the module
      that initializes the library.
 
  .. py:attribute:: name

    A string that uniquely identifies this library.

  .. py:attribute:: rootpath
    
    The (relative or absolute) path to the directory that contains the
    static resources.

  .. py:attribute:: path

    The absolute path to the directory which contains the static
    resources this library publishes.

  .. py:method:: signature(devmode=False)

    Get a unique signature for this Library. This is calculated by
    hashing the contents of the directory indicated by ``path``. If
    ``devmode`` is set to ``True``, the signature will be recalculated
    each time, which is useful during development when changing
    Javascript code.

ResourceInclusion
-----------------

.. py:class:: ResourceInclusion

   A resource inclusion specifies how to include a single resource in
   a library in a web page. This is useful for Javascript and CSS
   resources in particular. Some static resources such as images are
   not included in this way and therefore do not have to be defined
   this way.

  .. py:method:: __init__(library, relpath, depends=None, \
       supersedes=None, eager_superseder=False, bottom=False, **kw):

     Create a resource inclusion

     :param library: the :py:class:`Library` this resource is in.

     :param relpath: the relative path (from the root of the library
       path) that indicates the actual resource file.

     :param depends: optionally, a list of resources that this
       resource depends on. Entries in the list can be
       :py:class:`ResourceInclusion` instances, or, as a shortcut,
       strings that are paths to resources. If a string is given, a
       :py:class:`ResourceInclusion` instance is constructed that has
       the same library as this inclusion.
     
     :param supersedes: optionally, a list of
       :py:class:`ResourceInclusion` instances that this resource
       inclusion supersedes as a rollup resource. If all these
       resources are required for render a page, the superseding
       resource will be included instead.
     
     :param eager_superseder: normally superseding resources will only
       show up if all resources that the resource supersedes are
       required in a page. If this flag is set, even if only part of
       the requirements are met, the superseding resource will show
       up.

     :param bottom: optionally, indicate that this resource inclusion
       can be safely included on the bottom of the page (just before
       ``</body>``). This can be used to improve the performance of
       page loads when Javascript resources are in use. Not all
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
       the relative path to a resource in the library (for instance
       the minified file). In this case :py:class:`ResourceInclusion`
       instance is constructed that has the same library as this
       inclusion.

NeededInclusions
----------------

.. py:class:: NeededInclusions
 

