import sqlite3
import os

DATABASE = '/nfs/demo.db'

def connect_db():
    """Connect to the SQLite database."""
    # Ensure the directory exists (though the PV mount should handle /nfs)
    # db_dir = os.path.dirname(DATABASE)
    # if db_dir and not os.path.exists(db_dir):
    #     print(f"Database directory {db_dir} does not exist.") # Should not happen if PV is mounted
    #     # os.makedirs(db_dir, exist_ok=True) # data-gen should not create this dir, main.py on PV should
    return sqlite3.connect(DATABASE)

def generate_test_data(num_contacts):
    """Generate test data for the contacts table."""
    print(f"Attempting to connect to database: {DATABASE}")
    db = None # Initialize
    try:
        db = connect_db()
        cursor = db.cursor()
        # Check if table exists first (optional, but good for debug)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contacts';")
        if not cursor.fetchone():
            print("ERROR in data-gen.py: 'contacts' table does not exist!")

        print(f"Generating {num_contacts} test contacts...")
        for i in range(num_contacts):
            name = f'Test Name {i}'
            phone = f'123-456-789{i}'
            print(f"Inserting: {name}, {phone}")
            cursor.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (name, phone))
        db.commit()
        print(f"{num_contacts} test contacts committed to the database.")

        # Verify insertion
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE name LIKE 'Test Name %';")
        count = cursor.fetchone()[0]
        print(f"Verification count in data-gen.py: Found {count} 'Test Name %' contacts.")
        if count != num_contacts:
            print(f"WARNING in data-gen.py: Expected {num_contacts} but found {count} matching contacts after insert.")

    except sqlite3.Error as e:
        print(f"ERROR in data-gen.py: SQLite error: {e}")
    except Exception as e:
        print(f"ERROR in data-gen.py: An unexpected error occurred: {e}")
    finally:
        if db:
            db.close()
            print("Database connection closed in data-gen.py.")

if __name__ == '__main__':
    generate_test_data(10)