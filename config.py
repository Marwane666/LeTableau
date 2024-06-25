import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = '2b5aad2b2f454102cde030bc1cfe607e06a98f8ba7319d6f'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://Marwane:Kayakan2002@localhost/e_learning_dashboard'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'sessions'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'sk-proj-WumELeokW8wJ61rlHwgvT3BlbkFJN7Dro6KAgaN9Zre4JxA6'
