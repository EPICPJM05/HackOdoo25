from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
import os
import datetime
from functools import wraps
import csv
from io import StringIO

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Set the template folder to the Front-end directory
template_dir = os.path.join(os.path.dirname(current_dir), 'Front-end')

app = Flask(__name__, template_folder=template_dir, static_folder=os.path.join(current_dir, 'static'))
app.secret_key = 'your-secret-key-here'

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'skill_swap'
}

# File upload configuration
UPLOAD_FOLDER = os.path.join(current_dir, 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Admin access required.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Active Users: count all users
    cursor.execute("SELECT COUNT(*) AS active_users FROM users")
    active_users = cursor.fetchone()['active_users']

    # Skills Available: count distinct skill names
    cursor.execute("SELECT COUNT(DISTINCT skill_name) AS skills_available FROM skills_offered")
    skills_available = cursor.fetchone()['skills_available']

    # Successful Swaps: count completed swaps
    cursor.execute("SELECT COUNT(*) AS successful_swaps FROM swap_requests WHERE status = 'completed'")
    successful_swaps = cursor.fetchone()['successful_swaps']

    # % Satisfaction: average rating from feedback (0 if no feedback)
    cursor.execute("SELECT AVG(rating) AS avg_rating FROM feedback")
    avg_rating = cursor.fetchone()['avg_rating']
    avg_rating = round(avg_rating, 1) if avg_rating is not None else 0

    cursor.close()
    conn.close()

    return render_template(
        'index.html',
        active_users=active_users,
        skills_available=skills_available,
        successful_swaps=successful_swaps,
        avg_rating=avg_rating
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        location = request.form.get('location', '')
        availability = request.form.get('availability', '')
        
        # Handle file upload
        photo_url = ''
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_url = f"uploads/{filename}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered.', 'error')
            cursor.close()
            conn.close()
            return render_template('register.html')
        
        # Hash password and insert user
        hashed_password = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password, location, photo_url, availability, is_public) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (name, email, hashed_password, location, photo_url, availability, True)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get user info
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    # Get skills offered
    cursor.execute("SELECT * FROM skills_offered WHERE user_id = %s", (session['user_id'],))
    skills_offered = cursor.fetchall()
    
    # Get skills wanted
    cursor.execute("SELECT * FROM skills_wanted WHERE user_id = %s", (session['user_id'],))
    skills_wanted = cursor.fetchall()
    
    # Get swap requests
    cursor.execute("""
        SELECT sr.*, u.name as requester_name, u2.name as receiver_name 
        FROM swap_requests sr 
        JOIN users u ON sr.requester_id = u.id 
        JOIN users u2 ON sr.receiver_id = u2.id 
        WHERE sr.requester_id = %s OR sr.receiver_id = %s 
        ORDER BY sr.timestamp DESC
    """, (session['user_id'], session['user_id']))
    swap_requests = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', user=user, skills_offered=skills_offered, 
                         skills_wanted=skills_wanted, swap_requests=swap_requests)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE id = %s AND is_public = 1", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        flash('Profile not found or private.', 'error')
        return redirect(url_for('index'))
    
    # Get skills offered
    cursor.execute("SELECT * FROM skills_offered WHERE user_id = %s", (user_id,))
    skills_offered = cursor.fetchall()
    
    # Get skills wanted
    cursor.execute("SELECT * FROM skills_wanted WHERE user_id = %s", (user_id,))
    skills_wanted = cursor.fetchall()
    
    # Get average rating
    cursor.execute("""
        SELECT AVG(f.rating) as avg_rating, COUNT(f.rating) as total_ratings
        FROM feedback f
        JOIN swap_requests sr ON f.swap_id = sr.id
        WHERE (sr.requester_id = %s OR sr.receiver_id = %s) AND sr.status = 'completed'
    """, (user_id, user_id))
    rating_data = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('profile.html', user=user, skills_offered=skills_offered, 
                         skills_wanted=skills_wanted, rating_data=rating_data)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form['name']
        location = request.form.get('location', '')
        availability = request.form.get('availability', '')
        is_public = 'is_public' in request.form
        
        # Handle file upload
        photo_url = request.form.get('current_photo', '')
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                photo_url = f"uploads/{filename}"
        
        cursor.execute(
            "UPDATE users SET name = %s, location = %s, photo_url = %s, availability = %s, is_public = %s WHERE id = %s",
            (name, location, photo_url, availability, is_public, session['user_id'])
        )
        conn.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return render_template('edit_profile.html', user=user)

@app.route('/add_skill_offered', methods=['POST'])
@login_required
def add_skill_offered():
    skill_name = request.form['skill_name']
    description = request.form.get('description', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO skills_offered (user_id, skill_name, description) VALUES (%s, %s, %s)",
        (session['user_id'], skill_name, description)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Skill added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_skill_wanted', methods=['POST'])
@login_required
def add_skill_wanted():
    skill_name = request.form['skill_name']
    description = request.form.get('description', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO skills_wanted (user_id, skill_name, description) VALUES (%s, %s, %s)",
        (session['user_id'], skill_name, description)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Skill wanted added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_skill_offered/<int:skill_id>')
@login_required
def delete_skill_offered(skill_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skills_offered WHERE id = %s AND user_id = %s", 
                  (skill_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Skill removed successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_skill_wanted/<int:skill_id>')
@login_required
def delete_skill_wanted(skill_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skills_wanted WHERE id = %s AND user_id = %s", 
                  (skill_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Skill wanted removed successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('search.html', results=[])
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT DISTINCT u.id, u.name, u.location, u.availability, u.photo_url,
               GROUP_CONCAT(DISTINCT so.skill_name) as skills_offered
        FROM users u
        LEFT JOIN skills_offered so ON u.id = so.user_id
        WHERE u.is_public = 1 AND (so.skill_name LIKE %s OR u.name LIKE %s)
        GROUP BY u.id
    """, (f'%{query}%', f'%{query}%'))
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('search.html', results=results, query=query)

@app.route('/send_swap_request/<int:receiver_id>', methods=['POST'])
@login_required
def send_swap_request(receiver_id):
    if receiver_id == session['user_id']:
        flash('You cannot send a swap request to yourself.', 'error')
        return redirect(url_for('search'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if request already exists
    cursor.execute("""
        SELECT id FROM swap_requests 
        WHERE requester_id = %s AND receiver_id = %s AND status = 'pending'
    """, (session['user_id'], receiver_id))
    
    if cursor.fetchone():
        flash('Swap request already sent.', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('search'))
    
    cursor.execute(
        "INSERT INTO swap_requests (requester_id, receiver_id, status, timestamp) VALUES (%s, %s, %s, %s)",
        (session['user_id'], receiver_id, 'pending', datetime.datetime.now())
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Swap request sent successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/respond_swap_request/<int:request_id>/<action>')
@login_required
def respond_swap_request(request_id, action):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if action == 'accept':
        cursor.execute(
            "UPDATE swap_requests SET status = 'accepted' WHERE id = %s AND receiver_id = %s",
            (request_id, session['user_id'])
        )
        flash('Swap request accepted!', 'success')
    elif action == 'reject':
        cursor.execute(
            "UPDATE swap_requests SET status = 'rejected' WHERE id = %s AND receiver_id = %s",
            (request_id, session['user_id'])
        )
        flash('Swap request rejected.', 'info')
    elif action == 'complete':
        cursor.execute(
            "UPDATE swap_requests SET status = 'completed' WHERE id = %s AND (requester_id = %s OR receiver_id = %s)",
            (request_id, session['user_id'], session['user_id'])
        )
        flash('Swap marked as completed!', 'success')
    elif action == 'delete':
        cursor.execute(
            "DELETE FROM swap_requests WHERE id = %s AND requester_id = %s AND status = 'pending'",
            (request_id, session['user_id'])
        )
        flash('Swap request deleted.', 'info')
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/give_feedback/<int:swap_id>', methods=['POST'])
@login_required
def give_feedback(swap_id):
    rating = request.form['rating']
    comment = request.form.get('comment', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user is part of this swap
    cursor.execute("""
        SELECT id FROM swap_requests 
        WHERE id = %s AND (requester_id = %s OR receiver_id = %s) AND status = 'completed'
    """, (swap_id, session['user_id'], session['user_id']))
    
    if not cursor.fetchone():
        flash('Invalid swap request.', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Check if feedback already given
    cursor.execute("SELECT id FROM feedback WHERE swap_id = %s AND rater_id = %s", 
                  (swap_id, session['user_id']))
    
    if cursor.fetchone():
        flash('You have already given feedback for this swap.', 'error')
        cursor.close()
        conn.close()
        return redirect(url_for('dashboard'))
    
    cursor.execute(
        "INSERT INTO feedback (swap_id, rater_id, rating, comment) VALUES (%s, %s, %s, %s)",
        (swap_id, session['user_id'], rating, comment)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Feedback submitted successfully!', 'success')
    return redirect(url_for('dashboard'))

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if admin and admin['password'] == password:
            session['admin_id'] = admin['id']
            session['admin_email'] = admin['email']
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get stats
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    
    cursor.execute("SELECT COUNT(*) as total_swaps FROM swap_requests")
    total_swaps = cursor.fetchone()['total_swaps']
    
    cursor.execute("SELECT COUNT(*) as completed_swaps FROM swap_requests WHERE status = 'completed'")
    completed_swaps = cursor.fetchone()['completed_swaps']
    
    cursor.execute("SELECT COUNT(*) as total_feedback FROM feedback")
    total_feedback = cursor.fetchone()['total_feedback']
    
    cursor.close()
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users, total_swaps=total_swaps,
                         completed_swaps=completed_swaps, total_feedback=total_feedback)

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users ORDER BY id DESC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/ban_user/<int:user_id>')
@admin_required
def ban_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_public = 0 WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('User banned successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/swaps')
@admin_required
def admin_swaps():
    status_filter = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if status_filter:
        cursor.execute("""
            SELECT sr.*, u1.name as requester_name, u2.name as receiver_name 
            FROM swap_requests sr 
            JOIN users u1 ON sr.requester_id = u1.id 
            JOIN users u2 ON sr.receiver_id = u2.id 
            WHERE sr.status = %s ORDER BY sr.timestamp DESC
        """, (status_filter,))
    else:
        cursor.execute("""
            SELECT sr.*, u1.name as requester_name, u2.name as receiver_name 
            FROM swap_requests sr 
            JOIN users u1 ON sr.requester_id = u1.id 
            JOIN users u2 ON sr.receiver_id = u2.id 
            ORDER BY sr.timestamp DESC
        """)
    
    swaps = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin_swaps.html', swaps=swaps, status_filter=status_filter)

@app.route('/admin/download_report/<report_type>')
@admin_required
def download_report(report_type):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if report_type == 'users':
        cursor.execute("SELECT id, name, email, location, availability, is_public, created_at FROM users")
        data = cursor.fetchall()
        filename = 'user_activity.csv'
    elif report_type == 'swaps':
        cursor.execute("""
            SELECT sr.id, u1.name as requester, u2.name as receiver, sr.status, sr.timestamp
            FROM swap_requests sr 
            JOIN users u1 ON sr.requester_id = u1.id 
            JOIN users u2 ON sr.receiver_id = u2.id
        """)
        data = cursor.fetchall()
        filename = 'swap_stats.csv'
    elif report_type == 'feedback':
        cursor.execute("""
            SELECT f.id, u.name as rater, f.rating, f.comment, f.created_at
            FROM feedback f
            JOIN users u ON f.rater_id = u.id
        """)
        data = cursor.fetchall()
        filename = 'feedback_logs.csv'
    
    cursor.close()
    conn.close()
    
    # Create CSV
    output = StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Admin logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/chat/<int:swap_id>')
@login_required
def chat(swap_id):
    # Check if user is part of this swap and swap is accepted
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM swap_requests WHERE id = %s AND status = 'accepted' AND (requester_id = %s OR receiver_id = %s)", (swap_id, session['user_id'], session['user_id']))
    swap = cursor.fetchone()
    if not swap:
        cursor.close()
        conn.close()
        return "Unauthorized", 403
    # Get other user info
    other_id = swap['receiver_id'] if swap['requester_id'] == session['user_id'] else swap['requester_id']
    cursor.execute("SELECT id, name, photo_url FROM users WHERE id = %s", (other_id,))
    other_user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('chat_modal.html', swap_id=swap_id, other_user=other_user)

@app.route('/api/messages/<int:swap_id>')
@login_required
def get_messages(swap_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM swap_requests WHERE id = %s AND (requester_id = %s OR receiver_id = %s)", (swap_id, session['user_id'], session['user_id']))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    cursor.execute("SELECT m.*, u.name, u.photo_url FROM messages m JOIN users u ON m.sender_id = u.id WHERE m.swap_id = %s ORDER BY m.timestamp ASC", (swap_id,))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(messages)

@app.route('/api/send_message/<int:swap_id>', methods=['POST'])
@login_required
def send_message(swap_id):
    msg = request.form.get('message', '').strip()
    if not msg:
        return jsonify({'error': 'Empty message'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if user is part of this swap
    cursor.execute("SELECT * FROM swap_requests WHERE id = %s AND (requester_id = %s OR receiver_id = %s)", (swap_id, session['user_id'], session['user_id']))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    cursor.execute("INSERT INTO messages (swap_id, sender_id, message) VALUES (%s, %s, %s)", (swap_id, session['user_id'], msg))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True) 