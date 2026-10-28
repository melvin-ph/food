import os
import atexit
import logging
from bson import ObjectId, json_util
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import Config

logger = logging.getLogger('foodshare.db')

_db_instance = None
_is_mock = False
_mock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'local_db_dump.json')

def save_mock_db():
    global _db_instance, _is_mock
    if not _is_mock or _db_instance is None:
        return
    try:
        data = {}
        for coll_name in _db_instance.list_collection_names():
            docs = list(_db_instance[coll_name].find())
            data[coll_name] = docs
        with open(_mock_file, 'w', encoding='utf-8') as f:
            f.write(json_util.dumps(data, indent=2))
    except Exception as e:
        logger.debug(f"Error saving mock db: {e}")

def load_mock_db(mock_db):
    if not os.path.exists(_mock_file):
        return
    try:
        with open(_mock_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return
            data = json_util.loads(content)
            for coll_name, docs in data.items():
                mock_db[coll_name].drop()
                if docs:
                    mock_db[coll_name].insert_many(docs)
    except Exception as e:
        logger.debug(f"Error loading mock db: {e}")

class PersistentMockDatabaseWrapper:
    """Wraps a mongomock Database to automatically persist writes to local JSON storage."""
    def __init__(self, raw_db):
        self._raw_db = raw_db

    def __getattr__(self, name):
        attr = getattr(self._raw_db, name)
        if callable(attr) and name in ['list_collection_names', 'command', 'drop_collection']:
            return attr
        # Return a wrapped collection
        return PersistentMockCollectionWrapper(attr)

    def __getitem__(self, name):
        return PersistentMockCollectionWrapper(self._raw_db[name])

class PersistentMockCollectionWrapper:
    def __init__(self, raw_coll):
        self._raw_coll = raw_coll

    def insert_one(self, *args, **kwargs):
        res = self._raw_coll.insert_one(*args, **kwargs)
        save_mock_db()
        return res

    def insert_many(self, *args, **kwargs):
        res = self._raw_coll.insert_many(*args, **kwargs)
        save_mock_db()
        return res

    def update_one(self, *args, **kwargs):
        res = self._raw_coll.update_one(*args, **kwargs)
        save_mock_db()
        return res

    def update_many(self, *args, **kwargs):
        res = self._raw_coll.update_many(*args, **kwargs)
        save_mock_db()
        return res

    def delete_one(self, *args, **kwargs):
        res = self._raw_coll.delete_one(*args, **kwargs)
        save_mock_db()
        return res

    def delete_many(self, *args, **kwargs):
        res = self._raw_coll.delete_many(*args, **kwargs)
        save_mock_db()
        return res

    def __getattr__(self, name):
        return getattr(self._raw_coll, name)

def get_db():
    global _db_instance, _is_mock
    if _db_instance is not None:
        return _db_instance

    mongo_uri = Config.MONGO_URI
    db_name = Config.MONGO_DB_NAME

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        _db_instance = client[db_name]
        _is_mock = False
        logger.info(f"Connected to live MongoDB database '{db_name}' at {mongo_uri}")
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
        logger.warning(f"Could not connect to live MongoDB at {mongo_uri}. Using PyMongo-compatible persistent store.")
        import mongomock
        mock_client = mongomock.MongoClient()
        raw_mock = mock_client[db_name]
        load_mock_db(raw_mock)
        _is_mock = True
        _db_instance = PersistentMockDatabaseWrapper(raw_mock)
        atexit.register(save_mock_db)

    init_db_indexes(_db_instance)
    return _db_instance

def is_mock_db():
    global _is_mock
    return _is_mock

def to_object_id(id_val):
    if not id_val:
        return None
    if isinstance(id_val, ObjectId):
        return id_val
    try:
        return ObjectId(str(id_val))
    except Exception:
        return None

def init_db_indexes(db):
    try:
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("role", ASCENDING)])
        db.donations.create_index([("donor_id", ASCENDING)])
        db.donations.create_index([("status", ASCENDING)])
        db.donation_requests.create_index([("donation_id", ASCENDING)])
        db.donation_requests.create_index([("recipient_id", ASCENDING)])
        db.notifications.create_index([("user_id", ASCENDING)])
    except Exception as e:
        logger.debug(f"Index initialization note: {e}")
