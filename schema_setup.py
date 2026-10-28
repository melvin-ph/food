from database import get_db, init_db_indexes

def setup_schema():
    print("Setting up MongoDB collections and schema indexes for foodshare_db...")
    db = get_db()
    init_db_indexes(db)
    print("Collections and indexes ensured successfully.")

if __name__ == '__main__':
    setup_schema()
