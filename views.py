from flask import flash, render_template, request, redirect, jsonify, url_for
from flask_mail import Message
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import current_user
from flask.ext.login import login_required
from wette import app, db_session, ModelForm, mail

from models import User, Match, Outcome

from wtforms.fields import TextField, DecimalField, PasswordField, SelectField
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

        msg = Message('Hello',
                  sender='euro2016@schosel.net',
                  recipients=[user.email])

        mail.send(msg)

        return render_template('register_success.html')

    return render_template('register.html', form=form)

class BetForm(Form):

    def append_field(self, name, field):
        setattr(self, name, field)

@app.route('/')
@app.route('/main')
@login_required
def main():

    # form = BetForm()
    #
    # bets = current_user.bets

    #This numbering might be dangerous
    # for i, bet in enumerate(bets):
    #     form.append_field('bet_' + i, SelectField(choices=Outcome))

    return render_template('main.html')
