import os
import csv
import io
import json
import logging
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
import psycopg2
import psycopg2.extras

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.environ.get("SESSION_SECRET", "default_secret_key"))

# Database connection function
def get_db_connection():
    try:
        # First try to use DATABASE_URL (common in Railway, Heroku, Render)
        database_url = os.environ.get("DATABASE_URL")
        
        if database_url:
            # Handle Heroku's postgres:// vs postgresql:// issue
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            
            conn = psycopg2.connect(database_url)
            conn.autocommit = True
            return conn
        
        # Fall back to individual parameters
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
    
    total_count_result = cur.fetchone()
    total_count = total_count_result['total_appointments'] if total_count_result else 0
    
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

@app.route('/export/history/csv')
@login_required
def export_history_csv():
    conn = get_db_connection()
    if not conn:
        flash('Could not connect to database', 'danger')
        return redirect(url_for('history'))
    
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
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Time Slot', 'Client Name', 'Issue Type', 'Problem Description', 'Location', 'Contact'])
    
    # Write appointment data
    for appointment in appointments:
        writer.writerow([
            appointment['created_at'].strftime('%Y-%m-%d'),
            appointment['time_slot'],
            appointment['name'],
            appointment['intent'],
            appointment['problem_description'],
            appointment['location'],
            appointment['contact']
        ])
    
    # Prepare response
    output.seek(0)
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"appointment_history_{now}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route('/export/analytics/csv')
@login_required
def export_analytics_csv():
    conn = get_db_connection()
    if not conn:
        flash('Could not connect to database', 'danger')
        return redirect(url_for('analytics'))
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get technician data
    expertise = session.get('technician_expertise')
    location = session.get('technician_location')
    technician_name = session.get('technician_name')
    
    # Get analytics data
    
    # Daily appointment counts
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
    
    # Issue type distribution
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
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write report header
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    writer.writerow(['Analytics Report'])
    writer.writerow(['Generated on:', now])
    writer.writerow(['Technician:', technician_name])
    writer.writerow(['Expertise:', expertise])
    writer.writerow(['Location:', location])
    writer.writerow([])
    
    # Write daily appointments section
    writer.writerow(['Daily Appointments (Last 7 Days)'])
    writer.writerow(['Date', 'Number of Appointments'])
    for row in daily_data:
        writer.writerow([row['date'].strftime('%Y-%m-%d'), row['count']])
    writer.writerow([])
    
    # Write issue types section
    writer.writerow(['Issue Types Distribution'])
    writer.writerow(['Issue Type', 'Number of Appointments'])
    for row in issues_data:
        writer.writerow([row['intent'], row['count']])
    
    # Prepare response
    output.seek(0)
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"analytics_report_{now}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@app.route('/export/chart-data')
@login_required
def export_chart_data():
    """Return chart data as JSON for client-side chart export"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get technician data
        expertise = session.get('technician_expertise')
        location = session.get('technician_location')
        
        # Total appointments
        cur.execute("""
            SELECT COUNT(*) as total_appointments
            FROM appointments 
            WHERE location = %s 
            AND intent LIKE %s
        """, (location, f"%{expertise}%"))
        
        total_count_result = cur.fetchone()
        total_count = total_count_result['total_appointments'] if total_count_result else 0
        
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
        
        return jsonify({
            'technician': {
                'name': session.get('technician_name'),
                'expertise': expertise,
                'location': location
            },
            'total_count': total_count,
            'dates': dates,
            'daily_counts': daily_counts,
            'issues': issues,
            'issue_counts': issue_counts,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Error exporting chart data: {e}")
        return jsonify({'error': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/matplotlib-charts/<chart_type>')
@login_required
def matplotlib_charts(chart_type):
    """Generate Matplotlib charts on the server side"""
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from matplotlib.figure import Figure
    import io
    import base64
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'})
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get technician data
        expertise = session.get('technician_expertise')
        location = session.get('technician_location')
        technician_name = session.get('technician_name')
        
        # Create a figure with custom styling
        plt.style.use('dark_background')  # Dark theme to match our application
        fig = Figure(figsize=(10, 6))
        ax = fig.subplots()
        
        # Set the title with technician info
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title_text = f'Analytics for {technician_name} - {expertise} - {location}\nGenerated: {timestamp}'
        
        if chart_type == 'daily':
            # Daily appointment trend
            cur.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM appointments 
                WHERE location = %s 
                AND intent LIKE %s
                AND created_at >= NOW() - INTERVAL '14 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (location, f"%{expertise}%"))
            
            daily_data = cur.fetchall()
            
            if not daily_data:
                ax.text(0.5, 0.5, 'No data available for the selected period', 
                       horizontalalignment='center', verticalalignment='center')
            else:
                # Convert to pandas DataFrame for easier manipulation
                # Extract data from the DictRows into lists
                dates = [row['date'] for row in daily_data]
                counts = [row['count'] for row in daily_data]
                
                # Create DataFrame with explicit column names
                df = pd.DataFrame({'date': dates, 'count': counts})
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
                
                # Plot the data
                ax.plot(df['date'], df['count'], marker='o', linestyle='-', linewidth=2)
                ax.set_title(f'Daily Appointments Trend\n{title_text}')
                ax.set_xlabel('Date')
                ax.set_ylabel('Number of Appointments')
                ax.grid(True, alpha=0.3)
                
                # Format x-axis to show dates properly
                fig.autofmt_xdate()
                
                # Add data labels
                for i, count in enumerate(df['count']):
                    ax.annotate(str(count), (df['date'].iloc[i], count),
                               textcoords="offset points", xytext=(0,5), ha='center')
        
        elif chart_type == 'issues':
            # Issue types distribution
            cur.execute("""
                SELECT intent, COUNT(*) as count
                FROM appointments 
                WHERE location = %s 
                AND intent LIKE %s
                GROUP BY intent
                ORDER BY count DESC
                LIMIT 8
            """, (location, f"%{expertise}%"))
            
            issues_data = cur.fetchall()
            
            if not issues_data:
                ax.text(0.5, 0.5, 'No data available for issue types', 
                       horizontalalignment='center', verticalalignment='center')
            else:
                # Extract data from the DictRows into lists
                intents = [row['intent'] for row in issues_data]
                counts = [row['count'] for row in issues_data]
                
                # Create DataFrame with explicit column names
                df = pd.DataFrame({'intent': intents, 'count': counts})
                
                # Create horizontal bar chart
                bars = ax.barh(df['intent'], df['count'], color=plt.cm.viridis(np.linspace(0, 1, len(df))))
                ax.set_title(f'Issue Types Distribution\n{title_text}')
                ax.set_xlabel('Number of Appointments')
                ax.set_ylabel('Issue Type')
                
                # Add count labels to bars
                for bar in bars:
                    width = bar.get_width()
                    ax.annotate(f'{width}',
                              xy=(width, bar.get_y() + bar.get_height()/2),
                              xytext=(3, 0),  # 3 points horizontal offset
                              textcoords="offset points",
                              ha='left', va='center')
                
                # Adjust layout for better display of long text
                plt.tight_layout()
        
        elif chart_type == 'pie':
            # Pie chart of issue types
            cur.execute("""
                SELECT intent, COUNT(*) as count
                FROM appointments 
                WHERE location = %s 
                AND intent LIKE %s
                GROUP BY intent
                ORDER BY count DESC
            """, (location, f"%{expertise}%"))
            
            issues_data = cur.fetchall()
            
            if not issues_data:
                ax.text(0.5, 0.5, 'No data available for issue types', 
                       horizontalalignment='center', verticalalignment='center')
            else:
                # Extract data from the DictRows into lists
                intents = [row['intent'] for row in issues_data]
                counts = [row['count'] for row in issues_data]
                
                # Create DataFrame with explicit column names
                df = pd.DataFrame({'intent': intents, 'count': counts})
                
                # Generate colors
                colors = plt.cm.tab10(np.linspace(0, 1, len(df)))
                
                # Create pie chart
                wedges, texts, autotexts = ax.pie(
                    df['count'], 
                    labels=df['intent'],
                    autopct='%1.1f%%',
                    colors=colors,
                    shadow=True,
                    startangle=90,
                    textprops={'color': 'white'}
                )
                
                # Ensure pie is drawn as a circle
                ax.axis('equal')
                ax.set_title(f'Issue Types Distribution (Pie Chart)\n{title_text}')
                
                # Make labels more readable
                plt.setp(autotexts, size=9, weight="bold")
                plt.setp(texts, size=8)
                
                # Add legend for better readability with many categories
                if len(df) > 5:
                    ax.legend(df['intent'], loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        
        else:
            return jsonify({'error': 'Invalid chart type'})
        
        # Close database connection
        cur.close()
        conn.close()
        
        # Save plot to a temporary buffer and convert to base64 for embedding
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        
        # For direct download as file
        if request.args.get('download') == 'true':
            buf.seek(0)
            filename = f"matplotlib_{chart_type}_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            return Response(
                buf.getvalue(),
                mimetype='image/png',
                headers={"Content-Disposition": f"attachment;filename={filename}"}
            )
        
        # For displaying in browser or embedding
        data = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"<img src='data:image/png;base64,{data}'/>"
        
    except Exception as e:
        logger.error(f"Error generating Matplotlib chart: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    # Use PORT environment variable if available (commonly used by hosting providers)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
