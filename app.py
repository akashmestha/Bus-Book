from flask import Flask, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'bus_booking'
mysql = MySQL(app)

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# User and Bus Owner Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['user_type'] = user[3]
            return redirect('/dashboard')
        else:
            flash("Invalid username or password!")
    return render_template('login.html')

# User and Bus Owner Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users (username, password, user_type) VALUES (%s, %s, %s)",
                       (username, password, user_type))
        mysql.connection.commit()
        flash("Account created successfully!")
        return redirect('/login')
    return render_template('signup.html')

# Dashboard (User or Owner)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if session['user_type'] == 'user':
        return render_template('user_dashboard.html')
    elif session['user_type'] == 'owner':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM buses WHERE owner_id=%s", (session['user_id'],))
        buses = cursor.fetchall()
        return render_template('owner_dashboard.html', buses=buses)

# Add Bus (Owner Only)
@app.route('/add_bus', methods=['GET', 'POST'])
def add_bus():
    if session.get('user_type') != 'owner':
        return redirect('/')
    if request.method == 'POST':
        name = request.form['name']
        source = request.form['source']
        destination = request.form['destination']
        date = request.form['date']
        time = request.form['time']
        price = request.form['price']
        total_seats = request.form['total_seats']
        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO buses (owner_id, name, source, destination, date, time, price, total_seats, available_seats) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (session['user_id'], name, source, destination, date, time, price, total_seats, total_seats))
        mysql.connection.commit()
        return redirect('/dashboard')
    return render_template('add_bus.html')

# Search Buses
@app.route('/search', methods=['POST'])
def search():
    source = request.form['source']
    destination = request.form['destination']
    date = request.form['date']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM buses WHERE source=%s AND destination=%s AND date=%s AND available_seats > 0",
                   (source, destination, date))
    buses = cursor.fetchall()
    return render_template('search_results.html', buses=buses)

# Book Bus
@app.route('/book/<int:bus_id>', methods=['POST'])
def book(bus_id):
    seats = int(request.form['seats'])
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT price, available_seats FROM buses WHERE id=%s", (bus_id,))
    bus = cursor.fetchone()
    if bus[1] < seats:
        flash("Not enough seats available!")
        return redirect('/dashboard')
    total_price = seats * bus[0]
    cursor.execute("INSERT INTO bookings (user_id, bus_id, seats_booked, total_price) VALUES (%s, %s, %s, %s)",
                   (session['user_id'], bus_id, seats, total_price))
    cursor.execute("UPDATE buses SET available_seats=available_seats-%s WHERE id=%s", (seats, bus_id))
    mysql.connection.commit()
    return render_template('payment.html', total_price=total_price)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
