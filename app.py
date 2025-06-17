

from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load the trained model
model = pickle.load(open('liver_model.pkl', 'rb'))

# Insert a new user into the database
def insert_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

# Validate user credentials
def validate_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

# Save prediction record
def save_prediction(user_id, age, tb, ag, result):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (user_id, age, tb, ag, result) VALUES (?, ?, ?, ?, ?)", (user_id, age, tb, ag, result))
    conn.commit()
    conn.close()

# Retrieve prediction history
def get_history(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT age, tb, ag, result, timestamp FROM history WHERE user_id=? ORDER BY timestamp DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# Home Page (Prediction)
@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')

    result = ''
    if request.method == 'POST':
        try:
            age_raw = request.form.get('age')
            tb_raw = request.form.get('tb')
            ag_raw = request.form.get('ag')

            print(f"Received: Age={age_raw}, TB={tb_raw}, AG={ag_raw}")  # Debugging

            # Convert to numbers after stripping spaces
            age = int(age_raw.strip())
            tb = float(tb_raw.strip())
            ag = float(ag_raw.strip())

            prediction = model.predict([[age, tb, ag]])
            result = "High Risk of Liver Cirrhosis" if prediction[0] == 1 else "Low Risk of Liver Cirrhosis"

            save_prediction(session['user_id'], age, tb, ag, result)

        except Exception as e:
            print(f"Error during prediction: {e}")  # See exact error in terminal
            result = "Invalid input. Please enter only numbers."

    return render_template('index.html', result=result)

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        user_id = validate_user(request.form['username'], request.form['password'])
        if user_id:
            session['user_id'] = user_id
            session['username'] = request.form['username']
            return redirect('/')
        else:
            error = "Invalid credentials"
    return render_template('login.html', error=error)

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ''
    if request.method == 'POST':
        try:
            insert_user(request.form['username'], request.form['password'])
            return redirect('/login')
        except:
            error = "Username already exists"
    return render_template('register.html', error=error)

# Dashboard Page (Prediction History)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    history = get_history(session['user_id'])
    return render_template('dashboard.html', history=history)

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
