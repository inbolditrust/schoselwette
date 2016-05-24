from collections import namedtuple
from werkzeug.datastructures import MultiDict
from flask import flash, render_template, request, redirect, jsonify, url_for
from flask_mail import Message
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import current_user
from flask.ext.login import login_required
from wette import app, db_session, ModelForm, mail

from models import Bet, User, Match, Outcome, Team

from wtforms.fields import BooleanField, TextField, DecimalField, PasswordField, SelectField, FormField, FieldList, RadioField, HiddenField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Optional, Required, EqualTo, Length

from flask_wtf import Form

import hashlib



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

        q = db_session.query(User).filter(User.email == form.email.data, User.password == hashlib.md5(bytes(app.config['PASSWORD_SALT'] + form.password.data, 'utf-8')).hexdigest())

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
        msg.sender = 'euro2016@schosel.net'
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
        user.password = hashlib.md5(bytes(app.config['PASSWORD_SALT'] + user.password, 'utf-8')).hexdigest()
        db_session.add(user)

        user.create_missing_bets()

        send_mail(Message('Hello',
                  recipients=[user.email]))

        send_mail(Message('Neuer Schoselwetter',
                  body=str(user),
                  recipients=['gnebehay@gmail.com']))

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

def int_or_none(v):

    try:
        ret = int(v)
    except:
        #TODO: Check exactly what kind of exception occurs here
        ret = None

    return ret

class ChampionForm(Form):
    champion_id = SelectField('Champion',
        coerce=int_or_none)

@app.route('/')
@app.route('/main', methods=['GET', 'POST'])
@login_required
def main():


    if request.method == 'GET':

        form = ChampionForm(obj=current_user)
        #TODO: Where to put this?
        form.champion_id.choices=[(None, '')] + [(t.id, t.name) for t in db_session.query(Team).order_by('name')]

    if request.method == 'POST':

        form = ChampionForm()
        #TODO: Where to put this?
        form.champion_id.choices=[(None, '')] + [(t.id, t.name) for t in db_session.query(Team).order_by('name')]

        #This is just for the champion tip
        if form.validate():

            form.populate_obj(current_user)

        #TODO: Check for supertipp count here

        #We only deal with editable bets here so that we do not by accident change old data
        editable_bets = [bet for bet in current_user.bets if bet.match.editable]

        #Iterate over all editable tips
        for bet in editable_bets:
            # We need to set all supertips and outcomes to None/False,
            # as unechecked boxes and radio fields are not contained in the form

            bet.outcome = None
            bet.supertip = False

            outcomeField = 'outcome-{}'.format(bet.match.id)
            supertipField = 'supertip-{}'.format(bet.match.id)

            if outcomeField in request.form:
                bet.outcome = request.form[outcomeField]

            if supertipField in request.form:
                #No matter what was submitted, it means the box was checked
                bet.supertip = True

    sorted_bets = sorted(current_user.bets, key=lambda x: x.match.date)

    return render_template('main.html', bets=sorted_bets, form=form)

@app.route('/scoreboard')
@login_required
def scoreboard():

    users = db_session.query(User)

    users_sorted = sorted(users, key=lambda x: x.points, reverse=True)

    return render_template('scoreboard.html', scoreboard = users_sorted)

@app.route('/user/<int:user_id>')
@login_required
def user(user_id):

    user = db_session.query(User).filter(User.id == user_id).one()

    return render_template('user.html', user=user)

@app.route('/match/<int:match_id>')
@login_required
def match(match_id):

    match = db_session.query(Match).filter(Match.id == match_id).one()

    return render_template('match.html', match=match)
