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

def generate_random_name():
    return f"User_{random.randint(1000, 99999)}"

def generate_random_phone():
    return ''.join(random.choices(string.digits, k=10))

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ''  # Message indicating the result of the operation
if request.method == 'POST':
        action = request.form.get('action') # Get the action once
        try:
            db_conn = get_db() # Get DB connection once for the POST request if an action is expected

            if action == 'delete':
                contact_id = request.form.get('contact_id')
                if contact_id:
                    db_conn.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
                    db_conn.commit()
                    message = 'Contact deleted successfully.'
                else:
                    message = 'Error: Contact ID missing for delete action.'

            elif action == 'add_random':
                random_name = generate_random_name()
                random_phone = generate_random_phone()
                db_conn.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (random_name, random_phone))
                db_conn.commit()
                message = f'Random contact ({random_name}) added successfully.'

            elif action == 'clear_all':
                db_conn.execute('DELETE FROM contacts')
                db_conn.commit()
                message = 'All contacts have been cleared successfully.'
            
            # This 'else' corresponds to the 'if action == ...'
            # It implies that if 'action' is not one of the above, it's a manual add attempt.
            # Or, if 'action' is None (e.g., the main submit button of the add form was pressed which might not send an 'action' field)
            else: # Default action is adding a specific contact from the manual form
                name = request.form.get('name')
                phone = request.form.get('phone')

                if name and phone:
                    db_conn.execute('INSERT INTO contacts (name, phone) VALUES (?, ?)', (name, phone))
                    db_conn.commit()
                    message = 'Contact added successfully.'
                # Only show missing fields message if at least one field was attempted or if it's the default form submission
                elif request.form.get('name') is not None or request.form.get('phone') is not None: # Check if form was submitted
                    message = 'Both name and phone number are required for manual entry.'
                # If no specific action, and no name/phone, it might be an unhandled POST or page refresh after POST.
                # If no specific form was submitted with an action, and no name/phone provided, no message is needed
                # unless you want to explicitly state "No action taken."

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
    port = int(os.environ.get("PORT", 5000))
    init_db()  # Initialize the database and table
    app.run(debug=True, host='0.0.0.0', port=port)
