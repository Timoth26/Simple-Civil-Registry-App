import os

from flask import *
import psycopg2
from psycopg2.extras import Json
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


def get_cursor():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return cursor


@app.route('/')
def home():
    if 'loggedin' in session:
        pass
    return redirect((url_for('login')))


@app.route('/login', methods=['GET', 'POST'])
def login():
    cursor = get_cursor()
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
    cursor.execute('SELECT * FROM personal_data WHERE "PESEL" = %s', (get_pesel_from_id(session.get('id')),))
    data = cursor.fetchone()
    return render_template('userpersonaldata.html', data=data)


@app.route('/emppersonaldata', methods=['GET', 'POST'])
def show_emp_personal_data():
    if request.method == 'POST':
        if 'pokazdane' in request.form:
            pass
        elif 'edytujdaneklienta' in request.form:
            return redirect(url_for('get_pesel'))
        elif 'pokazwnioski' in request.form:
            return redirect(url_for('show_documents'))
        elif 'pokazzgloszeniabledow' in request.form:
            pass
        elif 'zglosblad' in request.form:
            return redirect(url_for('report_error'))
        elif 'przegladajwnioski' in request.form:
            pass
        elif 'przegladajzgloszeniabledow' in request.form:
            pass
        elif 'dodajklienta' in request.form:
            pass
        elif 'zlozwniosek' in request.form:
            return redirect(url_for('apply'))

    # if session['occupation'] is not None:
    visibility = 'visible'
    # else:
    # visibility = 'hidden'

    return render_template('UrzednikPokazDane.html', data=get_data_from_db(session.get('id')), visibility=visibility)


@app.route('/getpesel', methods=['GET', 'POST'])
def get_pesel():
    if request.method == "POST":
        session['pesel'] = request.form['pesel']
        return redirect(url_for('edit_user_data'))

    return render_template('EdytujPopUPKierownik.html')


def get_id_from_pesel(pesel):
    cursor = get_cursor()
    cursor.execute('SELECT "UserID" FROM login_credentials WHERE "PESEL" = %s', (pesel,))
    pesel = cursor.fetchone()
    if pesel:
        return pesel['UserID']
    else:
        return None


@app.route('/dataedition', methods=['GET', 'POST'])
def edit_user_data():
    data = get_data_from_db(get_id_from_pesel(session['pesel']))

    if request.method == "POST":
        if 'submit' in request.form:
            if data['name'] != request.form['name'] and request.form['name'] != "":
                data['name'] = request.form['name']
            if data['surname'] != request.form['surname'] and request.form['surname'] != "":
                data['surname'] = request.form['surname']
            if session['occupation'] != 'Urzędnik' or session['occupation'] is not None:
                if data['birthdate'] != request.form['birthdate'] and request.form['birthdate'] != "":
                    data['birthdate'] = request.form['birthdate']
            if data['birthcity'] != request.form['birthcity'] and request.form['birthcity'] != "":
                data['birthcity'] = request.form['birthcity']
            if session['occupation'] != 'Urzędnik' or session['occupation'] is not None:
                if data['gender'] != request.form['gender'] and request.form['gender'] != "":
                    data['gender'] = request.form['gender']
            if data['registrationcity'] != request.form['registrationcity'] and request.form['registrationcity'] != "":
                data['registrationcity'] = request.form['registrationcity']
            if data['postalcode'] != request.form['postalcode'] and request.form['postalcode'] != "":
                data['postalcode'] = request.form['postalcode']
            if data['street'] != request.form['street'] and request.form['street'] != "":
                data['street'] = request.form['street']
            if data['No'] != request.form['houseNo'] and request.form['houseNo'] != "":
                data['No'] = request.form['houseNo']
            if data['flatNo'] != request.form['flatNo'] and request.form['flatNo'] != "":
                data['flatNo'] = request.form['flatNo']
            if data['phoneNo'] != request.form['phoneNo'] and request.form['phoneNo'] != "":
                data['phoneNo'] = request.form['phoneNo']
            if data['phoneprefix'] != request.form['phoneprefix'] and request.form['phoneprefix'] != "":
                data['phoneprefix'] = request.form['phoneprefix']
            if data['civilstatus'] != request.form['civilstatus'] and request.form['civilstatus'] != "":
                data['civilstatus'] = request.form['civilstatus']
            if data['citizenship'] != request.form['citizenship'] and request.form['citizenship'] != "":
                data['citizenship'] = request.form['citizenship']

            cursor = get_cursor()
            cursor.execute(
                'UPDATE personal_data SET "Name" = %s, "Surname" = %s, "Birthdate" = %s, "Birthplace" = %s, '
                '"Gender" = %s, "CityOfRegistration" = %s, "PostCode" = %s, "Street" = %s, "HouseNo" = %s, '
                '"FlatNo" = %s, "PhoneNo" = %s, "CallPrefix" = %s, "CivilState" = %s, "Citizenship" = %s '
                'WHERE "PESEL" = %s',
                (data['name'], data['surname'], data['birthdate'], data['birthcity'], data['gender'],
                 data['registrationcity'], data['postalcode'], data['street'], data['No'], data['flatNo'],
                 data['phoneNo'],
                 data['phoneprefix'], data['civilstatus'], data['citizenship'], data['pesel'],))

            conn.commit()

        elif 'powrot' in request.form:
            return redirect(url_for('show_emp_personal_data'))

    if session['occupation'] == 'Urzędnik' or session['occupation'] is None:
        visibility = 'hidden'
    else:
        visibility = 'visible'

    return render_template('KierownikEdytujKlienta.html',
                           data=get_data_from_db(get_id_from_pesel(session.get('pesel'))),
                           visibility=visibility)


@app.route('/apply', methods=['GET', 'POST'])
def apply():
    cursor = get_cursor()
    types = ['Akt ślubu', 'Akt zgonu', 'Akt urodzenia', 'Akt obywatelstwa']

    if request.method == 'POST':
        if 'wyslij' in request.form:
            cursor.execute('INSERT INTO documents ("Type", "AppUserID") VALUES (%s, %s)',
                           (request.form['selectlist'], session.get('id'),))
            conn.commit()
            return redirect(url_for('show_emp_personal_data'))

        elif 'powrot' in request.form:
            return redirect(url_for('show_emp_personal_data'))

    return render_template('KierownikZlozWniosek.html', types=types)


@app.route('/documents', methods=['GET', 'POST'])
def show_documents():

    headings = ("Numer Aplikacji", "Typ", "Status", "Data złożenia wniosku", "Data weryfikacji", "Data rozpatrzenia")
    cursor = get_cursor()
    cursor.execute('SELECT "ApplicationID", "Type", "Status", DATE_TRUNC(\'second\', "DateOfApplication"::timestamp), '
                   '"DateOfVerification", "DateOfConsideration" FROM documents WHERE "AppUserID" = %s',
                   (str(session['id'])))
    data = cursor.fetchall()

    if request.method == "POST":
        return redirect(url_for('show_emp_personal_data'))


    return render_template('KierownikPokazWnioski.html', headings=headings, data=data)

@app.route('/reporterror', methods=['GET', 'POST'])
def report_error():
    cursor = get_cursor()
    data = get_data_from_db(session['id'])

    if request.method == "POST":
        if 'submit' in request.form:
            new_data = request.form.to_dict()
            for i, j in new_data.copy().items():
                if j == '':
                    new_data.pop(i)
                if i == 'submit':
                    new_data.pop(i)
                elif i == 'powrot':
                    new_data.pop(i)
                elif i == 'info':
                    info = new_data[i]
                    new_data.pop(i)

            for i in data.copy().keys():
                if i not in new_data:
                    data.pop(i)

            cursor.execute('INSERT INTO data_corrections ("DataField","OldVal", "NewVal", "AppUserID", "Info") '
                           'VALUES (%s, %s, %s, %s, %s);',
                           ('; '.join(list(new_data.keys())), Json(data), Json(new_data), session['id'], str(info)))
            conn.commit()
            return redirect(url_for('show_emp_personal_data'))

        if 'powrot' in request.form:
            return redirect(url_for('show_emp_personal_data'))

    return render_template("KierownikZglosBlad.html", data=get_data_from_db(session['id']))
def get_data_from_db(id):
    cursor = get_cursor()
    cursor.execute('SELECT * FROM personal_data WHERE "PESEL" = %s', (get_pesel_from_id(id),))
    data = cursor.fetchone()
    data = {
        'pesel': data[0],
        'name': data[1],
        'surname': data[2],
        'birthdate': data[3],
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

    return data


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
        (get_pesel_from_id(user_id),))
    occupation = cursor.fetchone()
    if occupation:
        return occupation['Occupation']
    else:
        return None


def get_pesel_from_id(user_id):
    cursor = get_cursor()
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
