import logging
import pytest
import os
import shutil
import sys
import tempfile
from subprocess import CalledProcessError, check_call

from sirang import Sirang


@pytest.fixture(scope="session", autouse=True)
def setup_server(request):
    """Setup server."""
    tmpdir = tempfile.mkdtemp()
    tmplog = os.path.join(tmpdir, 'log')
    setup_server_call = [
        'mongod', '--fork', '--logpath', tmplog, '--dbpath', tmpdir]
    try:
        check_call(setup_server_call)
        # Removing the DB directory will cause crash the Mongo daemon
        request.addfinalizer(lambda: shutil.rmtree(tmpdir))
    except OSError:
        logging.error("mongod setup failed; aborting tests")
        sys.exit(1)


@pytest.fixture(scope="session", autouse=True)
def sirang_instance():
    return Sirang()


def test_sirang(sirang_instance):
    assert '0' == sirang_instance.store('db', 'posts', {'_id': 0})
