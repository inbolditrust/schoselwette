from collections import namedtuple
from werkzeug.datastructures import MultiDict
from flask import flash, render_template, request, redirect, jsonify, url_for
from flask_mail import Message
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import current_user
from flask.ext.login import login_required
from wette import app, db_session, ModelForm, mail

from models import Bet, User, Match, Outcome

from wtforms.fields import BooleanField, TextField, DecimalField, PasswordField, SelectField, FormField, FieldList, RadioField, HiddenField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Optional, Required, EqualTo, Length

from flask_wtf import Form

import hashlib

salt = 'esekaesjAWFAKJnn;ea'


@app.route('/')
@app.route('/index')
def index():

    if current_user.is_authenticated:
        return redirect('main')

    return render_template('index.html')

class LoginForm(Form):

    email = EmailField('Email')
    password = PasswordField('Password')

class RegistrationForm(ModelForm):
    class Meta:
        model = User
        exclude = ['paid']

    password = PasswordField('Password', validators=[Length(min=8), EqualTo('confirm', message='The passwords do not match.')])
    confirm = PasswordField('Confirm Password')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('index')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.

    form = LoginForm()
    if request.method == 'POST' and form.validate():
        # Login and validate the user.
        # user should be an instance of your `User` class

        #Connect loginform and database

        q = db_session.query(User).filter(User.email == form.email.data, User.password == hashlib.md5(bytes(salt + form.password.data, 'utf-8')).hexdigest())

        user = q.first()

        if user is not None:

            login_user(user)

            flash('Logged in successfully.')

            next = request.args.get('next')
            # next_is_valid should check if the user has valid
            # permission to access the `next` url

            return redirect(next or url_for('index'))
        else:
            flash('Username/Password combination incorrect')

    return render_template('login.html', form=form)

def send_mail(msg):
    try:
        mail.send(msg)
    except:
        print('Tried to send mail, did not work.')
        print(msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if request.method == 'POST' and form.validate():
        user = User()
        form.populate_obj(user)

        #Set paid explicitly to False
        user.paid = False

        #Create password hash
        user.password = hashlib.md5(bytes(salt + user.password, 'utf-8')).hexdigest()
        db_session.add(user)

        user.create_missing_bets()

        msg = Message('Hello',
                  sender='euro2016@schosel.net',
                  recipients=[user.email])

        send_mail(msg)

        return render_template('register_success.html')

    return render_template('register.html', form=form)

def str_or_none(s):
    if s is None:
        return None
    return str(s)


class BetForm(ModelForm):
    class Meta:
        model = Bet

    #TODO: How can enum be rendered automatically as a select form?
    #TODO: this seems to be a required field. why?
    outcome = RadioField('Label', choices=[(o,o) for o in Outcome.enums], validators=[Optional()], coerce=str_or_none)

    #This stuff is important.
    dummy = HiddenField('arsch', default='foo')



class BetsForm(Form):
    bets = FieldList(FormField(BetForm))

@app.route('/')
@app.route('/main', methods=['GET', 'POST'])
@login_required
def main():

    #Collect all matches
    matches = [bet.match for bet in current_user.bets]

    if request.method == 'GET':

        # drop bets into a multidictionary
        bets_dict = MultiDict({'bets': current_user.bets})

        # Build form
        form = BetsForm(data=(bets_dict))

    if request.method == 'POST':

        form = BetsForm()

        #TODO: Check for supertipp count here

        if form.validate():

            form.populate_obj(current_user)

    return render_template('main.html', matches=matches, form=form)

@app.route('/')
@app.route('/scoreboard')
@login_required
def scoreboard():

    users = db_session.query(User)

    users_sorted = sorted(users, key=lambda x: x.points, reverse=True)

    return render_template('scoreboard.html', scoreboard = users_sorted)
