# app/models.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app.extensions import db

class Professor(UserMixin, db.Model):
    __tablename__ = 'professors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

class Student(UserMixin, db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

class Module(db.Model):
    __tablename__ = 'modules'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'), nullable=False)
    professor = db.relationship('Professor', backref=db.backref('modules', lazy=True))

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))
    quiz_path = db.Column(db.String(255))
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    module = db.relationship('Module', backref=db.backref('courses', lazy=True))

class QuizScore(db.Model):
    __tablename__ = 'quiz_scores'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    quiz_path = db.Column(db.String(255))
    score = db.Column(db.Numeric(5, 2))
    attempt_datetime = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, nullable=False)
    student = db.relationship('Student', backref=db.backref('quiz_scores', lazy=True))
    course = db.relationship('Course', backref=db.backref('quiz_scores', lazy=True))
