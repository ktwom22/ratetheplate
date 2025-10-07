import os
import sqlite3
import random
import math
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_default_secret")
DATABASE_URL = os.environ.get("DATABASE_URL", "/data/restaurant.db")
os.makedirs('/data', exist_ok=True)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CATEGORIES = [
    "Appetizer", "Soup", "Salad", "Sandwich", "Burger", "Pizza", "Pasta", "Meat", "Seafood", "Vegetarian", "Vegan",
    "Dessert", "Beverage", "Breakfast", "Brunch", "Lunch", "Dinner", "Snack", "Side Dish", "Sushi", "Noodle",
    "Rice Dish", "BBQ", "Taco", "Curry", "Fried Food", "Stew", "Wrap", "Deli", "Ice Cream", "Cake", "Pie"
]

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def migrate_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Ensure reminder_freq column exists in users
    try:
        c.execute("ALTER TABLE users ADD COLUMN reminder_freq TEXT DEFAULT '1day';")
    except sqlite3.OperationalError:
        pass
    # Ensure user_id column exists in plates
    try:
        c.execute("ALTER TABLE plates ADD COLUMN user_id INTEGER;")
    except sqlite3.OperationalError:
        pass
    # Ensure created_at column exists in plates
    try:
        c.execute("ALTER TABLE plates ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
    except sqlite3.OperationalError:
        pass
    # Ensure rating column can be NULL (migrate if NOT NULL)
    # Check if plates.rating is defined as NOT NULL and migrate if so
    c.execute("PRAGMA table_info(plates);")
    cols = c.fetchall()
    for col in cols:
        if col[1] == "rating" and col[3] == 1:  # NOT NULL
            # Migrate table to allow rating to be NULL
            c.executescript('''
                CREATE TABLE IF NOT EXISTS plates_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    restaurant TEXT NOT NULL,
                    plate TEXT NOT NULL,
                    category TEXT,
                    address TEXT NOT NULL,
                    zipcode TEXT,
                    city TEXT,
                    state TEXT,
                    rating INTEGER,
                    comment TEXT,
                    photo TEXT,
                    latitude REAL,
                    longitude REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO plates_new
                    (id, user_id, restaurant, plate, category, address, zipcode, city, state, rating, comment, photo, latitude, longitude, created_at)
                SELECT
                    id, user_id, restaurant, plate, category, address, zipcode, city, state, rating, comment, photo, latitude, longitude, created_at
                FROM plates;
                DROP TABLE plates;
                ALTER TABLE plates_new RENAME TO plates;
            ''')
            break
    conn.commit()
    conn.close()

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            reminder_freq TEXT DEFAULT '1day'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS plates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            restaurant TEXT NOT NULL,
            plate TEXT NOT NULL,
            category TEXT,
            address TEXT NOT NULL,
            zipcode TEXT,
            city TEXT,
            state TEXT,
            rating INTEGER,
            comment TEXT,
            photo TEXT,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    migrate_db()

init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), email))
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

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        flash('Please log in to view your account.', 'warning')
        return redirect(url_for('login'))
    conn = get_db_connection()
    if request.method == 'POST':
        freq = request.form.get('reminder_freq', '1day')
        conn.execute('UPDATE users SET reminder_freq = ? WHERE id = ?', (freq, session['user_id']))
        conn.commit()
        flash('Reminder preference updated.', 'success')
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    reminder_freq = user['reminder_freq'] if user and 'reminder_freq' in user.keys() and user['reminder_freq'] else '1day'
    favorites = conn.execute('''
        SELECT plates.* FROM plates
        JOIN favorites ON plates.id = favorites.plate_id
        WHERE favorites.user_id = ?
        ORDER BY plates.id DESC
    ''', (session['user_id'],)).fetchall()
    plates = conn.execute('SELECT * FROM plates ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('account.html', favorites=favorites, plates=plates, reminder_freq=reminder_freq)

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
    return redirect(url_for('account'))

@app.route('/')
def index():
    conn = get_db_connection()
    plates = conn.execute('SELECT * FROM plates ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', plates=plates)

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    radius = request.args.get('radius', '')
    user_lat = request.args.get('lat')
    user_lng = request.args.get('lng')
    plates = []

    if radius and user_lat and user_lng:
        lat1, lon1 = float(user_lat), float(user_lng)
        conn = get_db_connection()
        all_plates = conn.execute("SELECT * FROM plates WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchall()
        plates = []
        for plate in all_plates:
            try:
                lat2, lon2 = float(plate['latitude']), float(plate['longitude'])
                dist = haversine(lat1, lon1, lat2, lon2)
                if dist < float(radius):
                    plates.append(plate)
            except (TypeError, ValueError):
                continue
        conn.close()
    else:
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

@app.route('/post', methods=('GET', 'POST'))
def post():
    if 'user_id' not in session:
        flash('Please log in to post.', 'warning')
        return redirect(url_for('login'))
    if request.method == 'POST':
        restaurant = request.form['restaurant']
        plate = request.form['plate']
        category = request.form.get('category')
        address = request.form['address']
        zipcode = request.form.get('zipcode')
        city = request.form.get('city')
        state = request.form.get('state')
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
            INSERT INTO plates (user_id, restaurant, plate, category, address, zipcode, city, state, comment, photo, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], restaurant, plate, category, address, zipcode, city, state, comment, photo_filename, lat, lng))
        conn.commit()
        conn.close()
        flash('Plate posted! You will be reminded to rate it.', 'success')
        return redirect(url_for('index'))
    return render_template('post.html', categories=CATEGORIES)

@app.route('/rate/<int:plate_id>', methods=['GET', 'POST'])
def rate_plate(plate_id):
    if 'user_id' not in session:
        flash('Please log in to rate your plate.', 'warning')
        return redirect(url_for('login'))
    conn = get_db_connection()
    plate = conn.execute('SELECT * FROM plates WHERE id = ?', (plate_id,)).fetchone()
    if not plate:
        flash('Plate not found.', 'danger')
        conn.close()
        return redirect(url_for('account'))
    if plate['user_id'] != session['user_id']:
        flash('You can only rate your own plates.', 'danger')
        conn.close()
        return redirect(url_for('account'))
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        conn.execute('UPDATE plates SET rating = ?, comment = ? WHERE id = ?', (rating, comment, plate_id))
        conn.commit()
        conn.close()
        flash('Rating updated!', 'success')
        return redirect(url_for('account'))
    conn.close()
    return render_template('rate_plate.html', plate=plate)

# (Demo) Email reminder job - call from cron or scheduler
def send_reminder(to_email, username, plate_id, plate_name):
    # Replace this with real email sending in production!
    print(f"Send reminder to {to_email}: Hi {username}, please rate your plate '{plate_name}' at http://yourdomain.com/rate/{plate_id}")

def run_reminder_job():
    conn = get_db_connection()
    now = datetime.datetime.utcnow()
    plates = conn.execute(
        '''SELECT plates.id, plates.plate, plates.rating, plates.created_at, users.email, users.username, users.reminder_freq
           FROM plates
           JOIN users ON plates.user_id = users.id
           WHERE (plates.rating IS NULL OR plates.rating = '')
        ''').fetchall()
    for plate in plates:
        freq = plate['reminder_freq'] if plate and 'reminder_freq' in plate.keys() and plate['reminder_freq'] else '1day'
        if not plate['email'] or freq == 'none':
            continue
        created = datetime.datetime.fromisoformat(plate['created_at'])
        send = False
        elapsed_minutes = (now - created).total_seconds() / 60
        elapsed_days = (now - created).days
        if freq == '45min' and 44 < elapsed_minutes < 46:
            send = True
        elif freq == '1day' and elapsed_days == 1:
            send = True
        elif freq == '1week' and elapsed_days == 7:
            send = True
        if send:
            send_reminder(plate['email'], plate['username'], plate['id'], plate['plate'])
    conn.close()

@app.after_request
def add_header(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    return response

if __name__ == '__main__':
    app.run(debug=True)