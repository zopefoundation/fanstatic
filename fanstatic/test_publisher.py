import webob

from datetime import datetime, timedelta

from fanstatic import LibraryRegistry, Library, Publisher, Delegator
from fanstatic.publisher import FOREVER

def test_resource(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')
    resource = tmpdir.join('foo').join('test.js')
    resource.write('/* a test */')

    libraries = LibraryRegistry(
        [Library('foo', foo_library_dir.strpath)])

    app = Publisher(libraries)

    request = webob.Request.blank('/foo/test.js')
    response = request.get_response(app)
    assert response.body == '/* a test */'

def test_just_publisher():
    app = Publisher({})
    request = webob.Request.blank('/')
    response = request.get_response(app)
    assert response.status == '403 Forbidden'

def test_just_library(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')
    resource = tmpdir.join('foo').join('test.js')
    resource.write('/* a test */')

    libraries = LibraryRegistry(
        [Library('foo', foo_library_dir.strpath)])

    app = Publisher(libraries)

    request = webob.Request.blank('/foo')
    response = request.get_response(app)
    assert response.status == '403 Forbidden'

def test_unknown_library(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')
    resource = tmpdir.join('foo').join('test.js')
    resource.write('/* a test */')

    libraries = LibraryRegistry(
        [Library('foo', foo_library_dir.strpath)])

    app = Publisher(libraries)

    request = webob.Request.blank('/bar')
    response = request.get_response(app)
    assert response.status == '404 Not Found'

def test_resource_version_skipped(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')
    resource = tmpdir.join('foo').join('test.js')
    resource.write('/* a test */')

    libraries = LibraryRegistry(
        [Library('foo', foo_library_dir.strpath)])

    app = Publisher(libraries)

    request = webob.Request.blank('/foo/:version:something/test.js')
    response = request.get_response(app)
    assert response.body == '/* a test */'

def test_resource_no_version_no_cache(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')
    resource = tmpdir.join('foo').join('test.js')
    resource.write('/* a test */')

    libraries = LibraryRegistry(
        [Library('foo', foo_library_dir.strpath)])

    app = Publisher(libraries)

    request = webob.Request.blank('/foo/test.js')
    response = request.get_response(app)
    assert response.body == '/* a test */'
    assert response.cache_control.max_age is None
    assert response.expires is None

def test_resource_hash_cache(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')
    resource = tmpdir.join('foo').join('test.js')
    resource.write('/* a test */')

    libraries = LibraryRegistry(
        [Library('foo', foo_library_dir.strpath)])

    app = Publisher(libraries)

    request = webob.Request.blank('/foo/:version:something/test.js')
    response = request.get_response(app)
    assert response.body == '/* a test */'
    assert response.cache_control.max_age == FOREVER
    # the test has just run and will take less than a full day to
    # run. we therefore expect the expires to be greater than
    # one_day_ago + FOREVER
    utc = response.expires.tzinfo # get UTC as a hack
    one_day_ago = datetime.now(utc) - timedelta(days=1)
    future = one_day_ago + timedelta(seconds=FOREVER)
    assert response.expires > future

def test_resource_cache_only_for_success(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')

    libraries = LibraryRegistry(
        [Library('foo', foo_library_dir.strpath)])

    app = Publisher(libraries)

    request = webob.Request.blank('/foo/:version:something/nonexistent.js')
    response = request.get_response(app)
    assert response.status == '404 Not Found'
    assert response.cache_control.max_age is None
    assert response.expires is None

def test_delegator(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')
    resource = tmpdir.join('foo').join('test.js')
    resource.write('/* a test */')

    libraries = LibraryRegistry(
        [Library('foo', foo_library_dir.strpath)])

    publisher = Publisher(libraries)

    def real_app(environ, start_response):
        start_response('200 OK', [])
        return ['Hello world!']

    delegator = Delegator(real_app, publisher)

    request = webob.Request.blank('/fanstatic/foo/test.js')
    response = request.get_response(delegator)
    assert response.body == '/* a test */'

    request = webob.Request.blank('/somethingelse')
    response = request.get_response(delegator)
    assert response.body == 'Hello world!'

def test_publisher_ignores(tmpdir):
    foo_library_dir = tmpdir.mkdir('foo')
    tmpdir.join('foo').mkdir('.svn').join('entries').write('secret')
    foo_library = Library('foo', foo_library_dir.strpath)

    publisher = Publisher(LibraryRegistry([foo_library]))
    request = webob.Request.blank('/foo/.svn/entries')
    response = request.get_response(publisher)
    assert response.body == 'secret'

    foo_library = Library('foo', foo_library_dir.strpath, ignores=['.svn'])
    publisher = Publisher(LibraryRegistry([foo_library]))
    request = webob.Request.blank('/foo/.svn/entries')
    response = request.get_response(publisher)
    assert response.status_int == 404

    foo_library.ignores.extend(['*.psd', '*.ttf'])
    tmpdir.join('foo').join('font.ttf').write('I am a font.')
    request = webob.Request.blank('/foo/font.ttf')
    response = request.get_response(publisher)
    assert response.status_int == 404

    tmpdir.join('foo').join('logo.psd').write('I am a logo.')
    request = webob.Request.blank('/foo/logo.psd')
    response = request.get_response(publisher)
    assert response.status_int == 404

