import os
import sqlite3
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

os.makedirs('/data', exist_ok=True)  # Ensures /data exists for Railway persistence
DATABASE_URL = os.environ.get("DATABASE_URL", "/data/restaurant.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_default_secret")
DATABASE_URL = os.environ.get("DATABASE_URL", "/data/restaurant.db")
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CATEGORIES = [
    "Appetizer", "Soup", "Salad", "Sandwich", "Burger", "Pizza", "Pasta", "Meat", "Seafood", "Vegetarian", "Vegan",
    "Dessert", "Beverage", "Breakfast", "Brunch", "Lunch", "Dinner", "Snack", "Side Dish", "Sushi", "Noodle",
    "Rice Dish", "BBQ", "Taco", "Curry", "Fried Food", "Stew", "Wrap", "Deli", "Ice Cream", "Cake", "Pie"
]

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS plates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant TEXT NOT NULL,
            plate TEXT NOT NULL,
            category TEXT,
            address TEXT NOT NULL,
            zipcode TEXT,
            city TEXT,
            state TEXT,
            rating INTEGER NOT NULL,
            comment TEXT,
            photo TEXT,
            latitude REAL,
            longitude REAL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            plate_id INTEGER,
            PRIMARY KEY (user_id, plate_id)
        )
    ''')
    conn.commit()
    conn.close()

# Always create tables on startup, even with Gunicorn
init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, generate_password_hash(password)))
            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('Please log in to view your account.', 'warning')
        return redirect(url_for('login'))
    conn = get_db_connection()
    favorites = conn.execute('''
        SELECT plates.* FROM plates
        JOIN favorites ON plates.id = favorites.plate_id
        WHERE favorites.user_id = ?
        ORDER BY plates.id DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('account.html', favorites=favorites)

@app.route('/favorite/<int:plate_id>', methods=['POST'])
def favorite(plate_id):
    if 'user_id' not in session:
        flash('Please log in to favorite plates.', 'warning')
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute(
        'INSERT OR IGNORE INTO favorites (user_id, plate_id) VALUES (?, ?)',
        (session['user_id'], plate_id))
    conn.commit()
    conn.close()
    flash('Added to My Next Meal!', 'success')
    return redirect(url_for('index'))

@app.route('/')
def index():
    conn = get_db_connection()
    plates = conn.execute('SELECT * FROM plates ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', plates=plates)

@app.route('/post', methods=('GET', 'POST'))
def post():
    if request.method == 'POST':
        restaurant = request.form['restaurant']
        plate = request.form['plate']
        category = request.form.get('category')
        address = request.form['address']
        zipcode = request.form.get('zipcode')
        city = request.form.get('city')
        state = request.form.get('state')
        rating = request.form['rating']
        comment = request.form['comment']
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        photo = request.files.get('photo')
        photo_filename = None
        if photo and photo.filename:
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO plates (restaurant, plate, category, address, zipcode, city, state, rating, comment, photo, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (restaurant, plate, category, address, zipcode, city, state, rating, comment, photo_filename, lat, lng))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('post.html', categories=CATEGORIES)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    conn = get_db_connection()
    plates = conn.execute(
        """SELECT * FROM plates
           WHERE restaurant LIKE ?
           OR plate LIKE ?
           OR category LIKE ?
           OR address LIKE ?
           OR zipcode LIKE ?
           OR city LIKE ?
           OR state LIKE ?
           ORDER BY id DESC""",
        (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%')
    ).fetchall()
    conn.close()
    return render_template('index.html', plates=plates, search=query)

@app.route('/spin')
def spin():
    zipcode = request.args.get('zipcode', '')
    conn = get_db_connection()
    plates = conn.execute(
        "SELECT * FROM plates WHERE zipcode = ?", (zipcode,)
    ).fetchall()
    conn.close()
    plate = random.choice(plates) if plates else None
    return render_template('spin.html', plate=plate, zipcode=zipcode)

@app.route('/seed_rochester')
def seed_rochester():
    dummy_plates = [
        ("Lilac City Grill", "New England Clam Chowder", "Soup", "103 N Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 5, "Creamy and full of clams.", "clamchowder.jpg", 43.3045, -70.9786),
        ("Spaulding Steak & Ale", "Prime Rib", "Meat", "500 Spaulding Turnpike, Rochester, NH, USA", "03867", "Rochester", "NH", 4, "Tender, juicy prime rib.", "primerib.jpg", 43.3040, -70.9872),
        ("China Palace", "General Tso's Chicken", "Fried Food", "21 S Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 4, "Crispy and tangy.", "generaltso.jpg", 43.3018, -70.9727),
        ("Revolution Taproom & Grill", "Fish Tacos", "Taco", "61 N Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 5, "Fresh and zesty tacos.", "fishtacos.jpg", 43.3057, -70.9782),
        ("Dos Amigos Burritos", "Vegetarian Burrito", "Vegetarian", "55 N Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 5, "Loaded with veggies!", "vegburrito.jpg", 43.3052, -70.9783),
        ("Granite Steak & Grill", "Cheesecake", "Dessert", "11 Farmington Rd, Rochester, NH, USA", "03867", "Rochester", "NH", 5, "Rich and creamy.", "cheesecake.jpg", 43.2971, -70.9765),
        ("La Corona Mexican Restaurant", "Chicken Enchiladas", "Wrap", "83 S Main St, Rochester, NH, USA", "03867", "Rochester", "NH", 4, "Spicy and satisfying.", "enchiladas.jpg", 43.2993, -70.9726),
    ]
    conn = get_db_connection()
    for plate in dummy_plates:
        conn.execute('''
            INSERT INTO plates (restaurant, plate, category, address, zipcode, city, state, rating, comment, photo, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', plate)
    conn.commit()
    conn.close()
    return "Rochester NH dummy data loaded! <a href='/'>Back to feed</a>"

if __name__ == '__main__':
    app.run(debug=True)