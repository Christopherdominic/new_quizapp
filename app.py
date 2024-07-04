from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
import jwt
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config["MONGO_URI"] = "mongodb://localhost:27017/yourdbname"
mongo = PyMongo(app)

def generate_token(user_id):
    payload = {
        'user_id': str(user_id),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({'username': username})
        if user and user['password'] == password:
            token = generate_token(user['_id'])
            return redirect(url_for('quiz', token=token))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if mongo.db.users.find_one({'username': username}):
            flash('Username already exists')
        else:
            mongo.db.users.insert_one({'username': username, 'password': password})
            flash('Registration successful, please login')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/quiz')
def quiz():
    token = request.args.get('token')
    try:
        jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return render_template('quiz.html')
    except jwt.ExpiredSignatureError:
        flash('Session expired, please login again')
        return redirect(url_for('login'))
    except jwt.InvalidTokenError:
        flash('Invalid token, please login again')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

