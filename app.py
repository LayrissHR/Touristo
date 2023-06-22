import os
from datetime import datetime, timedelta
from random import random, sample

import requests
from transliterate import translit, get_available_language_codes
from flask import Flask, render_template, request, abort, flash, redirect, url_for, send_from_directory
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from flask_security import LoginForm
from flask_sqlalchemy import SQLAlchemy
import locale

from passlib.handlers.bcrypt import bcrypt
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import StringField, PasswordField, Form, SubmitField
from wtforms.validators import DataRequired, Email

postgres = {"username": "diplom", "password": "81EHvSZiBGLC", "host": "ep-shy-glade-508280.eu-central-1.aws.neon.tech", "port": 5432, "database": "diplom"}



app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(username)s:%(password)s@%(host)s:%(port)s/%(database)s' % postgres

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = "awiuigunmjijmjirwl12p5ugumnbmmawe"
db = SQLAlchemy(app, session_options={"autoflush": False})

login_manager = LoginManager()
login_manager.init_app(app)

locale.setlocale(locale.LC_ALL, 'bg_BG.utf8')

# no auto flsuh
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(40))
    lname = db.Column(db.String(40))
    address = db.Column(db.String(800))
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    passwordhash = db.Column(db.String(500))
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    admin = db.Column(db.Boolean, default=False)

    def __init__(self, fname, lname, address, email, phone, passwordhash):
        self.fname = fname
        self.lname = lname
        self.address = address
        self.email = email
        self.phone = phone
        self.passwordhash = passwordhash



class Country(db.Model):
    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.String(1000))
    category = db.Column(db.String(30))
    offers = db.relationship('Offer', backref='country', lazy=True)

    def __init__(self, name, description, category):
        self.name = name
        self.description = description
        self.category = category


class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    days = db.Column(db.Integer)
    date_of_departure = db.Column(db.Date)
    date_of_return = db.Column(db.Date)
    description = db.Column(db.String(1000))
    free_places = db.Column(db.Integer)
    price = db.Column(db.Float)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'))
    reservations = db.relationship('Reservation', backref='offer', lazy=True)
    location = db.Column(db.String(200))

    def __init__(self, name, days, date_of_departure, date_of_return, description, free_places, price, country_id,
                    location):
            self.name = name
            self.days = days
            self.date_of_departure = date_of_departure
            self.date_of_return = date_of_return
            self.description = description
            self.free_places = free_places
            self.price = price
            self.country_id = country_id
            self.location = location


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('offer.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tickets = db.Column(db.Integer)

    def __init__(self, offer_id, user_id, tickets):
        self.offer_id = offer_id
        self.user_id = user_id
        self.tickets = tickets


with app.app_context():
    db.create_all()


def get_countries():
    countries = Country.query.all()
    for country in countries:
        country.lower_name = country.name.lower()
    return countries


def generateticket(offer1, name1, location1, dateofdeparture, dateofreturn, price5, reguser, ticketi, reservationid):
    dateofreturn = dateofreturn.strftime("%d.%m.%Y")
    dateofdeparture = dateofdeparture.strftime("%d.%m.%Y")
    date5 = dateofdeparture + " - " + dateofreturn

    country1 = offer1.country
    country1 = translit(str(country1.name), 'bg', reversed=True)

    name1 = translit(name1, 'bg', reversed=True)


    url = f"https://tickets.kadsoftwareusa.com/imageCreator.php?" \
          f"event={offer1.id}" \
          f"&userID=17" \
          f"&clrCenterBack=FFFFFF" \
          f"&&imgBackName=" \
          f"&&clrCompany=6B7AAA" \
          f"&clrText=FFFFFF" \
          f"&clrUserText=000000" \
          f"&clrBottomRect=6B7AAA" \
          f"&clrSquares=6B7AAA" \
          f"&clrBack=F0F0F0" \
          f"&msg=&area=" \
          f"&smtxt1={translit(offer1.name, 'bg', reversed=True)}" \
          f"&concert={name1}" \
          f"&smtxt2={translit(location1, 'bg', reversed=True)}" \
          f"&venue={country1}" \
          f"&city=" \
          f"&date={date5}" \
          f"&section=&row=&seat=" \
          f"&price={price5}" \
          f"&company=Touristo" \
          f"&conv=" \
          f"&currsym=3" \
          f"&font=0&" \
          f"border=Y"



    response = requests.get(url)
    ticketid = str(reguser.id) + "_" + str(offer1.id) + "_" + str(reservationid.id) + "_" + str(ticketi)
    with open(f"static/tickets/{ticketid}.png", 'wb') as f:
        f.write(response.content)

        return True


@app.route('/')
def index():

    all_offers = Offer.query.all()

    random_offers = None

    if len(all_offers) > 4:
        random_offers = sample(all_offers, 4)
    else:
        random_offers = all_offers

    for offer in random_offers:
        offer.lower_name = offer.name.lower()


    return render_template('index.html', user=current_user, countries=get_countries(), topoffers=random_offers)



@app.route("/category", methods=['GET', 'POST'])
@app.route("/category/<categoryname>", methods=['GET', 'POST'])
def category(categoryname=None):

    if categoryname is None:
        flash('Нямаме информация за тази категория.', category='error')
        return redirect(url_for('index'))

    if categoryname != "eucap" and categoryname != "bg" and categoryname != "exotic":
        flash('Нямаме информация за тази категория.', category='error')
        return redirect(url_for('index'))

    countries = Country.query.filter_by(category=categoryname).all()

    for country1 in countries:
        country1.lower_name = country1.name.lower()

    return render_template('category.html', user=current_user, countries=countries, category=category)


@app.route('/country', methods=['GET', 'POST'])
@app.route('/country/<countryname>', methods=['GET', 'POST'])
def country(countryname=None):

    if countryname is None:
        flash('Нямаме информация за тази държава.', category='error')
        return redirect(url_for('index'))
    else:
        countryname = countryname.capitalize()
        country = Country.query.filter_by(name=countryname).first()

        if country is None:
            flash('Нямаме информация за тази държава.', category='error')
            return redirect(url_for('index'))

        country.lower_name = country.name.lower()

        offers = Offer.query.filter_by(country_id=country.id).all()

        for offer in offers:
            offer.date_of_departure = offer.date_of_departure.strftime("%d %B %Y")
            offer.date_of_return = offer.date_of_return.strftime("%d %B %Y")
            offer.country = country

        return render_template('country.html', user=current_user, country=country, offers=offers,
                               countries=get_countries())


@app.route('/offer/', methods=['GET', 'POST'])
@app.route('/offer/<offerid>', methods=['GET', 'POST'])
def offer(offerid=None):

    if offerid is None or not offerid.isdigit():
        flash('Нямаме информация за тази оферта.', category='error')
        return redirect(url_for('index'))

    offer = Offer.query.filter_by(id=offerid).first()
    if offer is None:
        flash('Нямаме информация за тази оферта.', category='error')
        return redirect(url_for('index'))


    offer.date_of_departure = offer.date_of_departure.strftime("%d %B %Y")
    offer.date_of_return = offer.date_of_return.strftime("%d %B %Y")
    offer.country = Country.query.filter_by(id=offer.country_id).first()

    return render_template('offer.html', user=current_user, offer=offer, countries=get_countries())


@app.route('/reserve', methods=['GET', 'POST'])
@app.route('/reserve/<offerid>', methods=['GET', 'POST'])
@login_required
def reserve(offerid=None):

    if offerid is None or not offerid.isdigit():
        flash('Нямаме информация за тази оферта.', category='error')
        return redirect(url_for('index'))

    offer = Offer.query.filter_by(id=offerid).first()
    if offer is None:
        flash('Нямаме информация за тази оферта.', category='error')
        return redirect(url_for('index'))


    earlyreservation = False
    earlydiscount = 0
    rounded_discount = 0


    # make offer.date_of_departure a datetime object insted of date
    offerdateofdeparture = datetime.strptime(str(offer.date_of_departure), '%Y-%m-%d')

    # check if offer.date_of_departure is more than 7 days from now #2023-06-23
    if offerdateofdeparture > datetime.now() + timedelta(days=20):
        print("early reservation")
        earlyreservation = True
        earlydiscount = offer.price * 0.10
        rounded_discount = round(earlydiscount, 2)


        # If XX.00, then round to XX
        if rounded_discount.is_integer():
            rounded_discount = int(rounded_discount)
            print("no decimals")
        else:
            rounded_discount = f"{rounded_discount:.2f}"
            print("decimals")


    else:
        print("late reservation")


    if request.method == "POST":
        ticketnumber = request.form.get("tickets")
        ticketnumber = int(ticketnumber)

        if ticketnumber < 1:
            flash('Невалиден брой билети.', category='error')
            return redirect(url_for('reserve', offerid=offer.id))

        if ticketnumber > offer.free_places:
            flash('Нямаме толкова свободни места.', category='error')
            return redirect(url_for('reserve', offerid=offer.id))

        reservation = Reservation(offer.id, current_user.id, ticketnumber)
        db.session.add(reservation)
        db.session.commit()

        # start from 1 and go to ticketnumber
        for i in range(1, ticketnumber + 1):
            fname = request.form.get("fname" + str(i))
            lname = request.form.get("lname" + str(i))
            address = request.form.get("address" + str(i))
            phone = request.form.get("phone" + str(i))
            ticketi = i



            generateticket(offer, fname + " " + lname, offer.location, offer.date_of_departure, offer.date_of_return, offer.price, current_user, ticketi, reservation)


        flash('Успешно резервирахте билети.', category='success')
        return redirect(url_for('index'))

    return render_template('reserve.html', user=current_user, offer=offer, countries=get_countries(), earlyreservation=earlyreservation, earlydiscount=rounded_discount)





@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()

    for reservation in reservations:
        offer = Offer.query.filter_by(id=reservation.offer_id).first()
        reservation.offer = offer
        reservation.total_price = offer.price * reservation.tickets

    return render_template('profile.html', user=current_user, countries=get_countries(), reservations=reservations)


@app.route('/tickets', methods=['GET', 'POST'])
@app.route("/tickets/<reservationid>", methods=['GET', 'POST'])
@login_required
def tickets(reservationid=None):

    if reservationid is None or not reservationid.isdigit():
        flash('Нямаме информация за тази резервация.', category='error')
        return redirect(url_for('index'))

    reservation = Reservation.query.filter_by(id=reservationid).first()
    if reservation is None:
        flash('Нямаме информация за тази резервация.', category='error')
        return redirect(url_for('index'))

    if reservation.user_id != current_user.id:
        flash('Нямаме информация за тази резервация.', category='error')
        return redirect(url_for('index'))

    tickets = []

    for filename in os.listdir("static/tickets"):
        if filename.startswith(str(current_user.id) + "_" + str(reservation.offer_id) + "_" + str(reservation.id)):
            tickets.append(filename)



    return render_template('tickets.html', user=current_user, countries=get_countries(), tickets=tickets, reservation=reservation, offer=Offer.query.filter_by(id=reservation.offer_id).first())




@app.route('/static/tickets/<filename>')
def uploaded_file(filename):
    # remove the extension
    filename = filename.split(".")[0]
    filename = filename.split("_")
    userid = filename[0]
    offerid = filename[1]
    reservationid = filename[2]
    ticketnumber = filename[3]

    if userid != str(current_user.id):
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    if reservationid is None or not reservationid.isdigit():
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    if offerid is None or not offerid.isdigit():
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    if ticketnumber is None or not ticketnumber.isdigit():
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    reservation = Reservation.query.filter_by(id=reservationid).first()
    if reservation is None:
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    if reservation.user_id != current_user.id:
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    offer = Offer.query.filter_by(id=offerid).first()
    if offer is None:
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    if offer.id != reservation.offer_id:
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    if int(ticketnumber) > int(reservation.tickets):
        flash('Нямаме информация за този билет.', category='error')
        return redirect(url_for('index'))

    UPLOAD_FOLDER = 'static/tickets'

    return send_from_directory(UPLOAD_FOLDER, str(current_user.id) + "_" + str(reservation.offer_id) + "_" + str(reservation.id) + "_" + str(ticketnumber) + ".png")




@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))




    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user is None or not check_password_hash(user.passwordhash, password):
            flash('Грешен имейл или парола.', category='error')
            return redirect(url_for('login'))

        login_user(user)
        flash('Успешно влизане.', category='success')
        return redirect(url_for('index'))







    return render_template('login.html', user=current_user, countries=get_countries())



@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        address = request.form.get('address')
        phone = request.form.get('phone')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Имейл адресът е зает.', category='error')
        elif len(email) < 4:
            flash('Имейл адресът е твърде къс.', category='error')
        elif len(fname) < 2:
            flash('Името е твърде късо.', category='error')
        elif len(lname) < 2:
            flash('Фамилията е твърде къса.', category='error')
        elif password1 != password2:
            flash('Паролите не съвпадат.', category='error')
        elif len(password1) < 7:
            flash('Паролата е твърде къса.', category='error')

        else:
            new_user = User(email=email, fname=fname, lname=lname, address=address, passwordhash=generate_password_hash(password1, method='sha256'), phone=phone)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Успешна регистрация.', category='success')
            return redirect(url_for('index'))

    return render_template('sign-up.html', user=current_user, countries=get_countries())



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Успешно излизане.', category='success')
    return redirect(url_for('index'))


@app.route('/admin', methods=['GET', 'POST'])
@app.route('/admin/', methods=['GET', 'POST'])
@app.route('/admin/<where>', methods=['GET', 'POST'])
@app.route('/admin/<where>/', methods=['GET', 'POST'])
@app.route('/admin/<where>/edit/<ided>', methods=['GET', 'POST'])
@app.route('/admin/<where>/edit/<ided>/', methods=['GET', 'POST'])
@login_required
def admin(where=None, ided=None):
    if not current_user.admin:
        flash('Нямате достъп до тази страница.', category='error')
        return redirect(url_for('index'))


    if where == 'offers':
        if ided is not None:
            isreserved = False
            # check if any reservation is made for this offer
            reservations = Reservation.query.filter_by(offer_id=ided).all()
            if reservations is not None and len(reservations) > 0:
                isreserved = True
            if request.method == "POST":
                name = request.form.get('name')
                description = request.form.get('description')
                countryid = request.form.get('country')
                location = request.form.get('loc')
                price = request.form.get('price')
                free_places = request.form.get('free_places')

                date_of_departure = request.form.get('date_of_departure')
                date_of_return = request.form.get('date_of_return')

                picture = request.files['picture']

                if name is None or description is None or countryid is None or location is None or price is None or free_places is None or date_of_departure is None or date_of_return is None or picture is None:
                    flash('Моля попълнете всички полета.', category='error')
                    return redirect(url_for('admin', where='offers', ided=ided))

                country = Country.query.filter_by(id=countryid).first()


                Offer.query.filter_by(id=ided).update(dict(name=name, description=description, country_id=country.id, location=location, price=price, free_places=free_places, date_of_departure=date_of_departure, date_of_return=date_of_return))
                db.session.commit()

                if picture.filename != '':
                    UPLOAD_FOLDER = 'static/offers'
                    picture.save(os.path.join(UPLOAD_FOLDER, str(ided) + ".jpg"))

                flash('Успешно редактиране.', category='success')
                return redirect(url_for('admin', where='offers', ided=ided))


            return render_template("editoffers.html", user=current_user, offer=Offer.query.filter_by(id=ided).first(), countries=get_countries(), isreserved=isreserved)
        else:

            return render_template('adminoffers.html', user=current_user, offers=Offer.query.all())

    elif where == 'dests':
        if ided is not None:
            if request.method == "POST":
                name = request.form.get('name')
                description = request.form.get('description')
                picture = request.files['picture']
                category = request.form.get('country')

                if name is None or description is None or picture is None:
                    flash('Моля попълнете всички полета.', category='error')
                    return redirect(url_for('admin', where='dests', ided=ided))

                Country.query.filter_by(id=ided).update(dict(name=name, description=description, category=category))
                db.session.commit()

                if picture.filename != '':
                    UPLOAD_FOLDER = 'static/dests'
                    picture.save(os.path.join(UPLOAD_FOLDER, str(ided) + ".jpg"))

                flash('Успешно редактиране.', category='success')
                return redirect(url_for('admin', where='dests', ided=ided))

            return render_template("editdests.html", user=current_user, dest=Country.query.filter_by(id=ided).first())
        else:
            return render_template('admindests.html', user=current_user, dests=Country.query.all())







    return render_template('admin.html', user=current_user)


@app.route('/del/<where>/<ided>')
@app.route('/del/<where>/<ided>/')
@login_required
def delete(where=None, ided=None):
    if where is None or ided is None:
        flash('Няма такава страница.', category='error')
        return redirect(url_for('admin'))

    if where == 'offers':
        offer = Offer.query.filter_by(id=ided).first()
        reservations = Reservation.query.filter_by(offer_id=offer.id).all()
        if reservations is not None and len(reservations) > 0:
            for reservation in reservations:
                db.session.delete(reservation)

        db.session.delete(offer)
        db.session.commit()
        flash('Успешно изтриване.', category='success')
        return redirect(url_for('admin', where='offers'))

    elif where == 'dests':
        country = Country.query.filter_by(id=ided).first()
        offers = Offer.query.filter_by(country_id=country.id).all()
        if offers is not None and len(offers) > 0:
            for offer in offers:
                reservations = Reservation.query.filter_by(offer_id=offer.id).all()
                if reservations is not None and len(reservations) > 0:
                    for reservation in reservations:
                        db.session.delete(reservation)
                db.session.delete(offer)

        db.session.delete(country)
        db.session.commit()

        flash('Успешно изтриване.', category='success')
        return redirect(url_for('admin', where='dests'))


@app.route('/add/<where>', methods=['GET', 'POST'])
@app.route('/add/', methods=['GET', 'POST'])
@app.route('/add', methods=['GET', 'POST'])
@app.route('/add/<where>/', methods=['GET', 'POST'])
@login_required
def add(where=None):

    print(where)

    if where is None:
        flash('Няма такава страница.', category='error')
        return redirect(url_for('admin'))

    if where == 'offers':

        if request.method == "POST":
            name = request.form.get('name')
            description = request.form.get('description')
            countryid = request.form.get('country')
            location = request.form.get('loc')
            price = request.form.get('price')
            free_places = request.form.get('free_places')

            date_of_departure = request.form.get('date_of_departure')
            date_of_return = request.form.get('date_of_return')


            picture = request.files['picture']

            if name is None or description is None or countryid is None or location is None or price is None or free_places is None or date_of_departure is None or date_of_return is None or picture is None or picture.filename == '':
                flash('Моля попълнете всички полета.', category='error')
                return redirect(url_for('add', where='offers'))

            days = (datetime.strptime(date_of_return, '%Y-%m-%d') - datetime.strptime(date_of_departure, '%Y-%m-%d')).days

            country = Country.query.filter_by(id=countryid).first()

            offer = Offer(name=name, description=description, country_id=country.id, days=days, location=location, price=price, free_places=free_places, date_of_departure=date_of_departure, date_of_return=date_of_return)
            db.session.add(offer)
            db.session.commit()

            if picture.filename != '':
                UPLOAD_FOLDER = 'static/offers'
                picture.save(os.path.join(UPLOAD_FOLDER, str(offer.id) + ".jpg"))

            flash('Успешно добавяне.', category='success')
            return redirect(url_for('admin', where='offers'))


        return render_template('addoffer.html', user=current_user, countries=get_countries())

    elif where == 'dests':
        if request.method == "POST":
            name = request.form.get('name')
            description = request.form.get('description')
            picture = request.files['picture']
            category = request.form.get('country')

            if name is None or description is None or picture is None or picture.filename == '' or category is None:
                flash('Моля попълнете всички полета.', category='error')
                return redirect(url_for('add', where='dests'))

            country = Country(name=name, description=description, category=category)
            db.session.add(country)
            db.session.commit()

            if picture.filename != '':
                UPLOAD_FOLDER = 'static/dests'
                picture.save(os.path.join(UPLOAD_FOLDER, str(country.id) + ".jpg"))

            flash('Успешно добавяне.', category='success')
            return redirect(url_for('admin', where='dests'))

        return render_template('adddest.html', user=current_user, countries=get_countries())





if __name__ == '__main__':
    app.debug = True
    app.run()
