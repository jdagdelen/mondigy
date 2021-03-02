import os
import json
import time
import prodigy
from pymongo import MongoClient, ASCENDING
from prodigy.util import TASK_HASH_ATTR, INPUT_HASH_ATTR

class MongoDatabase:

    def __init__(self, config_data):
        """
        Configures a pymongo database connection from a config data directory.
        Alternatively, if no config data is provided, it will use environment variables.

        Args:
            config_data (dict): dictionary containing database config info

        """
        if "mongo_uri" in config_data and config_data["mongo_uri"]:
            client = MongoClient(config_data["mongo_uri"])
        else:
            MONGO_HOSTNAME = config_data.get("host", None) or os.environ['MONGO_HOSTNAME']
            MONGO_DB = config_data.get("database", None) or os.environ['MONGO_DB']
            MONGO_USERNAME = config_data.get("user", None) or os.environ['MONGO_USERNAME']
            MONGO_PASSWORD = config_data.get("password", None) or os.environ['MONGO_PASSWORD']
            MONGO_AUTHENTICATION_DB = config_data.get("auth_source", None) or os.environ['MONGO_AUTHENTICATION_DB']
            client = MongoClient(host=MONGO_HOSTNAME,
                                 username=MONGO_USERNAME,
                                 password=MONGO_PASSWORD,
                                 authSource=MONGO_AUTHENTICATION_DB)

        self.db = client[MONGO_DB]


class AnnotationDatabase(object):

    def __init__(self, display_id='mongodb', display_name="Custom MongoDB Database", db=None):

        config = prodigy.get_config()
        config_data = config["db_settings"]["mongodb"]["annotations_db"]

        # if not (config_data and config_data is not {}):
        #     raise AssertionError("AnnotationDatabases cannot be initialized without config file data.")

        self.mdb = MongoDatabase(config_data).db
        self.db_id = config_data.get("display_id", display_id)
        self.db_name = config_data.get("display_name", display_name)

        # Prodigy-related collections are prefixed by `_p` and there are 3 collections per dataset.
        # e.g. _p.my_NER_task.dataset, _p.my_NER_task.examples, _p.my_NER_task.links
        self.dataset_collection_name = f'_p.dataset'
        self.example_collection_name = f'_p.examples'
        self.link_collection_name = f'_p.links'

        # Check for existing dataset. If it doesn't exist, create it.
        if any(c not in self.datasets for c in [self.dataset_collection_name,
                                       self.example_collection_name,
                                       self.link_collection_name]):
            self._initialize_new()
        else:
            self._load_collections()


    def _load_collections(self):
        """
        Loads/creates necessary collections

        """
        self.dataset_collection = self.mdb[self.dataset_collection_name]
        self.example_collection = self.mdb[self.example_collection_name]
        self.link_collection = self.mdb[self.link_collection_name]


    def _initialize_new(self):
        """
        Initializes the collections and indices used for a new dataset.

        """

        self._load_collections()

        self.dataset_collection.create_index('name', unique=True)
        self.dataset_collection.create_index([('created', ASCENDING)])
        self.dataset_collection.create_index('session')

        self.example_collection.create_index('input_hash')
        self.example_collection.create_index('task_hash')

        self.link_collection.create_index('dataset_id')
        self.link_collection.create_index('example_id')


    @property
    def db(self):
        return None

    def __len__(self):
        return len(self.datasets)

    def __contains__(self, name):
        return self.dataset_collection.find_one({"name": name}) is not None

    @property
    def datasets(self):
        possible_collections = self.mdb.list_collection_names()
        return [s.replace("_p.", "").replace(".dataset", "") for s in possible_collections if "_p." in s and ".dataset" in s]
        # return [x.name
        #         for x in self.dataset_collection.find(
        #         {'session': False}).sort([('created', ASCENDING)])]

    @property
    def sessions(self):
        return [x.name
                for x in self.dataset_collection.find(
                {'session': True}).sort([('created', ASCENDING)])]

    def close(self):
        pass

    def reconnect(self):
        pass

    def get_examples(self, ids, by="task_hash"):
        try:
            ids = list(ids)
        except TypeError:
            ids = [ids]
        return [json.loads(x['content'])
                for x in self.example_collection.find({by: ids})]

    def get_meta(self, name):
        doc = self.dataset_collection.find_one({'name': name})
        if doc is None:
            return None
        meta = json.loads(doc['meta'])
        meta['created'] = doc['created']
        return meta

    def get_sessions_examples(self, session_ids=None):
        if session_ids is None or len(session_ids) == 0:
            raise ValueError("One or more sessions are required")

        id_to_session = {}
        for s in self.dataset_collection.find({'name': {'$in': session_ids}}):
            id_to_session[s['_id']] = s['name']
        links = {}
        for link in self.link_collection.find({'dataset_id': {'$in': list(id_to_session.keys())}}):
            links[link['example_id']] = id_to_session[link['_id']]
        examples = []
        for eg in self.example_collection.find({'_id': {'$in': list(links.keys())}}):
            example = json.loads(eg['content'])
            example["session_id"] = links[eg['_id']]
            examples.append(example)
        return examples

    def count_dataset(self, name, session=False):
        dataset = self.dataset_collection.find_one({'name': name, 'session': session})
        if dataset is None:
            raise ValueError

        return self.link_collection.find({'dataset_id': dataset['_id']}).count()

    def get_dataset(self, name, default=None, session=False):
        dataset = self.dataset_collection.find_one({'name': name, 'session': session})
        if dataset is None:
            return default

        example_ids = [x['example_id'] for x in self.link_collection.find({'dataset_id': dataset['_id']})]
        return [json.loads(x['content']) for x in self.example_collection.find({'_id': {'$in': example_ids}})]

    def get_dataset_page(self, name, page_number: int, page_size: int):
        dataset = self.dataset_collection.find_one({'name': name})
        if dataset is None:
            return [], -1

        query = self.link_collection.find({'dataset_id': dataset['_id']})
        count = query.count()

        page = query.skip(page_number - 1 if page_number > 0 else 0).limit(page_size)
        examples = self.example_collection.find({'_id': [x['example_id'] for x in page]})
        examples = [{
            "id": str(x['_id']),
            "content": json.loads(x['content']),
            "input_hash": x['input_hash'],
            "task_hash": x['task_hash'],
        } for x in examples]
        return examples, count

    def get_input_hashes(self, *names):
        example_ids = self.dataset_collection.aggregate([
            {'$match': {'name': {'$in': names}}},
            {'$lookup': {
                'from': self.link_collection_name,
                'localField': '_id',
                'foreignField': 'dataset_id',
                'as': 'links'
            }}
        ])
        example_ids = sum(([y['example_id'] for y in x['links']] for x in example_ids), [])
        return set(x['input_hash'] for x in self.example_collection.find({'_id': {'$in': example_ids}}))

    def get_task_hashes(self, *names):
        example_ids = self.dataset_collection.aggregate([
            {'$match': {'name': {'$in': names}}},
            {'$lookup': {
                'from': self.link_collection_name,
                'localField': '_id',
                'foreignField': 'dataset_id',
                'as': 'links'
            }}
        ])
        example_ids = sum(([y['example_id'] for y in x['links']] for x in example_ids), [])
        return set(x['task_hash'] for x in self.example_collection.find({'_id': {'$in': example_ids}}))

    def add_dataset(self, name, meta={}, session=False):
        if any([char in name for char in (",", " ")]):
            raise ValueError("Dataset name can't include commas or whitespace")
        doc = self.dataset_collection.find_one({'name': name})
        if doc is not None:
            return doc
        else:
            self.dataset_collection.insert_one({
                'name': name,
                'meta': json.dumps(meta),
                'session': session,
                'created': int(time.time()),
            })
            return self.dataset_collection.find_one({'name': name})

    def add_examples(self, examples, datasets=tuple()):
        examples = [
            {
                'input_hash': x[INPUT_HASH_ATTR],
                'task_hash': x[TASK_HASH_ATTR],
                'content': json.dumps(x)
            } for x in examples
        ]
        result = self.example_collection.insert_many(examples)
        ids = result.inserted_ids

        if type(datasets) is not tuple and type(datasets) is not list:
            raise ValueError(f"Datasets must be a tuple or list, not: {type(datasets)}")
        for dataset in datasets:
            self.link(dataset, ids)

    def link(self, dataset_name, example_ids):
        dataset = self.add_dataset(dataset_name)
        links = [{'example_id': x, 'dataset_id': dataset['_id']} for x in example_ids]
        self.link_collection.insert_many(links)

    def unlink(self, dataset):
        # Don't allow to remove examples
        raise NotImplementedError()
        # dataset = collection_dataset.find_one({'name': dataset})
        # if dataset is None:
        #     return
        # link_collection.delete_many({'dataset_id': dataset['_id']})

    def drop_dataset(self, name, batch_size=None):
        # Don't allow to remove examples
        raise NotImplementedError()
        # dataset = collection_dataset.find_one({'name': name})
        # if dataset is None:
        #     return
        # example_collection.delete_many(
        #     {'_id': {
        #         '$in': [x['example_id']
        #                 for x in link_collection.find({'dataset_id': dataset['_id']})]}})
        # link_collection.delete_many({'dataset_id': dataset['_id']})
        # collection_dataset.delete_many({'name': name})

    def drop_examples(self, ids, by="task_hash"):
        # Don't allow to remove examples
        raise NotImplementedError()
        # try:
        #     ids = list(ids)
        # except TypeError:
        #     ids = [ids]
        # example_ids = [x['_id'] for x in example_collection.find({by: ids})]
        # example_collection.delete_many({'_id': {'$in': example_ids}})
        # link_collection.delete_many({'example_id': {'$in': example_ids}})

    def save(self):
        pass

    def export_session(self, session_id):
        raise NotImplementedError()

    def trash_session(self, session_id=None):
        raise NotImplementedError()

    def add_to_trash(self, examples, base_path: str):
        raise NotImplementedError()

    def add_to_exports(self, examples, base_path: str):
        raise NotImplementedError()

    def write_examples(self, examples, folder_name: str, file_base: str):
        raise NotImplementedError()

    def export_sessions(self, session_ids, export_name):
        raise NotImplementedError()

    def trash_sessions(self, session_ids, export_name):
        raise NotImplementedError()

    def export_collection(self, sessions_ids_dict, collection_name):
        raise NotImplementedError()

    def trash_collection(self, sessions_ids_dict, collection_name):
        raise NotImplementedError()

mongodb = AnnotationDatabase()