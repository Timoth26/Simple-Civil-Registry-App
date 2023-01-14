import os
from flask import *
import psycopg2
from psycopg2.extras import Json
import random
from datetime import datetime


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

            try:
                cursor.execute('INSERT INTO login_history ("UserID", "LoginTime", "ActivityStatus") VALUES (%s, now(), %s)',
                               (str(account['UserID']), 'Logged'))
                conn.commit()
            except Exception as error:
                session['Exception'] = str(error)
                return redirect(url_for('server_error'))

            return redirect(url_for('show_personal_data'))

        else:
            error = 'Podano błędny login lub hasło'

    return render_template('index.html', error=error)


def logout_user():

    try:
        cursor = get_cursor()
        cursor.execute('INSERT INTO login_history ("UserID", "LoginTime", "ActivityStatus") '
                       'VALUES (%s, now(), %s)', (session['id'], 'Logged Out'))
        conn.commit()
    except Exception as error:
        session['Exception'] = str(error)
        return redirect(url_for('server_error'))

    session['loggedin'] = False
    session['id'] = None
    session['occupation'] = None


@app.route('/emppersonaldata', methods=['GET', 'POST'])
def show_personal_data():
    if request.method == 'POST':
        if 'pokazdane' in request.form:
            return redirect(url_for('show_personal_data'))
        elif 'edytujdaneklienta' in request.form:
            return redirect(url_for('get_pesel'))
        elif 'pokazwnioski' in request.form:
            return redirect(url_for('show_documents'))
        elif 'pokazzgloszeniabledow' in request.form:
            return redirect(url_for('show_error_reports'))
        elif 'zglosblad' in request.form:
            return redirect(url_for('report_error'))
        elif 'przegladajwnioski' in request.form:
            return redirect(url_for('view_forms'))
        elif 'przegladajzgloszeniabledow' in request.form:
            return redirect(url_for('view_error_reports'))
        elif 'dodajklienta' in request.form:
            return redirect(url_for('add_client'))
        elif 'zlozwniosek' in request.form:
            return redirect(url_for('apply'))
        elif 'wyloguj' in request.form:
            logout_user()
            error = 'Zostałeś poprawnie wylogowany'
            return redirect(url_for('login', error=error))

    if session['occupation'] is not None:
        visibility = 'visible'
    else:
        visibility = 'hidden'

    return render_template('PokazDane.html', data=get_data_from_db(session.get('id')), visibility=visibility)


@app.route('/getpesel', methods=['GET', 'POST'])
def get_pesel():
    if request.method == "POST":
        session['pesel'] = request.form['pesel']
        return redirect(url_for('edit_user_data'))

    return render_template('EdytujPopUP.html')


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
    try:
        data = get_data_from_db_by_pesel(session['pesel'])
    except Exception as error:
        session['Exception'] = str(error)
        return redirect(url_for('server_error'))

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

            if data['birthdate'] == request.form['birthdate'] or data['gender'] == request.form['gender']:
                new_pesel = generate_pesel(data['birthdate'], data['gender'])
                session['pesel'] = new_pesel

            try:
                cursor = get_cursor()
                cursor.execute(
                    'UPDATE personal_data SET "Name" = %s, "Surname" = %s, "Birthdate" = %s, "Birthplace" = %s, '
                    '"Gender" = %s, "CityOfRegistration" = %s, "PostCode" = %s, "Street" = %s, "HouseNo" = %s, '
                    '"FlatNo" = %s, "PhoneNo" = %s, "CallPrefix" = %s, "CivilState" = %s, "Citizenship" = %s, '
                    '"PESEL" = %s '
                    'WHERE "PESEL" = %s',
                    (data['name'], data['surname'], data['birthdate'], data['birthcity'], data['gender'],
                     data['registrationcity'], reformat_postal_code(data['postalcode']), data['street'], data['No'],
                     data['flatNo'],
                     data['phoneNo'],
                     data['phoneprefix'], data['civilstatus'], data['citizenship'], session['pesel'], data['pesel'],))

                conn.commit()
            except Exception as error:
                session['Exception'] = str(error)
                return redirect(url_for('server_error'))

        elif 'powrot' in request.form:
            return redirect(url_for('show_personal_data'))

    if session['occupation'] == 'Urzędnik' or session['occupation'] is None:
        visibility = 'hidden'
    else:
        visibility = 'visible'

    return render_template('EdytujKlienta.html',
                           data=get_data_from_db_by_pesel(session.get('pesel')),
                           visibility=visibility)


@app.route('/apply', methods=['GET', 'POST'])
def apply():
    cursor = get_cursor()
    types = ['Akt ślubu', 'Akt zgonu', 'Akt urodzenia', 'Akt obywatelstwa']

    if request.method == 'POST':
        if 'wyslij' in request.form:
            try:
                cursor.execute('INSERT INTO documents ("Type", "AppUserID") VALUES (%s, %s)',
                               (request.form['selectlist'], session.get('id'),))
                conn.commit()
            except Exception as error:
                session['Exception'] = str(error)
                return redirect(url_for('server_error'))
            return redirect(url_for('show_personal_data'))

        elif 'powrot' in request.form:
            return redirect(url_for('show_personal_data'))

    return render_template('ZlozWniosek.html', types=types)


@app.route('/documents', methods=['GET', 'POST'])
def show_documents():
    headings = ("Numer Aplikacji", "Typ", "Status", "Data złożenia wniosku", "Data weryfikacji", "Data rozpatrzenia")
    cursor = get_cursor()

    cursor.execute('SELECT "ApplicationID", "Type", "Status", DATE_TRUNC(\'second\', "DateOfApplication"::timestamp), '
                   'DATE_TRUNC(\'second\', "DateOfVerification"::timestamp), '
                   'DATE_TRUNC(\'second\', "DateOfConsideration"::timestamp) FROM documents WHERE "AppUserID" = %s',
                   (str(session['id']),))
    data = cursor.fetchall()

    for i in data:
        try:
            i[3] = i[3].strftime("%d.%m.%Y %H:%M:%S")
        except:
            pass

    if request.method == "POST":
        return redirect(url_for('show_personal_data'))

    return render_template('PokazWnioski.html', headings=headings, data=data)


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
                elif i == 'postalcode':
                    new_data[i] = reformat_postal_code(j)

            for i in data.copy().keys():
                if i not in new_data:
                    data.pop(i)
            try:
                cursor.execute('INSERT INTO data_corrections ("DataField","OldVal", "NewVal", "AppUserID", "Info") '
                               'VALUES (%s, %s, %s, %s, %s);',
                               ('; '.join(list(new_data.keys())), Json(data), Json(new_data), session['id'], str(info)))
                conn.commit()
            except Exception as error:
                session['Exception'] = str(error)
                return redirect(url_for('server_error'))
            return redirect(url_for('show_personal_data'))

        if 'powrot' in request.form:
            return redirect(url_for('show_personal_data'))

    return render_template("ZglosBlad.html", data=get_data_from_db(session['id']))


@app.route('/showerrorreports', methods=['GET', 'POST'])
def show_error_reports():
    headings = (
        "Numer zgłoszenia", "Status", "Poprzednie dane", "Poprawione dane", "Data zgłoszenia", "Data weryfikacji",
        "Info")

    cursor = get_cursor()

    cursor.execute(
        'SELECT "CorrectionID", "Status", "OldVal", "NewVal", DATE_TRUNC(\'second\', "DateOfApplication"::timestamp), '
        'DATE_TRUNC(\'second\', "DateOfConsideration"::timestamp), "Info" FROM data_corrections WHERE "AppUserID" = %s',
        (str(session['id']),))
    data = cursor.fetchall()

    for i in data:
        temp = ''
        if i[2] is not None:
            for j in list(i[2].values()):
                temp = temp + j
                if len(data) != 1:
                    temp + '; '
            i[2] = temp
        temp = ''
        if i[3] is not None:
            for j in list(i[3].values()):
                temp = temp + j
                if len(data) != 1:
                    temp + '; '
            i[3] = temp

    for i in data:
        try:
            i[3] = i[3].strftime("%d.%m.%Y %H:%M:%S")
        except:
            pass

    return render_template('PokazBledy.html', headings=headings, data=data)


@app.route('/addclient', methods=['GET', 'POST'])
def add_client():
    visibility = 'hidden'
    error = ''

    if request.method == 'POST':
        if 'submit' in request.form:
            data = request.form.to_dict()
            for i, j in data.copy().items():
                if i == 'submit':
                    data.pop(i)
                elif i == 'powrot':
                    data.pop(i)
                elif i == 'birthdate':
                    data[i] = datetime.strptime(j, '%Y-%m-%d')
            new_pesel = generate_pesel(data['birthdate'], data['gender'])

            try:
                cursor = get_cursor()
                cursor.execute(
                    'INSERT INTO personal_data ( "Name", "Surname", "Birthdate", "Birthplace", '
                    '"Gender", "CityOfRegistration", "PostCode", "Street", "HouseNo", '
                    '"FlatNo", "PhoneNo", "CallPrefix", "CivilState", "Citizenship", "PESEL") '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (data['name'], data['surname'], data['birthdate'], data['birthcity'], data['gender'],
                     data['registrationcity'], reformat_postal_code(data['postalcode']), data['street'], data['No'],
                     data['flatNo'],
                     data['phoneNo'],
                     data['phoneprefix'], data['civilstatus'], data['citizenship'],
                     new_pesel,))
                conn.commit()

            except Exception as err:
                visibility = 'visible'
                error = err

        if 'powrot' in request.form:
            return redirect(url_for('show_personal_data'))

    return render_template('DodajKlienta.html', visibility=visibility, error=error)


@app.route('/viewforms', methods=['GET', 'POST'])
def view_forms():
    headings = ("Numer wniosku", "Typ", "Status", "Data złożenia", "Data weryfikacji", "Data akceptacji", "PESEL",
                "Ustaw status")

    if session['occupation'] == 'Burmistrz':
        types = ('', 'Zatwierdzone', 'Zweryfikowane', 'Odrzucone', 'Oczekujące')
    else:
        types = ('', 'Zweryfikowane', 'Odrzucone', 'Oczekujące')
    cursor = get_cursor()
    cursor.execute('SELECT "ApplicationID", "Type", "Status", DATE_TRUNC(\'second\', "DateOfApplication"::timestamp), '
                   'DATE_TRUNC(\'second\', "DateOfVerification"::timestamp), '
                   'DATE_TRUNC(\'second\', "DateOfConsideration"::timestamp), "PESEL" FROM official_documents_view')
    data = cursor.fetchall()

    if request.method == 'POST':
        if 'submit' in request.form:
            action = request.form.to_dict()
            for i, j in action.copy().items():
                if i == 'submit':
                    action.pop(i)
                elif i == 'powrot':
                    action.pop(i)
                elif j == '':
                    action.pop(i)

            for i, j in action.items():
                if j == 'Zatwierdzone' or j == 'Odrzucone':
                    cursor.execute(
                        'UPDATE documents SET "Status" = %s, "DateOfConsideration" = now() WHERE "ApplicationID" = %s',
                        (j, i))
                elif j == 'Zweryfikowane':
                    cursor.execute(
                        'UPDATE documents SET "Status" = %s, "DateOfVerification" = now() WHERE "ApplicationID" = %s',
                        (j, i))
                elif j == 'Oczekujące':
                    cursor.execute('UPDATE documents SET "Status" = %s, "DateOfVerification" = NULL, '
                                   '"DateOfConsideration" = NULL WHERE "ApplicationID" = %s', (j, i))
                conn.commit()

                cursor = get_cursor()
                cursor.execute(
                    'SELECT "ApplicationID", "Type", "Status", DATE_TRUNC(\'second\', "DateOfApplication"::timestamp), '
                    'DATE_TRUNC(\'second\', "DateOfVerification"::timestamp), '
                    'DATE_TRUNC(\'second\', "DateOfConsideration"::timestamp), "PESEL" FROM official_documents_view')
                data = cursor.fetchall()

        if 'powrot' in request.form:
            return redirect(url_for('show_personal_data'))

    return render_template('PrzegladajWnioskiKlientow.html', headings=headings, data=data, types=types)


@app.route('/viewerrors', methods=['GET', 'POST'])
def view_error_reports():
    headings = ("Numer zgłoszenia", "Status", "Data złożenia", "Data akceptacji", "PESEL", "Poprzednie dane",
                "Nowe dane", "Informacja", "Ustaw status")
    types = ('', 'Oczekujące', 'Zatwierdzone', 'Odrzucone')

    cursor = get_cursor()
    cursor.execute('SELECT "CorrectionID", "Status", DATE_TRUNC(\'second\', "DateOfApplication"::timestamp), '
                   'DATE_TRUNC(\'second\', "DateOfConsideration"::timestamp), '
                   '"PESEL", "OldVal", "NewVal", "Info" FROM official_data_corrections_view')
    data = cursor.fetchall()

    if request.method == 'POST':
        if 'submit' in request.form:
            action = request.form.to_dict()
            for i, j in action.copy().items():
                if i == 'submit':
                    action.pop(i)
                elif i == 'powrot':
                    action.pop(i)
                elif j == '':
                    action.pop(i)

            for i, j in action.items():
                if j == 'Zatwierdzone' or j == 'Odrzucone':
                    try:
                        cursor.execute(
                            'UPDATE data_corrections SET "Status" = %s, "DateOfConsideration" = now() WHERE "CorrectionID" = %s',
                            (j, i))
                    except Exception as error:
                        session['Exception'] = str(error)
                        return redirect(url_for('server_error'))

                elif j == 'Oczekujące':
                    try:
                        cursor.execute('UPDATE data_corrections SET "Status" = %s, '
                                       '"DateOfConsideration" = NULL WHERE "CorrectionID" = %s', (j, i))
                    except Exception as error:
                        session['Exception'] = str(error)
                        return redirect(url_for('server_error'))

                conn.commit()

            return redirect(url_for('view_error_reports'))

        if 'powrot' in request.form:
            return redirect(url_for('show_personal_data'))

    return render_template('PrzegladajWnioskiKlientow.html', headings=headings, data=data, types=types)


@app.route('/server_error', methods=['GET', 'POST'])
def server_error():
    error = session.get('Exception', '')
    return render_template('errorHandler.html', error=error)


def generate_pesel(date, gender):
    gender = str(gender)
    if not isinstance(date, str):
        date = date.strftime('%Y-%m-%d')
    date = list(date.split("-"))
    year = int(date[0])
    month = int(date[1])
    day = int(date[2])

    if year >= 2000:
        month = month + 20

    while True:

        four_random = random.randint(1000, 9999)
        four_random = str(four_random)

        y = '%02d' % (int(year) % 100)
        m = '%02d' % int(month)
        dd = '%02d' % int(day)

        a = y[0]
        a = int(a)

        b = y[1]
        b = int(b)

        c = m[0]
        c = int(c)

        d = m[1]
        d = int(d)

        e = dd[0]
        e = int(e)

        f = dd[1]
        f = int(f)

        g = four_random[0]
        g = int(g)

        h = four_random[1]
        h = int(h)

        i = four_random[2]
        i = int(i)

        j = four_random[3]
        j = int(j)

        if str(gender) == 'Kobieta':
            if j % 2 == 1:
                j = j + 1
            if j >= 10:
                j = 0
        else:
            if j % 2 == 0:
                j = j + 1
            if j >= 10:
                j = 1

        check = a + 3 * b + 7 * c + 9 * d + e + 3 * f + 7 * g + 9 * h + i + 3 * j

        if check % 10 == 0:
            last_digit = 0
        else:
            last_digit = 10 - (check % 10)

        if len(str(month)) == 1:
            month = '0' + str(month)

        if len(str(day)) == 1:
            day = '0' + str(day)

        final_pesel = str(str(year)[-2]) + str(str(year)[-1]) + str(month) + str(day) + str(four_random) + str(
            last_digit)

        cursor = get_cursor()
        cursor.execute('SELECT * FROM personal_data WHERE "PESEL" = %s', [final_pesel])
        temp = cursor.fetchone()

        if not temp:
            break

    return final_pesel


def get_data_from_db(id):
    data = get_data_from_db_by_pesel(get_pesel_from_id(id))

    return data


def get_data_from_db_by_pesel(pesel):
    cursor = get_cursor()
    cursor.execute('SELECT * FROM personal_data WHERE "PESEL" = %s', [pesel])
    data = cursor.fetchone()
    data = {
        'pesel': data[0],
        'name': data[1],
        'surname': data[2],
        'birthdate': data[3].strftime("%d.%m.%Y"),
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


def reformat_postal_code(code):
    return code.replace('-', '')


if __name__ == '__main__':
    app.run(debug=True)
