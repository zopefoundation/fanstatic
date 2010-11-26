import pprint
import shutil
from pkg_resources import resource_filename

import fanstatic

from fanstatic.checksum import list_directory, checksum

def _copy_testdata(tmpdir):
    src = resource_filename('fanstatic', 'testdata/MyPackage')
    dst = tmpdir / 'MyPackage'
    shutil.copytree(src, str(dst))
    return dst

def test_list_directory(tmpdir):
    testdata_path = str(_copy_testdata(tmpdir))
    prefix = str(tmpdir)

    expected = [
        prefix+'/MyPackage/setup.py',
        prefix+'/MyPackage/MANIFEST.in',
        prefix+'/MyPackage/src/mypackage/__init__.py',
        prefix+'/MyPackage/src/mypackage/resources/style.css',
        ]
    found = list(list_directory(testdata_path))
    assert sorted(found) == sorted(expected)
    
def test_checksum(tmpdir):
    testdata_path = str(_copy_testdata(tmpdir))
    assert checksum(testdata_path) == '4f671f095fadfec05e79df3fe2fe9a8a'
    
