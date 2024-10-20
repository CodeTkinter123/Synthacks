from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import pickle
import numpy as np


app = Flask(__name__)
app.config['SECRET_KEY'] = 'key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///synt.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
model = pickle.load(open('heart.pkl','rb'))

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/check/")
def home():
    return render_template('improved.html')

def custom_function(user_input):
    result = f"Processed Data: {user_input}"
    return result

@app.route('/parameter-explanation/')
def parameter_explanation():
    return render_template("home.html")
@app.route('/process', methods=['POST'])
def process():
    data = request.json['data']
    result = data
    for i in range(len(result)):
        result[i] = float(result[i])
    array = np.array(result)
    array = array.reshape(1, -1)
    result = model.predict(array)
    probs = model.predict_proba(array)
    no_heart_disease = probs[0][0]
    print(float(no_heart_disease))
    heart_disease = 1-no_heart_disease
    heart_disease *= 100
    no_heart_disease *= 100
    yash = "There is a %i percentage chance that the patient has no heart disease and %i percentage chance that the person has a heart disease." %(no_heart_disease, heart_disease)
    whetherornot = int(result[0])
    return jsonify(result=yash)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route("/login/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard', username=username))
        else:
            flash('Login failed. Check your username and/or password.', 'danger')
    return render_template('login.html')

@app.route("/dashboard/<username>")
@login_required
def dashboard(username):
    user = User.query.filter_by(username=username).first()
    if user and user.id == current_user.id:
        return render_template('home.html', user=user)
    else:
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
