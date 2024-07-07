from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/quiz')
def quiz():
    token = session.get('token')
    logging.debug(f"Accessing quiz with token: {token}")
    if not token:
        flash('Invalid token, please login again')
        logging.error("Invalid token")
        return redirect(url_for('login'))
    try:
        decoded = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        logging.debug(f"Token decoded: {decoded}")
        questions = fetch_questions()
        result = session.pop('result', None)  # Retrieve and remove result from session
        return render_template('quiz.html', questions=questions, result=result)
    except jwt.ExpiredSignatureError:
        flash('Session expired, please login again')
        logging.error("Session expired")
        return redirect(url_for('login'))
    except jwt.InvalidTokenError:
        flash('Invalid token, please login again')
        logging.error("Invalid token")
        return redirect(url_for('login'))

def fetch_questions():
    response = requests.get('https://opentdb.com/api.php?amount=10&type=multiple')
    data = response.json()
    return data['results']

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    # Process the submitted quiz answers here
    submitted_answers = request.form
    correct_answers = fetch_questions()  # Fetch correct answers again (ideally should store initially)
    
    score = 0
    for i, question in enumerate(correct_answers):
        if submitted_answers.get(f'question{i+1}') == question['correct_answer']:
            score += 1

    # Store the result in the session
    session['result'] = f'You scored {score} out of {len(correct_answers)}'

    flash('Quiz submitted successfully!')
    return redirect(url_for('quiz'))

if __name__ == '__main__':
    # Ensure the database and tables are created
    db.create_all()
    app.run(debug=True)
