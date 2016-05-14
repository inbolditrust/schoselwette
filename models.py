from wette import Base, db_session
from sqlalchemy import Column, Boolean, DateTime, String, Integer, ForeignKey, Enum
from sqlalchemy_utils import EmailType
from sqlalchemy.orm import relationship

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
    def bets(self):

        all_matches = db_session.query(Match)

        matches_of_existing_bets = [bet.match for bet in self.existing_bets]

        matches_without_bets = [match for match in all_matches if match not in matches_of_existing_bets]

        for match in matches_without_bets:
            bet = Bet()
            bet.user = self
            bet.match = match

        return self.existing_bets

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

    @property
    def name(self):
        return self.first_name + ' ' + self.last_name[:1] + '.'


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    long_name = Column(String(128), nullable=False)
    short_name = Column(String(3), nullable=False)
    group = Column(String(1), nullable=False)
    champion = Column(Boolean, nullable=False)

Outcome = Enum('1', '2', 'X')

class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    team1_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    team2_id = Column(Integer, ForeignKey('teams.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    outcome = Column(Outcome)

    team1 = relationship('Team', foreign_keys=[team1_id])
    team2 = relationship('Team', foreign_keys=[team2_id])

    # Returns a dictionary from outcome -> odd
    def get_odds(self):

        valid_outcomes = [bet.outcome for bet in self.bets if bet.is_valid()]

        n = len(valid_outcomes)

        from collections import Counter

        counter = Counter(valid_outcomes)

        #TODO: normalize using n
        return counter


class Bet(Base):
    __tablename__ = 'bets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    outcome = Column(Outcome)

    user = relationship('User', backref='existing_bets')
    match = relationship('Match', backref='bets')

    def is_valid(self):
        return self.outcome is not None
