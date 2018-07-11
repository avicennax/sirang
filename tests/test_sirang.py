import os
import sys
from subprocess import CalledProcessError, check_call

from sirang import Sirang


@pytest.fixture(scope="session", autouse=True)
def setup_server():
    """Setup server."""
    setup_server_call = ['mongod', '--fork', '--logpath', tmpdir, '--db-path', tmpdir]
    try:
        check_call(setup_server_call)
    except CalledProcessError:
        logging.error("mongod setup failed; aborting tests")
        sys.exit(1)


@pytest.fixture(scope="session", autouse=True)
def sirang_instance():
    return Sirang()


def test_sirang(sirang_instance):
    assert 0 == sirang_instance('db', 'posts', {})
