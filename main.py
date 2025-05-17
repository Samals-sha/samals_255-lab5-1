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
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            );
        ''')
        db.commit()
        db.close()

def generate_random_name():
    return f"User_{random.randint(1000, 99999)}"

def generate_random_phone():
    return ''.join(random.choices(string.digits, k=10))

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''  # Message indicating the result of the operation
    if request.method == 'POST':
        action = request.form.get('action')
        # Check if it's a delete action
        if request.form.get('action') == 'delete':
            contact_id = request.form.get('contact_id')
            db = get_db()
            db.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
            db.commit()
            db.close() 
            message = 'Contact deleted successfully.'
        elif action == 'add_random':
            db = get_db()
            random_name = generate_random_name()
            random_phone = generate_random_phone()
            db.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (random_name, random_phone))
            db.commit()
            db.close()
            message = f'Random contact ({random_name}) added successfully.'
        elif action == 'clear_all': # New action to clear all contacts
            db = get_db()
            db.execute('DELETE FROM contacts')
            db.commit()
            db.close()
            message = 'All contacts have been cleared successfully.'
        else:
            name = request.form.get('name')
            phone = request.form.get('phone')
            if name and phone:
                db = get_db()
                db.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (name, phone))
                db.commit()
                db.close()
                message = 'Contact added successfully.'
            else:
                message = 'Missing name or phone number.'

    # Always display the contacts table
    db = get_db()
    contacts = db.execute('SELECT * FROM contacts').fetchall()
    # Display the HTML form along with the contacts table
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Contacts</title>
            <script>
        function confirmClearAll() {
        return confirm("Are you sure you want to delete ALL contacts? This action cannot be undone.");
            }
        </script>
        </head>
        <body>
            <h2>Add Contacts</h2>
            <form method="POST" action="/">
                <label for="name">Name:</label><br>
                <input type="text" id="name" name="name" required><br>
                <label for="phone">Phone Number:</label><br>
                <input type="text" id="phone" name="phone" required><br><br>
                <input type="submit" value="Submit">
            </form>
            <div class="action-buttons">
                <h2>Quick Actions</h2>
                <form method="POST" action="/">
                    <input type="hidden" name="action" value="add_random">
                    <input type="submit" value="Add Random Test Contact">
                </form>
                <form method="POST" action="/" class="clear-all-form" onsubmit="return confirmClearAll();">
                    <input type="hidden" name="action" value="clear_all">
                    <input type="submit" value="Clear All Contacts" style="background-color: #dc3545;">
                </form>
            </div>
            <p>{{ message }}</p>
            {% if contacts %}
                <table border="1">
                    <tr>
                        <th>Name</th>
                        <th>Phone Number</th>
                        <th>Delete</th>
                    </tr>
                    {% for contact in contacts %}
                        <tr>
                            <td>{{ contact['name'] }}</td>
                            <td>{{ contact['phone'] }}</td>
                            <td>
                                <form method="POST" action="/">
                                    <input type="hidden" name="contact_id" value="{{ contact['id'] }}">
                                    <input type="hidden" name="action" value="delete">
                                    <input type="submit" value="Delete">
                                </form>
                            </td>
                        </tr>
                    {% endfor %}
                </table>
            {% else %}
                <p>No contacts found.</p>
            {% endif %}
        </body>
        </html>
    ''', message=message, contacts=contacts)

if __name__ == "__main__":
    db_dir = os.path.dirname(DATABASE)
    if db_dir and not os.path.exists(db_dir): # Check if db_dir is not empty
        os.makedirs(db_dir, exist_ok=True)
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)