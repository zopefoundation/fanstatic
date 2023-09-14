from fanstatic import get_library_registry
from fanstatic import set_auto_register_library
from fanstatic import set_resource_file_existence_checking
from fanstatic.core import NEEDED
from fanstatic.core import thread_local_needed_data


def pytest_runtest_setup(item):
    set_resource_file_existence_checking(False)
    set_auto_register_library(True)
    # Reset the registry before each test.
    get_library_registry().clear()
    thread_local_needed_data.__dict__.pop(NEEDED, None)


def pytest_runtest_teardown(item):
    set_resource_file_existence_checking(True)
    set_auto_register_library(False)
