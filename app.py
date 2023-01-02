from flask import *
import psycopg2
import psycopg2.extras
import sys
import logging

app = Flask(__name__)

DB_HOST = "usc-bd.postgres.database.azure.com"
DB_NAME = "usc"
DB_USER = "app"
DB_PASS = "password"
DB_PORT = "5432"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)


@app.route('/')
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if user submitted form
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
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
            return redirect('index.html')
        else:
            flash('Podane błędny login lub hasło')

    return render_template('login.html')
def get_occupation(user_id):

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM employees WHERE (SELECT "PESEL" FROM login_credentials WHERE "UserID" = %s) = employees."PESEL"',
                   (user_id,))
    occupation = cursor.fetchone()
    if occupation:
        return occupation['Occupation']
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
