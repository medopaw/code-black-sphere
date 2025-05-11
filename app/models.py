from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class Candidate(UserMixin, db.Model):
    __tablename__ = 'candidates'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False, unique=True)
    email = db.Column(db.Text, nullable=False, unique=True) # Assuming email is also required and unique
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship('Submission', backref='candidate', lazy='dynamic')
    tabs = db.relationship('CandidateProblemTab', backref='candidate', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

class Problem(db.Model):
    __tablename__ = 'problems'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False, unique=True)
    description = db.Column(db.Text)
    llm_prompt = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_cases = db.relationship('TestCase', backref='problem', lazy='dynamic', cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='problem', lazy='dynamic')
    tabs = db.relationship('CandidateProblemTab', backref='problem', lazy='dynamic', cascade='all, delete-orphan')

class TestCase(db.Model):
    __tablename__ = 'test_cases'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False)
    input_params = db.Column(db.Text)  # JSON string
    expected_output = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False)
    language = db.Column(db.Text)
    code = db.Column(db.Text)
    test_results = db.Column(db.Text)  # JSON string
    llm_review = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class CandidateProblemTab(db.Model):
    __tablename__ = 'candidate_problem_tabs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id', ondelete='CASCADE'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id', ondelete='CASCADE'), nullable=False)
    tab_order = db.Column(db.Integer)

    __table_args__ = (db.UniqueConstraint('candidate_id', 'problem_id', name='_candidate_problem_uc'),)

class Setting(db.Model):
    __tablename__ = 'settings'
    key = db.Column(db.Text, primary_key=True)
    value = db.Column(db.Text)
