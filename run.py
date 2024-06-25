from app import create_app, db
from app.models import Professor, Student, Course

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Professor': Professor, 'Student': Student, 'Course': Course}

if __name__ == '__main__':
    app.run(debug=True)
