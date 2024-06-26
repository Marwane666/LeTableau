from flask import render_template, redirect, url_for, flash, request, session as flask_session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, login
from app.models import Professor, Student, Course, Module, QuizScore
import random
import json
import time
from .initialization import initialize_and_persist_vectorstore
import llama_index.core.chat_engine.types
import os
import datetime

# Set your paths
PDF_PATH = 'data/module001/QM-S6.pdf'
PERSIST_DIR = './storage'

chat_engine = None

@login.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id)) or Professor.query.get(int(user_id))

def init_routes(app):
    @app.route('/')
    @app.route('/index')
    def index():
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = Student.query.filter_by(email=email).first() or Professor.query.filter_by(email=email).first()

            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Login unsuccessful. Please check your email and password.', 'danger')

        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            name = request.form['name']
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            user_exists = Student.query.filter_by(email=email).first() or Professor.query.filter_by(email=email).first()

            if user_exists:
                flash('Email already registered.', 'warning')
            else:
                new_user = Student(
                    name=name,
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                db.session.add(new_user)
                db.session.commit()
                flash('Account created successfully! Please login.', 'success')
                return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        courses = Course.query.all()
        return render_template('dashboard.html', courses=courses)

    @app.route('/chatbot')
    def chatbot():
        global chat_engine
        # Initialize chat engine
        if chat_engine is None:
            chat_engine = initialize_and_persist_vectorstore(PDF_PATH, PERSIST_DIR)
        return render_template('Chatbot.html', chat_engine=chat_engine)

    @app.route('/send_message', methods=['POST'])
    def send_message():
        global chat_engine
        if chat_engine is None:
            return jsonify({'error': 'Chat engine not initialized'}), 500
        message = request.form['message']
        print("Received message:", message)
        
        # Obtenir la réponse du moteur de chat
        response = chat_engine.chat(message)
        print("Type of response:", type(response))
        print(response)
        
        # Adapter pour extraire les parties sérialisables de l'objet AgentChatResponse
        if isinstance(response, llama_index.core.chat_engine.types.AgentChatResponse):
            response_data = {
                'response': response.response,  # Assurez-vous que 'response' est l'attribut correct à extraire
            }
        else:
            response_data = str(response)
        
        # Retourner la réponse comme JSON
        return jsonify(response_data)

    # Load questions from the JSON file
    def load_questions(quiz_path):
        with open(quiz_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        return questions

    def reset_quiz_session():
        keys_to_clear = ['question_ids', 'current_question', 'start_time', 'answers', 'total_time', 'quiz_path', 'course_id']
        for key in keys_to_clear:
            flask_session.pop(key, None)

    def start_new_quiz(quiz_path, course_id):
        reset_quiz_session()
        questions = load_questions(quiz_path)
        flask_session['question_ids'] = [question['id'] for question in random.sample(questions, 20)]
        flask_session['current_question'] = 0
        flask_session['start_time'] = time.time()
        flask_session['answers'] = {}
        flask_session['total_time'] = 600
        flask_session['quiz_path'] = quiz_path
        flask_session['course_id'] = course_id

    @app.route('/quizz', methods=['GET', 'POST'])
    @login_required
    def quizz():
        if request.method == 'POST':
            course_id = request.form['course']
            course = Course.query.get(course_id)
            start_new_quiz(course.quiz_path, course_id)
            return redirect(url_for('quizz_question', question_id=0))
        modules = Module.query.all()
        return render_template('quizz.html', modules=modules)

    @app.route('/quizz_start', methods=['POST'])
    @login_required
    def quizz_start():
        course_id = request.form['course']
        course = Course.query.get(course_id)
        if not course:
            flash('Cours non trouvé.', 'danger')
            return redirect(url_for('quizz'))
        start_new_quiz(course.quiz_path, course_id)
        return redirect(url_for('quizz_question', question_id=0))

    @app.route('/quizz_reset')
    @login_required
    def quizz_reset():
        start_new_quiz(flask_session['quiz_path'], flask_session['course_id'])
        return redirect(url_for('quizz_question', question_id=0))

    @app.route('/quizz_retry')
    @login_required
    def quizz_retry():
        start_new_quiz(flask_session['quiz_path'], flask_session['course_id'])
        return redirect(url_for('quizz_question', question_id=0))

    @app.route('/quizz/question/<int:question_id>', methods=['GET', 'POST'])
    @login_required
    def quizz_question(question_id):
        if 'question_ids' not in flask_session or 'start_time' not in flask_session:
            start_new_quiz(flask_session['quiz_path'], flask_session['course_id'])
            return redirect(url_for('quizz_question', question_id=0))

        questions = load_questions(flask_session['quiz_path'])
        question = next((q for q in questions if q['id'] == flask_session['question_ids'][question_id]), None)

        if not question:
            start_new_quiz(flask_session['quiz_path'], flask_session['course_id'])
            return redirect(url_for('quizz_question', question_id=0))

        if request.method == 'POST':
            answer = request.form.get('answer')
            flask_session['answers'][str(question_id)] = answer

            if 'next' in request.form:
                next_question_id = question_id + 1
            elif 'prev' in request.form:
                next_question_id = question_id - 1
            else:
                next_question_id = question_id

            flask_session['current_question'] = next_question_id

            if next_question_id >= len(flask_session['question_ids']):
                return redirect(url_for('quizz_result'))
            else:
                return redirect(url_for('quizz_question', question_id=next_question_id))

        current_time = time.time()
        elapsed_time = current_time - flask_session['start_time']
        remaining_time = max(0, (flask_session['total_time'] - elapsed_time))

        if remaining_time <= 0:
            return redirect(url_for('quizz_result'))

        selected_choice = flask_session['answers'].get(str(question_id), None)
        progress = (question_id + 1) / len(flask_session['question_ids']) * 100

        return render_template(
            'quizz_question.html',
            question=question,
            question_id=question_id,
            current_question_number=question_id + 1,
            progress=progress,
            timer=remaining_time,
            selected_choice=selected_choice
        )

    @app.route('/quizz/result')
    @login_required
    def quizz_result():
        if 'question_ids' not in flask_session or 'answers' not in flask_session:
            start_new_quiz(flask_session['quiz_path'], flask_session['course_id'])
            return redirect(url_for('quizz_question', question_id=0))

        questions = load_questions(flask_session['quiz_path'])
        correct_answers = 0
        for i, question_id in enumerate(flask_session['question_ids']):
            question = next((q for q in questions if q['id'] == question_id), None)
            if question and flask_session['answers'].get(str(i)) == question['correct_answer']:
                correct_answers += 1
        flask_session['score'] = correct_answers

        # Enregistrer les résultats du quiz
        if current_user.is_authenticated and isinstance(current_user, Student):
            result = QuizScore(
                student_id=current_user.id,
                course_id=flask_session['course_id'],
                quiz_path=flask_session['quiz_path'],
                score=correct_answers,
                attempt_datetime=datetime.datetime.now(),
                attempts=flask_session.get('attempts', 1)
            )
            db.session.add(result)
            db.session.commit()
        else:
            flash('Vous devez être un étudiant pour enregistrer les résultats du quiz.', 'danger')

        return render_template('quizz_result.html', score=correct_answers)

    @app.route('/quizz/details')
    @login_required
    def quizz_details():
        if 'question_ids' not in flask_session or 'answers' not in flask_session:
            start_new_quiz(flask_session['quiz_path'], flask_session['course_id'])
            return redirect(url_for('quizz_question', question_id=0))

        questions = load_questions(flask_session['quiz_path'])
        question_list = [next((q for q in questions if q['id'] == qid), None) for qid in flask_session['question_ids']]
        answers = flask_session.get('answers', {})
        return render_template('quizz_details.html', questions=question_list, answers=answers, enumerate=enumerate, str=str)

    @app.route('/add_module_form')
    @login_required
    def add_module_form():
        if not isinstance(current_user, Professor):
            flash('Vous devez être professeur pour accéder à cette page.', 'danger')
            return redirect(url_for('dashboard'))
        return render_template('add_module.html')

    @app.route('/add_module', methods=['POST'])
    @login_required
    def add_module():
        if not isinstance(current_user, Professor):
            flash('Vous devez être professeur pour effectuer cette action.', 'danger')
            return redirect(url_for('dashboard'))

        title = request.form['title']

        if not title:
            flash('Le titre du module est requis.', 'danger')
            return redirect(url_for('add_module_form'))

        # Ajouter le module à la base de données
        new_module = Module(title=title, professor_id=current_user.id)
        db.session.add(new_module)
        db.session.commit()

        flash('Module ajouté avec succès!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/add_course_form')
    @login_required
    def add_course_form():
        if not isinstance(current_user, Professor):
            flash('Vous devez être professeur pour accéder à cette page.', 'danger')
            return redirect(url_for('dashboard'))
        modules = Module.query.filter_by(professor_id=current_user.id).all()
        return render_template('add_course.html', modules=modules)

    @app.route('/add_course', methods=['POST'])
    @login_required
    def add_course():
        if not isinstance(current_user, Professor):
            flash('Vous devez être professeur pour effectuer cette action.', 'danger')
            return redirect(url_for('dashboard'))

        title = request.form['title']
        content = request.form['content']
        module_id = request.form['module_id']
        file_path = request.files['file_path']
        quiz_path = request.files['quiz_path']

        if not title or not content or not module_id or not file_path or not quiz_path:
            flash('Tous les champs sont requis.', 'danger')
            return redirect(url_for('add_course_form'))

        # Créer les répertoires si nécessaire
        course_dir = 'static/courses'
        quiz_dir = 'static/quizzes'
        if not os.path.exists(course_dir):
            os.makedirs(course_dir)
        if not os.path.exists(quiz_dir):
            os.makedirs(quiz_dir)

        # Sauvegarder les fichiers
        course_file_path = os.path.join(course_dir, file_path.filename)
        quiz_file_path = os.path.join(quiz_dir, quiz_path.filename)
        file_path.save(course_file_path)
        quiz_path.save(quiz_file_path)

        # Ajouter le cours à la base de données
        new_course = Course(
            title=title,
            content=content,
            file_path=course_file_path,
            quiz_path=quiz_file_path,
            module_id=module_id
        )
        db.session.add(new_course)
        db.session.commit()

        flash('Cours ajouté avec succès!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/flashcard')
    @login_required
    def flashcard():
        course_id = request.args.get('course_id')
        course = Course.query.get(course_id)

        if not course or not course.quiz_path:
            return jsonify({'error': 'No flashcards found'}), 404

        questions = load_questions(course.quiz_path)
        flashcard = random.choice(questions)
        return jsonify({'question': flashcard['question'], 'answer': flashcard['correct_answer']})

    @app.route('/flashcard_page')
    @login_required
    def flashcard_page():
        courses = Course.query.all()
        return render_template('flashcard.html', courses=courses)

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))
