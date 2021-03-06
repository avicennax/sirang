"""
base.py

Contains core Sirang experiment logger class.
"""

import datetime
import logging
import subprocess

import pymongo


class Sirang():
    """
    Sirang contains effectively 3 core calls:
        - store_meta
        - store/dstore
        - retrieve

    For `store` there are both decorated and
    non-decorated calls, with the decorated calls being pre-fixed
    by 'd'.
    """

    def __init__(self, uri='mongodb://localhost:27017', verbose=0):
        """
        Establish connection to Mongo Server.

        Parameters
        ----------
        host : str
            URI string to connect to Mongo server
        verbose : int
            Specifies verbosity level
        """
        self.dbs = {}
        self.client = pymongo.MongoClient(uri)
        self.verbose = verbose

    def collection_doc_count(self, db_name, collection_name):
        """Get total number of documents from a collection in a DB."""
        return self.get_db(db_name)[collection_name].count()

    def store_meta(self, db_name, collection_name, doc=None, doc_id=None):
        """
        Stores experiment meta-data, e.g: git commmit info of
        executing dir, experiment exe timedate, other passed parameters.

        Parameters
        ----------
        db_name : str
            Name of database to connect to, if it doesn't exist, it
            is created.
        doc : dict
            Key/values pairs to be stored in document saved to db_name.
        doc_id : _
            Unique id key for document to be stored, must be unique
            across collection.

        Returns
        -------
        res_id : str
            Document id of newly created document.

        """
        if doc is None:
            doc = {}

        # Fill doc with meta-data values
        dt_now = str(datetime.datetime.now())
        git_commit = subprocess.check_output(
            ["git", "describe", "--always"]).strip()
        doc.update({'exe-date': dt_now, 'git-commit': git_commit})
        if doc_id:
            doc["_id"] = doc_id
        else:
            doc["_id"] = self.collection_doc_count(db_name, collection_name) + 1

        # Calls store with pre-built meta-data document
        res_id = self.store(
            db_name=db_name, collection_name=collection_name, raw_document=doc,
            keep={}, inversion=True)

        return res_id

    def get_db(self, db_name):
        """
        Fetches DB object based on DB name or creates new one if not
        instantiated.

        Primarily intended to be used internally as to abstract away
        low level pymongo calls.

        Parameters
        ----------
        db_name : str
            Mongo database name.

        Returns
        -------
        pymongo.database.Database

        """
        if db_name not in self.dbs.keys():
            self.dbs[db_name] = self.client.get_database(db_name)
        return self.dbs[db_name]

    def store(
            self, db_name, collection_name, raw_document, keep=None,
            inversion=False, doc_id=None):
        """
        Store new document through client connection.

        Parameters
        ----------
        db_name : str
            Mongo database name; database is created if it does
            not already exist.
        collection_name : str
            Name of collection in database: `db_name`.
            Collection is created if it does not already exist.
        raw_document : dict
            Key/pairs values to be stored in new document.
        keep : list-like, optional
            List of keys in `raw_document` to keep.
            If None, keep all items.
        inversion : bool, optional
            Specifies whether to invert keys in `keep`,
            e.g: calling `store` with in these args:
                >> raw_document = {'x': 0, 'y': 1},
                >> keep = ['x']
                >> inversion = True
           Would only store the document with one key/pair: {'y': 1}.

        Returns
        -------
        res_id : str
            Document id of newly created document.

        """
        if keep is None:
            keep = raw_document.keys()

        # Fetch database and collection to store document in.
        db_instance = self.get_db(db_name)
        collection = db_instance[collection_name]
        doc = self._doc_sub_dict(raw_document, keep, inversion)

        # Set unique document ID if not defined.
        if doc_id:
            doc['_id'] = doc_id

        # Insert in DB/collection
        result = collection.insert_one(doc)
        res_id = str(result.inserted_id)
        self._verbose_print(res_id)

        return res_id

    def retrieve(self, db_name, collection_name, filter_criteria):
        """
        Fetches all documents matching a passed filter.

        Parameters
        -----------
        db_name : str
            Mongo database name; database is created if it does
            not already exist.
        collection_name : str
            Name of collection in database: `db_name`.
            Collection is created if it does not already exist.
        filter_criteria : dict
            Dictionary of key/pairs to match documents in DB/collection
            against

        Returns
        -------
        retrieved_docs : list
            A list of all the documents that match the passed criteria.
        """
        db_instance = self.get_db(db_name)
        collection = db_instance[collection_name]
        retrieved_docs = collection.find(filter=filter_criteria)
        self._verbose_print(retrieved_docs)

        return [doc for doc in retrieved_docs]

    def dstore(
            self, db_name, collection_name, keep=None, inversion=False,
            store_return=False, doc_id_template=None, id_counter=0):
        """
        Decorated version of store.
        See: store.

        Parameters
        ----------
        doc_id_template : str (optional)
            Unformatted v3. style string with one unnamed argument,
            e.g: 'doc-id-{}'. Everytime the function is called, the
            id_counter parameter is incremented and used to format
            the doc_id_template string, which is used as the stored
            document's '_id' unique key.
        id_counter : int (optional)
            Starting value for counter described above.
        """
        db_instance = self.get_db(db_name)
        collection = db_instance[collection_name]

        def store_dec(dec_func):
            def func(**kwargs):
                new_post = {}
                nonlocal keep, id_counter
                keep = keep if keep else kwargs.keys()
                for param_name, param in kwargs.items():
                    if self._include(param_name, keep, inversion):
                        new_post[param_name] = param
                if doc_id_template:
                    new_post['_id'] = doc_id_template.format(id_counter)
                    id_counter += 1
                if store_return:
                    res_store, res = dec_func(**kwargs)
                    new_post.update(res_store)
                else:
                    res = dec_func(**kwargs)
                result = collection.insert_one(new_post)
                res_id = str(result.inserted_id)
                self._verbose_print(res_id)
                return res
            return func
        return store_dec

    def _include(self, param_name, store_list, inversion):
        """
        Checks whether to include parameter for storage based
        on inversion flag and passed store list.
        """
        if inversion:
            return param_name not in store_list
        return param_name in store_list

    def _doc_sub_dict(self, raw_doc, store, inversion):
        if inversion:
            return {key: pair for key, pair in raw_doc.items() if key not in store}
        return {key: pair for key, pair in raw_doc.items() if key in store}

    def _verbose_print(self, pstr):
        if self.verbose == 1:
            logging.info(pstr)
