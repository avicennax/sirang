import inspect
import pymongo

class Sirang(object):
    def __init__(self, host='mongodb://localhost:27017'):
        self.client = MongoClient(host)
        self.dbs = {}

    def get_db(self, db_name):
        if db_name not in self.dbs.keys():
            self.dbs[db_name] = self.client.get_database(db_name)
        return self.dbs[db_name]

    def store(self, db, store, inversion=False, doc_id=None):
        db = self.get_db(db_name)
        posts = db.posts
        new_post = {}
        def store_dec(f):
            def func(*args, **kwargs):
                for param_name, param in kwargs.items():
                    if self._include(param_name, store, inversion):
                        new_post[param_name] = param
                    if doc_id:
                        new_post['_id'] = doc_id
                result = posts.insert_one(post)
                return f(*args, **kwargs)
            return func
        return store_dec

    def retrieve(self, db, retrieve):
        db = self.get_db(db_name)
        posts = db.posts
        def store_dec(f):
            def func(*args, **kwargs):
                retrieved_params = posts.find_one(filter=retrieve)
                kwargs.update(retrieved_params)
                return f(*args, **kwargs)
            return func
        return store_dec

    def _include(param_name, store_list, inversion):
        if inversion:
            return param_name not in store_list
        return param_name in store_list
