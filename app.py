import random
from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdbname.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# SQLAlchemy User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

# Function to generate JWT token
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

# Jinja filter to randomize options
@app.template_filter('randomize')
def randomize_filter(sequence):
    random.shuffle(sequence)
    return sequence

# Homepage route
@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        logging.debug(f"Login attempt for email: {email}")

        if not email or not password:
            flash('Email and Password are required')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()
        if user:
            logging.debug(f"User found: {user.email}")
        else:
            logging.debug(f"User not found: {email}")

        if user and check_password_hash(user.password_hash, password):
            token = generate_token(user.id)
            session['token'] = token  # Store the token in the session
            logging.debug(f"Login successful for email: {email}")
            return redirect(url_for('quiz'))
        flash('Invalid credentials')
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        logging.debug(f"Attempting registration for email: {email}")
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
        else:
            password_hash = generate_password_hash(password)
            new_user = User(email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            logging.debug(f"Registration successful for email: {email}")
            flash('Registration successful, please login')
            return redirect(url_for('login'))
    return render_template('register.html')

# Quiz route - displays quiz categories
@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

# Route for General Knowledge quiz
@app.route('/general_knowledge_quiz')
def general_knowledge_quiz():
    token = session.get('token')
    logging.debug(f"Accessing General Knowledge quiz with token: {token}")
    if not token:
        flash('Invalid token, please login again')
        logging.error("Invalid token")
        return redirect(url_for('login'))
    
    # Fetch questions for General Knowledge category
    questions = fetch_questions(amount=10, category=9, difficulty='easy')
    result = session.pop('result', None)  # Retrieve and remove result from session
    return render_template('quiz.html', questions=questions, result=result)

# Route for Politics quiz
@app.route('/politics_quiz')
def politics_quiz():
    token = session.get('token')
    logging.debug(f"Accessing Politics quiz with token: {token}")
    if not token:
        flash('Invalid token, please login again')
        logging.error("Invalid token")
        return redirect(url_for('login'))
    
    # Fetch questions for Politics category
    questions = fetch_questions(amount=10, category=24)
    result = session.pop('result', None)  # Retrieve and remove result from session
    return render_template('quiz.html', questions=questions, result=result)

# Route for Sports quiz
@app.route('/sports_quiz')
def sports_quiz():
    token = session.get('token')
    logging.debug(f"Accessing Sports quiz with token: {token}")
    if not token:
        flash('Invalid token, please login again')
        logging.error("Invalid token")
        return redirect(url_for('login'))
    
    # Fetch questions for Sports category
    questions = fetch_questions(amount=10, category=21)
    result = session.pop('result', None)  # Retrieve and remove result from session
    return render_template('quiz.html', questions=questions, result=result)

# Function to fetch questions from API
def fetch_questions(amount=10, category=None, difficulty=None):
    url = f'https://opentdb.com/api.php?amount={amount}'
    if category:
        url += f'&category={category}'
    if difficulty:
        url += f'&difficulty={difficulty}'
    
    response = requests.get(url)
    data = response.json()
    return data['results']

# Route to submit quiz answers
@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    submitted_answers = request.form
    correct_answers = fetch_questions()  # Fetch correct answers again (ideally should store initially)
    
    score = 0
    for i, question in enumerate(correct_answers):
        if submitted_answers.get(f'question{i+1}') == question['correct_answer']:
            score += 1

    session['result'] = f'You scored {score} out of {len(correct_answers)}'
    return redirect(url_for('result'))


# Route to display quiz result
@app.route('/result')
def result():
    result = session.get('result')
    if result:
        # Clear the result from session
        session.pop('result', None)
        return render_template('result.html', result=result)
    else:
        flash('No quiz result available. Please take the quiz first.')
        return redirect(url_for('quiz'))

if __name__ == '__main__':
    # Create database tables if they don't exist
    db.create_all()
    app.run(debug=True)
