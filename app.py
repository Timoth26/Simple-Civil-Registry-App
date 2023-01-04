import os

from flask import *
import psycopg2
import psycopg2.extras
import sys
import logging
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

DB_HOST = "usc-bd.postgres.database.azure.com"
DB_NAME = "usc"
DB_USER = "app"
DB_PASS = "password"
DB_PORT = "5432"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)

def create_connection():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return cursor

@app.route('/')
def home():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    if 'loggedin' in session:
        pass
    return redirect((url_for('login')))

@app.route('/login', methods=['GET', 'POST'])
def login():
    cursor = create_connection()
    error = ""
    # Check if user submitted form
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if account exists in db
        cursor.execute('SELECT * FROM login_credentials WHERE "Login" = %s AND "Password" = crypt(%s, "Password")',
                       (username, password,))
        account = cursor.fetchone()

        # If account exist (with correct password) run session
        if account:
            # Create session data
            session['loggedin'] = True
            session['id'] = account['UserID']
            session['occupation'] = get_occupation(account['UserID'])

            if session['occupation'] is None:
                return redirect(url_for('show_user_personal_data'))

            return redirect(url_for('show_emp_personal_data'))

        else:
            error = 'Podano błędny login lub hasło'

    return render_template('index.html', error=error)


def logout_user():
    session['loggedin'] = False
    session['id'] = None
    session['occupation'] = None


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)


@app.route('/userpersonaldata')
def show_user_personal_data():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM personal_data WHERE "PESEL" = %s', (get_pesel(session.get('id')),))
    data = cursor.fetchone()
    return render_template('userpersonaldata.html', data=data)

@app.route('/emppersonaldata', methods=['GET', 'POST'])
def show_emp_personal_data():
    cursor = create_connection()
    cursor.execute('SELECT * FROM personal_data WHERE "PESEL" = %s', (get_pesel(session.get('id')),))
    data = cursor.fetchone()
    data = {
        'pesel': data[0],
        'name': data[1],
        'surname': data[2],
        'birthday': data[3],
        'birthcity': data[4],
        'gender': data[5],
        'registrationcity': data[6],
        'postalcode': data[7],
        'street': data[8],
        'No': data[9],
        'flatNo': data[10],
        'phoneNo': data[11],
        'phoneprefix': data[12],
        'civilstatus': data[13],
        'citizenship': data[14]
    }

    for i, j in data.items():
        if j is None:
            data[i] = '-'

    if request.method == 'POST':
        if 'pokazdane' in request.form:
            pass
        elif 'edytujdaneklienta' in request.form:
            return redirect(url_for('login'))
            #return render_template('index.html', error="")
        elif 'pokazwnioski' in request.form:
            pass
        elif 'pokazzgloszeniabledow' in request.form:
            pass
        elif 'zglosblad' in request.form:
            pass
        elif 'przegladajwnioski' in request.form:
            pass
        elif 'przegladajzgloszeniabledow' in request.form:
            pass
        elif 'dodajklienta' in request.form:
            pass
        elif 'zlozwniosek' in request.form:
            pass

    return render_template('UrzednikPokazDane.html', data=data)

@app.route('/edycjadanych', methods=['GET', 'POST'])
def edit_user_data():
    return render_template('index.html', error="")
@app.route('/userapplication')
def user_application():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    application = request.form['application']

    cursor.execute('INSERT INTO documents ("Type", "AppUserID") VALUES (%s, %s)', (application, session.get('id')))
    return render_template('userapplication.html')


def get_occupation(user_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(
        'SELECT * FROM employees WHERE %s = employees."PESEL"',
        (get_pesel(user_id),))
    occupation = cursor.fetchone()
    if occupation:
        return occupation['Occupation']
    else:
        return None


def get_pesel(user_id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT "PESEL" FROM login_credentials WHERE "UserID" = %s', (user_id,))
    pesel = cursor.fetchone()
    if pesel:
        return pesel['PESEL']
    else:
        return None


@app.route('/usermenu')
def user_menu():
    return render_template('usermenu.html')


@app.route('/officialmenu')
def official_menu():
    return render_template('officialmenu.html')


@app.route('/mayormenu')
def mayor_menu():
    return render_template('mayormenu.html')


if __name__ == '__main__':
    app.run(debug=True)
