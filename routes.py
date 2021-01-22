import sqlite3 as sql
from my_app import app
from flask import render_template, request

# connect to email_database.sq (database will be created, if not exist)
con = sql.connect('email_database.db')
con.execute('CREATE TABLE IF NOT EXISTS save_emails (event_id INTEGER PRIMARY KEY AUTOINCREMENT,'
            + 'recipients TEXT, email_subject TEXT, email_content TEXT, timestamp TEXT, is_sent TEXT DEFAULT False)')

con.execute('CREATE TABLE IF NOT EXISTS sent_emails (id INTEGER PRIMARY KEY AUTOINCREMENT,'
            + 'event_id INTEGER, execute_time TEXT, FOREIGN KEY (event_id) REFERENCES save_emails(event_id))')


con.close()


# home page
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/save_emails', methods=['GET', 'POST'])
def save_emails():
    if request.method == 'GET':
        # send the form
        return render_template('save_emails.html')
    else: # request.method == 'POST':
        # read data from the form and save in variable
        recipients = request.form['recipients']
        email_subject = request.form['email_subject']
        email_content = request.form['email_content']
        timestamp = request.form['timestamp']

        # store in database
        try:
            con = sql.connect('email_database.db')
            c = con.cursor()
            c.execute("INSERT INTO save_emails (recipients, email_subject, email_content, timestamp) VALUES (?,?,?,?)",
                (recipients, email_subject, email_content, timestamp))
            con.commit()
            return render_template('createThanks.html')
        except con.Error as err:
            # then display the error in 'database_error.html' page
            return render_template('database_error.html', error=err)
        finally:
            con.close()