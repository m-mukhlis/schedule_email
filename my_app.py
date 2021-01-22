from flask import Flask
from flask_mail import Mail, Message
import sqlite3 as sql
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging


app = Flask(__name__)
mail = Mail(app)
con = sql.connect('email_database.db')

# set (sender) your email and your time zone in here:
your_email = 'your_gmail@gmail.com'
your_password = 'your_password'
your_time_zone = 8

app.config['MAIL_SERVER'] = 'smtp.gmail.com' #if your email is not gmail, set using your own mail server
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = your_email
app.config['MAIL_PASSWORD'] = your_password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

logging.basicConfig(filename="save_emails.log",
                    datefmt='%d-%m-%y %H:%M:%S',
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    level=logging.ERROR)


def email():
    """
    Function for constantly checking time and data from database.
    The constantly checking can be fulfill with the library BackgroundScheduler from APScheduler.
    This function will be called from task BackgroundScheduler.
    If there is/are email(s) that needed to be sent, the function will call function send_email with event_id as the param.
    """
    try:
        """
        You have to setting the timedelta same with your server time
        This app assume using UTC+8
        """
        utc_8 = datetime.utcnow() + timedelta(hours=your_time_zone)
        utc_8_unix = datetime.timestamp(utc_8)
        con = sql.connect('email_database.db')
        c = con.cursor()
        query = "Select event_id, timestamp FROM save_emails where is_sent='False'"
        c.execute(query)
        data = c.fetchall()
        for el in data:
            event_id = el[0]
            time_sent = el[1]
            schedule = datetime.fromisoformat(time_sent)
            schedule_unix = datetime.timestamp(schedule)
            check_time = int(schedule_unix) - int(utc_8_unix)
            if check_time < 0:
                query = "update save_emails set is_sent=? where event_id=?"
                value = ('True', event_id)
                c.execute(query, value)
                con.commit()
            elif 0 <= check_time < 30:
                query = "update save_emails set is_sent=? where event_id=?"
                value = ('True', event_id)
                c.execute(query, value)
                con.commit()
                query = "insert into sent_emails (event_id, execute_time) values (?,?)"
                value = (event_id, str(utc_8))
                c.execute(query, value)
                con.commit()
                return send_email(event_id)
            else:
                pass
    except Exception as err:
        logging.error(f"EMAIL-FUNCTION-ERROR : {str(err)}")
        pass
    finally:
        con.close()

def send_app_context(app, msg):
    try:
        with app.app_context():
            mail.send(msg)
    except Exception as err:
        logging.error(f"SEND-APP-CONTEXT : {str(err)}")
        pass

def send_email(event_id):
    """
    Function for sending email that to be triggered.
    This function will call function send_app_context for sending email asynchronously as background task.
    """
    try:
        con = sql.connect('email_database.db')
        c = con.cursor()
        c.execute("Select recipients, email_subject, email_content FROM save_emails where event_id=?", (event_id,))
        data = c.fetchone()
        recipients = data[0]
        recipients = list(recipients.split(","))
        subject = data[1]
        content = data[2]
        for user in recipients:
            msg = Message(subject, sender=your_email, recipients=[user])
            msg.body = content
            send_app_context(app, msg)
    except Exception as err:
        logging.error(f"SEND-EMAIL-ERROR : {str(err)}")
        pass
    finally:
        con.close()



"""
This task will running as background task for checking time and send the necessary email
This task will looping every 30s and will calling function email
"""
sched = BackgroundScheduler(daemon=True)
sched.add_job(email,'interval',seconds=30)
sched.start()


# import files
from routes import *


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)