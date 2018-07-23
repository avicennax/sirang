import datetime
import pymongo
import subprocess
from functools import wraps


class Sirang():
    """
    Sirang contains effectively 3 core calls:
        - store_meta
        - store/dstore
        - retrieve/dretrieve

    For `store` and `retrieve` there are both decorated and
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

    def store_meta(self, db_name, collection, doc=None, doc_id=None):
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
            doc["_id"] = self.collection_doc_count(db_name) + 1

        # Calls store with pre-built meta-data document
        res_id = self.store(
            db_name=db_name, collection_name=collection, raw_document=doc,
            store={}, inversion=True)

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
        db = self.get_db(db_name)
        collection = db[collection_name]
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
        Fetch a single document based on passed filter.

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
        retrieved_doc : dict or None
            If document match is found, a dictionary of the document's
            key/value pairs is returned, otherwise None..

        """
        db = self.get_db(db_name)
        collection = db[collection_name]
        retrieved_doc = collection.find_one(filter=filter_criteria)
        self._verbose_print(retrieved_doc)

        return retrieved_doc

    def dstore(
        self, db_name, collection_name, keep=None, inversion=False,
        doc_id=None, store_return=False):
        """
        Decorated version of store.
        See: store.
        """
        db = self.get_db(db_name)
        collection = db[collection_name]
        new_post = {}

        def store_dec(f):
            def func(**kwargs):
                # If keep is overwritten in the function body
                # then keep will be removed from the it's closure's
                # free variables and will yield a reference before
                # assignment error.
                keepers = keep if keep else kwargs.keys()
                for param_name, param in kwargs.items():
                    if self._include(param_name, keepers, inversion):
                        new_post[param_name] = param
                    if doc_id:
                        new_post['_id'] = doc_id
                if store_return:
                    res_store, res = f(**kwargs)
                    new_post.update(res_store)
                else:
                    res = f(**kwargs)
                import ipdb; ipdb.set_trace() 
                result = collection.insert_one(new_post)
                res_id = str(result.inserted_id)
                self._verbose_print(res_id)
                return res
            return func
        return store_dec

    def dretrieve(self, db_name, collection_name, filter_criteria):
        """
        Decorated version of retrieve.
        See: retrieve.
        """
        db = self.get_db(db_name)
        collection = db[collection]

        def retrieve_dec(f):
            def func(*args, **kwargs):
                retrieved_params = collection.find_one(filter=filter_criteria)
                self._verbose_print(retrieved_params)
                kwargs.update(retrieved_params)
                return f(*args, **kwargs)
            return func
        return retrieve_dec

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
            print(pstr)
