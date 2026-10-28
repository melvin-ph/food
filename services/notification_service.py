from datetime import datetime, timezone
from database import get_db, to_object_id

def create_notification(user_id, title, message, link=None, notif_type='info'):
    db = get_db()
    uid = to_object_id(user_id)
    if not uid:
        return None

    # Avoid duplicate pending notifications within a short window
    existing = db.notifications.find_one({
        'user_id': uid,
        'title': title,
        'message': message,
        'is_read': False
    })
    if existing:
        return existing['_id']

    notif_doc = {
        'user_id': uid,
        'title': title,
        'message': message,
        'link': link or '#',
        'type': notif_type,  # info, success, warning, danger
        'is_read': False,
        'created_at': datetime.now(timezone.utc)
    }
    result = db.notifications.insert_one(notif_doc)
    return result.inserted_id

def get_user_notifications(user_id, limit=20, unread_only=False):
    db = get_db()
    uid = to_object_id(user_id)
    if not uid:
        return []

    query = {'user_id': uid}
    if unread_only:
        query['is_read'] = False

    return list(db.notifications.find(query).sort('created_at', -1).limit(limit))

def get_unread_count(user_id):
    db = get_db()
    uid = to_object_id(user_id)
    if not uid:
        return 0
    return db.notifications.count_documents({'user_id': uid, 'is_read': False})

def mark_notification_read(notification_id, user_id):
    db = get_db()
    nid = to_object_id(notification_id)
    uid = to_object_id(user_id)
    if not nid or not uid:
        return False
    result = db.notifications.update_one(
        {'_id': nid, 'user_id': uid},
        {'$set': {'is_read': True, 'read_at': datetime.now(timezone.utc)}}
    )
    return result.modified_count > 0

def mark_all_notifications_read(user_id):
    db = get_db()
    uid = to_object_id(user_id)
    if not uid:
        return 0
    result = db.notifications.update_many(
        {'user_id': uid, 'is_read': False},
        {'$set': {'is_read': True, 'read_at': datetime.now(timezone.utc)}}
    )
    return result.modified_count
