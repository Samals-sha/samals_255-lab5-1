from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import os
import random
import string

app = Flask(__name__)

# Database file path
DATABASE = '/nfs/demo.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  # This enables name-based access to columns
    return db

def init_db():
    with app.app_context():
        db_conn_init = None # Use a distinct variable
        try:
            db_conn_init = get_db()
            db_conn_init.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL
                );
            ''')
            db_conn_init.commit()
        except sqlite3.Error as e:
            app.logger.error(f"Error during init_db: {e}") # Optional: log error
        finally:
            if db_conn_init:
                db_conn_init.close()

def generate_random_name():
    return f"User_{random.randint(1000, 99999)}"

def generate_random_phone():
    return ''.join(random.choices(string.digits, k=10))

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''
    db_conn_post = None # Connection for POST operations

    if request.method == 'POST':
        action = request.form.get('action') # Define action ONCE for the POST block

        try:
            db_conn_post = get_db() # Open connection for all POST DB operations

            if action == 'delete':
                contact_id = request.form.get('contact_id')
                if contact_id:
                    db_conn_post.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
                    db_conn_post.commit()
                    message = 'Contact deleted successfully.'
                else:
                    message = 'Error: Contact ID missing for delete.'
            
            elif action == 'add_random':
                random_name = generate_random_name()
                random_phone = generate_random_phone()
                db_conn_post.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (random_name, random_phone))
                db_conn_post.commit()
                message = f'Random contact ({random_name}) added successfully.'

            elif action == 'clear_all':
                db_conn_post.execute('DELETE FROM contacts')
                db_conn_post.commit()
                message = 'All contacts have been cleared successfully.'
            
            else:  # Default: Manual add (action might be None or an unrecognized value)
                name = request.form.get('name')
                phone = request.form.get('phone')
                if name and phone:
                    db_conn_post.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (name, phone))
                    db_conn_post.commit()
                    message = 'Contact added successfully.'
                # This condition helps distinguish a manual form submission with missing fields
                # from other scenarios where 'action' might be defined but not matched above.
                elif action is None and (name or phone): # If it's the manual add form with some input
                    message = 'Both name and phone number are required for manual entry.'
                elif action is None and not name and not phone: # If manual add form submitted empty
                    message = 'Missing name or phone number for manual entry.'
                # If 'action' has a value but didn't match any above, no specific message here unless desired.

        except sqlite3.Error as e:
            message = f"Database error: {e}"
            app.logger.error(f"Database error in POST: {e}") # Optional: log detailed error
        finally:
            if db_conn_post:
                db_conn_post.close()

    # Always display the contacts table (for GET or after POST)
    db_conn_display = None
    contacts = [] # Default to empty list
    try:
        db_conn_display = get_db()
        # It's good practice to sort the results, e.g., by ID or name
        contacts = db_conn_display.execute('SELECT * FROM contacts ORDER BY id DESC').fetchall()
    except sqlite3.Error as e:
        message = f"Error fetching contacts for display: {e}" # Inform user of display error
        app.logger.error(f"Error fetching contacts for display: {e}") # Log detailed error
    finally:
        if db_conn_display:
            db_conn_display.close()

    # Your full HTML template string
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contacts</title>
            <style>
                body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
                h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
                .container { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                form { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="text"], input[type="submit"] {
                    margin-bottom: 10px; padding: 10px; border: 1px solid #ccc; border-radius: 4px;
                    width: calc(100% - 22px); box-sizing: border-box;
                }
                input[type="submit"] { background-color: #007bff; color: white; cursor: pointer; width: auto; }
                input[type="submit"]:hover { background-color: #0056b3; }
                .message { margin-bottom: 15px; padding: 10px; border-radius: 3px; text-align: center; }
                .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
                th { background-color: #007bff; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .delete-form input[type="submit"], .clear-all-form input[type="submit"] { background-color: #dc3545; }
                .delete-form input[type="submit"]:hover, .clear-all-form input[type="submit"]:hover { background-color: #c82333; }
                .action-buttons { margin-top: 20px; padding-top: 20px; border-top: 1px dashed #ccc; }
                .action-buttons form { display: inline-block; margin-right: 10px; }
            </style>
            <script>
                function confirmClearAll() {
                    return confirm("Are you sure you want to delete ALL contacts? This action cannot be undone.");
                }
            </script>
        </head>
        <body>
            <div class="container">
                <h2>Add Contacts</h2>
                <form method="POST" action="/">
                    <label for="name">Name:</label>
                    <input type="text" id="name" name="name"> <label for="phone">Phone Number:</label>
                    <input type="text" id="phone" name="phone"><br><br>
                    <input type="submit" value="Submit"> </form>

                <div class="action-buttons">
                    <h2>Quick Actions</h2>
                    <form method="POST" action="/">
                        <input type="hidden" name="action" value="add_random">
                        <input type="submit" value="Add Random Test Contact">
                    </form>
                    <form method="POST" action="/" class="clear-all-form" onsubmit="return confirmClearAll();">
                        <input type="hidden" name="action" value="clear_all">
                        <input type="submit" value="Clear All Contacts"> </form>
                </div>

                {% if message %}
                    <p class="message {% if 'successfully' in message %}success{% elif 'required' in message or 'Missing' in message or 'Error:' in message or 'Database error:' in message %}error{% else %}success{% endif %}">{{ message }}</p>
                {% endif %}

                <h2>Contacts List</h2>
                {% if contacts %}
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Phone Number</th>
                                <th>Delete</th>
                            </tr>
                        </thead>
                        <tbody>
                        {% for contact in contacts %}
                            <tr>
                                <td>{{ contact['id'] }}</td>
                                <td>{{ contact['name'] }}</td>
                                <td>{{ contact['phone'] }}</td>
                                <td>
                                    <form method="POST" action="/" class="delete-form">
                                        <input type="hidden" name="contact_id" value="{{ contact['id'] }}">
                                        <input type="hidden" name="action" value="delete">
                                        <input type="submit" value="Delete">
                                    </form>
                                </td>
                            </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                {% else %}
                    <p>No contacts found.</p>
                {% endif %}
            </div>
        </body>
        </html>
    ''', message=message, contacts=contacts)

if __name__ == "__main__":
    db_dir = os.path.dirname(DATABASE)
    if db_dir and not os.path.exists(db_dir): # Check if db_dir is not empty
        os.makedirs(db_dir, exist_ok=True)
    init_db()  # Initialize the database and table
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)