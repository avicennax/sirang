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


def test_meta_funcs(sirang_instance):
    """Test meta_store and other meta functions."""
    # Declare database/collection names
    db = 'db'
    collection = 'meta'

    import pymongo.database

    # Store test documents
    assert sirang_instance.store_meta(db, collection, doc={}, doc_id=1) == '1'
    assert sirang_instance.store_meta(db, collection, {})

    # Test meta-functions
    assert sirang_instance.collection_doc_count(db, collection) == 2
    assert isinstance(sirang_instance.get_db(db), pymongo.database.Database)


def test_store_and_retrieve(sirang_instance):
    """Test store and retrieve functions."""
    # Declare database/collection names
    db = 'db'
    collection = 'store_and_retrieve'

    # Store tests
    assert sirang_instance.store(db, collection, {'_id': 0}) == '0'
    assert sirang_instance.store(db, collection, {'test': 'x', 'unique': 2})
    assert sirang_instance.store(db, collection, {'test': 'x', 'unique': 1})

    # Retrieve tests
    retrieved_docs = sirang_instance.retrieve(
        db, collection, filter_criteria={'test': 'x'})

    assert isinstance(retrieved_docs, list)
    assert len(retrieved_docs) == 2
    assert isinstance(retrieved_docs[0], dict)

    only_one = sirang_instance.retrieve(
        db, collection, filter_criteria={'test': 'x', 'unique': 1})

    assert isinstance(only_one, list)
    assert len(only_one) == 1
    assert only_one[0]['unique'] == 1


def test_store_decorator(sirang_instance):
    """Test dstore"""
    db = 'dstore'
    collection = 'test'

    def test_func(arg1, arg2, arg3, arg4):
        return arg2

    # Test inversions
    no_invert = sirang_instance.dstore(
        db, collection, keep=['arg1', 'arg2'], inversion=False,
        doc_id_template='~invert', store_return=False)(test_func)

    invert = sirang_instance.dstore(
        db, collection, keep=['arg1', 'arg2'], inversion=True,
        doc_id_template='invert', store_return=False)(test_func)

    a, b, c, d = range(4)

    assert no_invert(arg1=a, arg2=b, arg3=c, arg4=d) == b
    assert invert(arg1=a, arg2=b, arg3=c, arg4=d) == b

    no_invert_doc = sirang_instance.retrieve(
        db, collection, filter_criteria={'_id': '~invert'})[0]

    invert_doc = sirang_instance.retrieve(
        db, collection, filter_criteria={'_id': 'invert'})[0]

    assert 'arg1' in no_invert_doc.keys()
    assert 'arg2' in no_invert_doc.keys()
    assert 'arg3' not in no_invert_doc.keys()
    assert 'arg4' not in no_invert_doc.keys()

    assert 'arg1' not in invert_doc.keys()
    assert 'arg2' not in invert_doc.keys()
    assert 'arg3' in invert_doc.keys()
    assert 'arg4' in invert_doc.keys()

    # Test store_return=True and doc_id_template != None
    test_key = 'x'
    counter = 5

    def store_returns_func(arg1, arg2, arg3, arg4):
        return {test_key: arg2}, arg3

    ret_store = sirang_instance.dstore(
        db, collection, keep=['arg1', 'arg2'], inversion=False,
        doc_id_template="res_store_{}", id_counter=counter,
        store_return=True)(store_returns_func)

    a, b, c, d = range(4)

    assert ret_store(arg1=a, arg2=b, arg3=c, arg4=d) == c
    store_return_doc = sirang_instance.retrieve(
        db, collection,
        filter_criteria={'_id': "res_store_{}".format(counter)})[0]

    assert test_key in store_return_doc.keys()
    assert store_return_doc[test_key] == b
