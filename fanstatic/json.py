import simplejson

# {
#   libraries: {
#     library_name: { path: '...' } {
#       resources: {
#          resource_name: {  path: '...', deps: ['library_name:resource_name']}
#        },
#       slots: {
#          resource_name: { library: '...', ext: '.js', deps: ['....'] }
#        }
#   groups: {
#      name: { deps: ['...'] },
#   }
# }
#

# if library_name is left off then it defaults of the library it is
# embedded in

# the algorithm, a sketch

# create unresolved libraries, then unresolved resources and unresolved
# slots in them
# also create unresolved groups

# the libraries should be resolvable right away as they don't have
# dependencies themselves

# now we should be able to sort the resources topologically so that the
# resources with the least dependencies come first, etc

# an external dependency counts as no dependency in this sorting.

# we need to watch out for cyclic library and resource dependencies
# here and report an error if so

# then we can start resolving in the sort order. We can look up
# previously resolved resources when resolving a resource that
# has dependencies

# we now end up with a structure of libraries with resources (and
# slots). groups will have been removed as they only are a way to summarize
# dependencies

# we can now say: need(library_name, resource_name) and it will look up
# matters in that structure.

# note that we cannot support this structure with Python-only resources
# as we do not know their names.... We can however generate a Python
# equivalent to this library
