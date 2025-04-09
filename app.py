import os
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
import psycopg2.extras

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("PGHOST", "localhost"),
            dbname=os.environ.get("PGDATABASE", "utilities_db"),
            user=os.environ.get("PGUSER", "utilities_user"),
            password=os.environ.get("PGPASSWORD", "securepassword"),
            port=os.environ.get("PGPORT", "5432")
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'technician_id' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if not conn:
            flash('Could not connect to database', 'danger')
            return render_template('login.html')
        
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM technicians WHERE email = %s AND password = %s", (email, password))
        technician = cur.fetchone()
        cur.close()
        conn.close()
        
        if technician:
            session['technician_id'] = technician['id']
            session['technician_name'] = technician['name']
            session['technician_expertise'] = technician['expertise']
            session['technician_location'] = technician['location']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    if not conn:
        flash('Could not connect to database', 'danger')
        return render_template('dashboard.html', appointments=[])
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get current date in YYYY-MM-DD format for filtering
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get technician data
    expertise = session.get('technician_expertise')
    location = session.get('technician_location')
    
    # Find appointments matching technician expertise and location, and created today
    cur.execute("""
        SELECT * FROM appointments 
        WHERE location = %s 
        AND intent LIKE %s 
        AND DATE(created_at) = %s
        ORDER BY created_at DESC
    """, (location, f"%{expertise}%", today_date))
    
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('dashboard.html', appointments=appointments)

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    if not conn:
        flash('Could not connect to database', 'danger')
        return render_template('profile.html', technician=None)
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM technicians WHERE id = %s", (session['technician_id'],))
    technician = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('profile.html', technician=technician)

@app.route('/history')
@login_required
def history():
    conn = get_db_connection()
    if not conn:
        flash('Could not connect to database', 'danger')
        return render_template('history.html', appointments=[])
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get technician data
    expertise = session.get('technician_expertise')
    location = session.get('technician_location')
    
    # Find all appointments matching technician expertise and location
    cur.execute("""
        SELECT * FROM appointments 
        WHERE location = %s 
        AND intent LIKE %s 
        ORDER BY created_at DESC
    """, (location, f"%{expertise}%"))
    
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('history.html', appointments=appointments)

@app.route('/analytics')
@login_required
def analytics():
    conn = get_db_connection()
    if not conn:
        flash('Could not connect to database', 'danger')
        return render_template('analytics.html', analytics_data={})
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get technician data
    expertise = session.get('technician_expertise')
    location = session.get('technician_location')
    
    # Total appointments handled by this technician
    cur.execute("""
        SELECT COUNT(*) as total_appointments
        FROM appointments 
        WHERE location = %s 
        AND intent LIKE %s
    """, (location, f"%{expertise}%"))
    
    total_count = cur.fetchone()['total_appointments']
    
    # Appointments per day (last 7 days)
    cur.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM appointments 
        WHERE location = %s 
        AND intent LIKE %s
        AND created_at >= NOW() - INTERVAL '7 days'
        GROUP BY DATE(created_at)
        ORDER BY date
    """, (location, f"%{expertise}%"))
    
    daily_data = cur.fetchall()
    
    # Types of issues handled
    cur.execute("""
        SELECT intent, COUNT(*) as count
        FROM appointments 
        WHERE location = %s 
        AND intent LIKE %s
        GROUP BY intent
        ORDER BY count DESC
    """, (location, f"%{expertise}%"))
    
    issues_data = cur.fetchall()
    
    cur.close()
    conn.close()
    
    # Format data for charts
    dates = [row['date'].strftime('%Y-%m-%d') for row in daily_data]
    daily_counts = [row['count'] for row in daily_data]
    
    issues = [row['intent'] for row in issues_data]
    issue_counts = [row['count'] for row in issues_data]
    
    analytics_data = {
        'total_count': total_count,
        'dates': dates,
        'daily_counts': daily_counts,
        'issues': issues,
        'issue_counts': issue_counts
    }
    
    return render_template('analytics.html', analytics_data=analytics_data)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
