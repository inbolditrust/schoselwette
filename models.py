from collections import Counter
from wette import Base, db_session
from sqlalchemy import Column, Boolean, DateTime, String, Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy_utils import EmailType
from sqlalchemy.orm import relationship, backref
import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(EmailType, nullable=False, unique=True, info={'label': 'Email'})
    first_name = Column(String(64), nullable=False, info={'label': 'First Name'})
    last_name = Column(String(64), nullable=False, info={'label': 'Last Name'})
    password = Column(String(64), nullable=False)
    paid = Column(Boolean, nullable=False)
    champion_id = Column(Integer, ForeignKey('teams.id'), nullable=True)

    champion = relationship('Team')

    @property
    def points(self):

        return sum([bet.points for bet in self.bets])

    def create_missing_bets(self):

        all_matches = db_session.query(Match)

        matches_of_existing_bets = [bet.match for bet in self.bets]

        matches_without_bets = [match for match in all_matches if match not in matches_of_existing_bets]

        for match in matches_without_bets:
            bet = Bet()
            bet.user = self
            bet.match = match

    @property
    def name(self):
        return self.first_name + ' ' + self.last_name[:1] + '.'

    # BEGIN This is for flask login
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
    # END

    def __repr__(self):
        return '<User: id={}, email={}, first_name={}, last_name={}, paid={}, champion_id={}>'.format(
            self.id, self.email, self.first_name, self.last_name, self.paid, self.champion_id)

    @property
    def champion_editable(self):
        first_match = db_session.query(Match).order_by('date').first()
        return first_match.date > datetime.datetime.now()


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False, unique=True)
    short_name = Column(String(3), nullable=False, unique=True)
    group = Column(String(1), nullable=False)
    champion = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return '<Team: id={}, name={}, short_name={}, group={}, champion={}>'.format(
            self.id, self.name, self.short_name, self.group, self.champion)

Outcome = Enum('1', 'X', '2')
Stage = Enum('Group stage', 'Round of 16', 'Quarter-finals', 'Semi-finals', 'Final')

class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    team1_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    team2_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    stage = Column(Stage)
    outcome = Column(Outcome)

    team1 = relationship('Team', foreign_keys=[team1_id])
    team2 = relationship('Team', foreign_keys=[team2_id])
    __table_args__ = (UniqueConstraint('team1_id', 'team2_id', 'stage'),)

    @property
    def editable(self):
        # return self.date > datetime.datetime.now()
        return self.date > datetime.datetime(year=2016, month=6, day=15)


    # Returns a dictionary from outcome -> odd
    @property
    def odds(self):

        valid_bets = [bet for bet in self.bets if bet.valid]
        valid_outcomes = [bet.outcome for bet in valid_bets]

        n = len(valid_bets)

        counter = Counter(valid_outcomes)

        #TODO: normalize using n
        for o in counter.keys():
            counter[o] = n / counter[o] #n is always greater than counter

        return counter

    def __repr__(self):
        return '<Match: id={}, team1={}, team2={}, date={}, stage={}, outcome={}>'.format(
            self.id, self.team1.name, self.team2.name, self.date, self.stage, self.outcome)


class Bet(Base):
    __tablename__ = 'bets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    outcome = Column(Outcome)
    supertip = Column(Boolean, default=False, nullable=False)

    match = relationship('Match', backref='bets')
    user = relationship('User', backref='bets')

    __table_args__ = (UniqueConstraint('user_id', 'match_id'),)

    @property
    def valid(self):
        return self.outcome is not None

    @property
    def points(self):

        #Make sure that outcome is not None
        if not self.valid:
            return 0

        #Make sure that the bet is correct
        if self.outcome != self.match.outcome:
            return 0

        odds = self.match.odds

        return odds[self.outcome]


    def __repr__(self):
        return '<Bet: id={}, user={}, team1={}, team2={}, stage={}, supertip={}, outcome={}>'.format(
            self.id, self.user.name, self.match.team1.name, self.match.team2.name, self.match.stage, self.supertip, self.outcome)
