import datetime
import pymongo
import subprocess
from functools import wraps


class Sirang(object):

    def init(self, host='mongodb://localhost:27017', verbose=0):
        self.dbs = {}
        self.client = pymongo.MongoClient(host)
        self.verbose = verbose
        return self

    def db_doc_count(self, db_name):
        return self.get_db(db_name).posts.count()

    def store_meta(self, db_name, doc=None, doc_id=None):
        """
        Stores experiment meta-data, e.g: git commmit info of
        executing dir, experiment exe timedate, other passed parameters.
        """
        if doc is None:
            doc = {}
       
        dt_now = str(datetime.datetime.now())
        git_commit = subprocess.check_output(["git", "describe", "--always"]).strip()
        doc.update({'exe-date': dt_now, 'git-commit': git_commit})
        if doc_id:
            doc["_id"] = doc_id
        else:
            doc["_id"] = self.db_doc_count(db_name) + 1

        res_id = self.store(db_name=db_name, raw_document=doc, store={}, inversion=True)
        return res_id

    def get_db(self, db_name):
        """
        Fetches DB object based on DB name or creates new one if not
        instantiated.
        """
        if db_name not in self.dbs.keys():
            self.dbs[db_name] = self.client.get_database(db_name)
        return self.dbs[db_name]

    def store(self, db_name, raw_document, store=None, inversion=False, doc_id=None):
        """
        Store new document through client connection
        """
        if store is None:
            store = raw_document.keys()

        db = self.get_db(db_name)
        posts = db.posts
        doc = self._doc_sub_dict(raw_document, store, inversion)

        if doc_id:
            doc['_id'] = doc_id

        result = posts.insert_one(doc)
        res_id = str(result.inserted_id)
        self._verbose_print(res_id)
        return res_id

    def retrieve(self, db_name, filter):
        """
        Fetch document based on passed filter.
        """
        db = self.get_db(db_name)
        posts = db.posts
        retrieved_doc = posts.find_one(filter=filter)
        self._verbose_print(retrieved_doc)
        return retrieved_doc

    def dstore(self, db_name, store, inversion=False, doc_id=None, store_return=False):
        """
        Decorated version of store.
        Allows user to specify which arguments to store, or to invert passed arguments.
        """
        db = self.get_db(db_name)
        posts = db.posts
        new_post = {}
        def store_dec(f):
            @wraps
            def func(*args, **kwargs):
                for param_name, param in kwargs.items():
                    if self._include(param_name, store, inversion):
                        new_post[param_name] = param
                    if doc_id:
                        new_post['_id'] = doc_id
                if store_return:
                    res_store, res = f(*args, **kwargs)
                    new_post.update(res_store)
                else:
                    res = f(*args, **kwargs)
                result = posts.insert_one(new_post)
                res_id = str(result.inserted_id)
                self._verbose_print(res_id)
                return res
            return func
        return store_dec

    def dretrieve(self, db_name, filter):
        """
        Decorated version of retrieve.
        See: retrieve.
        """
        db = self.get_db(db_name)
        posts = db.posts
        
        def retrieve_dec(f):
            def func(*args, **kwargs):
                retrieved_params = posts.find_one(filter=filter)
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
