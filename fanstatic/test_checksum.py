import shutil
from pkg_resources import resource_filename

from fanstatic.checksum import list_directory, checksum
from fanstatic.checksum import VCS_NAMES, IGNORED_EXTENSIONS

def _copy_testdata(tmpdir):
    src = resource_filename('fanstatic', 'testdata/MyPackage')
    dst = tmpdir / 'MyPackage'
    shutil.copytree(src, str(dst))
    return dst

def test_list_directory(tmpdir):
    testdata_path = str(_copy_testdata(tmpdir))
    expected = [
        tmpdir.join('MyPackage/setup.py').strpath,
        tmpdir.join('MyPackage/MANIFEST.in').strpath,
        tmpdir.join('MyPackage/src/mypackage/__init__.py').strpath,
        tmpdir.join('MyPackage/src/mypackage/resources/style.css').strpath,
        ]
    found = list(list_directory(testdata_path))
    assert sorted(found) == sorted(expected)

def test_checksum(tmpdir):
    testdata_path = str(_copy_testdata(tmpdir))
    # As we cannot rely on a particular sort order of the directories,
    # and files therein we cannot test against a given md5sum. So
    # we'll have to do with circumstantial evidence.

    # Compute a first checksum for the test package:
    chksum_start = checksum(testdata_path)
    # Add a file (+ contents!) and see the checksum changed:
    tmpdir.join('/MyPackage/A').write('Contents for A')
    assert checksum(testdata_path) != chksum_start

    # Remove the file again, the checksum is same as we started with:
    tmpdir.join('/MyPackage/A').remove()
    assert checksum(testdata_path) == chksum_start

    # Obviously, changing the contents will change the checksum too:
    tmpdir.join('/MyPackage/B').write('Contents for B')
    chksum_start = checksum(testdata_path)
    tmpdir.join('/MyPackage/B').write('Contents for B have changed')
    assert checksum(testdata_path) != chksum_start
    tmpdir.join('/MyPackage/B').remove()

    # Moving, or renaming a file should change the checksum:
    chksum_start = checksum(testdata_path)
    tmpdir.join('/MyPackage/setup.py').rename(
        tmpdir.join('/MyPackage/setup.py.renamed'))
    expected = [
        tmpdir.join('MyPackage/setup.py.renamed').strpath,
        tmpdir.join('MyPackage/MANIFEST.in').strpath,
        tmpdir.join('MyPackage/src/mypackage/__init__.py').strpath,
        tmpdir.join('MyPackage/src/mypackage/resources/style.css').strpath,
        ]
    found = list(list_directory(testdata_path))
    assert sorted(found) == sorted(expected)
    assert checksum(testdata_path) != chksum_start

def test_checksum_no_vcs_name(tmpdir):
    testdata_path = str(_copy_testdata(tmpdir))
    tmpdir.join('/MyPackage/.novcs').ensure(dir=True)
    tmpdir.join('/MyPackage/.novcs/foo').write('Contents of foo')
    expected = [
        tmpdir.join('MyPackage/.novcs/foo').strpath,
        tmpdir.join('MyPackage/setup.py').strpath,
        tmpdir.join('MyPackage/MANIFEST.in').strpath,
        tmpdir.join('MyPackage/src/mypackage/__init__.py').strpath,
        tmpdir.join('MyPackage/src/mypackage/resources/style.css').strpath,
        ]
    found = list(list_directory(testdata_path))
    assert sorted(found) == sorted(expected)

def test_checksum_vcs_name(tmpdir):
    testdata_path = str(_copy_testdata(tmpdir))
    for name in VCS_NAMES:
        tmpdir.join('/MyPackage/%s' % name).ensure(dir=True)
        tmpdir.join('/MyPackage/%s/foo' % name).write('Contents of foo')
        expected = [
            tmpdir.join('MyPackage/setup.py').strpath,
            tmpdir.join('MyPackage/MANIFEST.in').strpath,
            tmpdir.join('MyPackage/src/mypackage/__init__.py').strpath,
            tmpdir.join('MyPackage/src/mypackage/resources/style.css').strpath,
            ]
        found = list(list_directory(testdata_path))
        assert sorted(found) == sorted(expected)
        tmpdir.join('/MyPackage/%s' % name).remove(rec=True)

def test_checksum_dot_file(tmpdir):
    testdata_path = str(_copy_testdata(tmpdir))
    tmpdir.join('/MyPackage/.woekie').ensure()
    expected = [
        tmpdir.join('MyPackage/.woekie').strpath,
        tmpdir.join('MyPackage/setup.py').strpath,
        tmpdir.join('MyPackage/MANIFEST.in').strpath,
        tmpdir.join('MyPackage/src/mypackage/__init__.py').strpath,
        tmpdir.join('MyPackage/src/mypackage/resources/style.css').strpath,
        ]
    found = list(list_directory(testdata_path))
    assert sorted(found) == sorted(expected)

def test_checksum_ignored_extensions(tmpdir):
    testdata_path = str(_copy_testdata(tmpdir))
    for ext in IGNORED_EXTENSIONS:
        tmpdir.join('/MyPackage/bar%s' % ext).ensure()
        expected = [
            tmpdir.join('MyPackage/setup.py').strpath,
            tmpdir.join('MyPackage/MANIFEST.in').strpath,
            tmpdir.join('MyPackage/src/mypackage/__init__.py').strpath,
            tmpdir.join('MyPackage/src/mypackage/resources/style.css').strpath,
            ]
        found = list(list_directory(testdata_path))
        assert sorted(found) == sorted(expected)
