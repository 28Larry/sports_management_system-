# sports_management_system-
A system that enables the management ,allocation and fixtures of games and various teams
# app.py - Main Flask Application

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
import pyodbc
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)
bcrypt = Bcrypt(app)

# Database connection
def get_db_connection():
    conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
                          r'DBQ=./sports_management_system.accdb;')
    return conn

# User roles
ROLES = {
    'admin': 'Administrator',
    'coach': 'Coach',
    'player': 'Player',
    'medical': 'Medical Staff',
    'fan': 'Fan'
}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role required decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']
        
        # Validate input
        if not username or not password or not email or not role:
            flash('All fields are required!', 'danger')
            return render_template('register.html', roles=ROLES)
        
        # Check if username already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM USERS WHERE Username = ?', (username,))
        if cursor.fetchone():
            flash('Username already exists!', 'danger')
            conn.close()
            return render_template('register.html', roles=ROLES)
        
        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Insert new user
        try:
            cursor.execute(
                'INSERT INTO USERS (Username, Password, Email, Phone, RegistrationDate, Role) VALUES (?, ?, ?, ?, ?, ?)',
                (username, hashed_password, email, phone, datetime.now(), role)
            )
            conn.commit()
            
            # Get the new user ID
            cursor.execute('SELECT @@IDENTITY')
            user_id = cursor.fetchone()[0]
            
            # If role is 'fan', create a fan record
            if role == 'fan':
                cursor.execute(
                    'INSERT INTO FANS (UserID, MembershipType, JoinDate, LoyaltyPoints) VALUES (?, ?, ?, ?)',
                    (user_id, 'Basic', datetime.now(), 0)
                )
            
            # If role is 'player', redirect to player profile creation
            if role == 'player':
                session['user_id'] = user_id
                session['role'] = role
                session['username'] = username
                conn.commit()
                conn.close()
                return redirect(url_for('create_player_profile'))
            
            # If role is 'medical', create medical staff record
            if role == 'medical':
                cursor.execute(
                    'INSERT INTO MEDICAL_STAFF (UserID, Specialization, Qualification) VALUES (?, ?, ?)',
                    (user_id, 'General', 'Not specified')
                )
            
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash(f'Error during registration: {str(e)}', 'danger')
            conn.close()
            return render_template('register.html', roles=ROLES)
    
    return render_template('register.html', roles=ROLES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT UserID, Username, Password, Role FROM USERS WHERE Username = ?', (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            
            flash(f'Welcome back, {username}!', 'success')
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
            conn.close()
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'coach':
        return redirect(url_for('coach_dashboard'))
    elif role == 'player':
        return redirect(url_for('player_dashboard'))
    elif role == 'medical':
        return redirect(url_for('medical_dashboard'))
    elif role == 'fan':
        return redirect(url_for('fan_dashboard'))
    else:
        flash('Unknown role!', 'danger')
        return redirect(url_for('logout'))

# Specific dashboards for different roles
@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/coach/dashboard')
@login_required
@role_required(['coach'])
def coach_dashboard():
    return render_template('coach_dashboard.html')

@app.route('/player/dashboard')
@login_required
@role_required(['player'])
def player_dashboard():
    # Get player details
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM PLAYERS WHERE UserID = ?', (session['user_id'],))
    player = cursor.fetchone()
    
    if not player:
        conn.close()
        flash('Player profile not found. Please create your profile.', 'warning')
        return redirect(url_for('create_player_profile'))
    
    # Get team details
    cursor.execute('SELECT * FROM TEAMS WHERE TeamID = ?', (player[5],))
    team = cursor.fetchone()
    
    # Get upcoming matches
    cursor.execute('''
        SELECT M.*, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam, V.VenueName 
        FROM MATCHES M
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        JOIN VENUES V ON M.VenueID = V.VenueID
        WHERE (M.HomeTeamID = ? OR M.AwayTeamID = ?) AND M.MatchDateTime > NOW()
        ORDER BY M.MatchDateTime
    ''', (player[5], player[5]))
    upcoming_matches = cursor.fetchall()
    
    # Get physio records
    cursor.execute('''
        SELECT PR.*, MS.Specialization, U.Username as StaffName
        FROM PHYSIO_RECORDS PR
        JOIN MEDICAL_STAFF MS ON PR.StaffID = MS.StaffID
        JOIN USERS U ON MS.UserID = U.UserID
        WHERE PR.PlayerID = ?
        ORDER BY PR.RecordDate DESC
    ''', (player[0],))
    physio_records = cursor.fetchall()
    
    # Get player stats
    cursor.execute('''
        SELECT PS.*, M.MatchDateTime, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam
        FROM PLAYER_STATS PS
        JOIN MATCHES M ON PS.MatchID = M.MatchID
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        WHERE PS.PlayerID = ?
        ORDER BY M.MatchDateTime DESC
    ''', (player[0],))
    stats = cursor.fetchall()
    
    conn.close()
    
    return render_template('player_dashboard.html', 
                           player=player, 
                           team=team, 
                           upcoming_matches=upcoming_matches, 
                           physio_records=physio_records, 
                           stats=stats)

@app.route('/medical/dashboard')
@login_required
@role_required(['medical'])
def medical_dashboard():
    # Get medical staff details
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM MEDICAL_STAFF WHERE UserID = ?', (session['user_id'],))
    staff = cursor.fetchone()
    
    if not staff:
        conn.close()
        flash('Medical staff profile not found.', 'warning')
        return redirect(url_for('index'))
    
    # Get assigned players with injuries
    cursor.execute('''
        SELECT PR.*, P.FullName, P.Position, T.TeamName
        FROM PHYSIO_RECORDS PR
        JOIN PLAYERS P ON PR.PlayerID = P.PlayerID
        JOIN TEAMS T ON P.TeamID = T.TeamID
        WHERE PR.StaffID = ? AND PR.Status <> 'Recovered'
        ORDER BY PR.ExpectedRecovery
    ''', (staff[0],))
    active_cases = cursor.fetchall()
    
    # Get recent records
    cursor.execute('''
        SELECT PR.*, P.FullName, P.Position, T.TeamName
        FROM PHYSIO_RECORDS PR
        JOIN PLAYERS P ON PR.PlayerID = P.PlayerID
        JOIN TEAMS T ON P.TeamID = T.TeamID
        WHERE PR.StaffID = ?
        ORDER BY PR.RecordDate DESC
        LIMIT 10
    ''', (staff[0],))
    recent_records = cursor.fetchall()
    
    conn.close()
    
    return render_template('medical_dashboard.html',
                          staff=staff,
                          active_cases=active_cases,
                          recent_records=recent_records)

@app.route('/fan/dashboard')
@login_required
@role_required(['fan'])
def fan_dashboard():
    # Get fan details
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM FANS WHERE UserID = ?', (session['user_id'],))
    fan = cursor.fetchone()
    
    if not fan:
        conn.close()
        flash('Fan profile not found.', 'warning')
        return redirect(url_for('index'))
    
    # Get upcoming matches
    cursor.execute('''
        SELECT M.*, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam, V.VenueName 
        FROM MATCHES M
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        JOIN VENUES V ON M.VenueID = V.VenueID
        WHERE M.MatchDateTime > NOW()
        ORDER BY M.MatchDateTime
        LIMIT 5
    ''')
    upcoming_matches = cursor.fetchall()
    
    # Get fan's engagement history
    cursor.execute('''
        SELECT FE.*, M.MatchDateTime, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam
        FROM FAN_ENGAGEMENT FE
        JOIN MATCHES M ON FE.MatchID = M.MatchID
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        WHERE FE.FanID = ?
        ORDER BY FE.EngagementDate DESC
    ''', (fan[0],))
    engagement_history = cursor.fetchall()
    
    conn.close()
    
    return render_template('fan_dashboard.html',
                          fan=fan,
                          upcoming_matches=upcoming_matches,
                          engagement_history=engagement_history)

@app.route('/create_player_profile', methods=['GET', 'POST'])
@login_required
@role_required(['player'])
def create_player_profile():
    if request.method == 'POST':
        full_name = request.form['full_name']
        date_of_birth = request.form['date_of_birth']
        position = request.form['position']
        team_id = request.form['team_id']
        
        # Validate
        if not full_name or not date_of_birth or not position or not team_id:
            flash('All fields are required!', 'danger')
            
            # Get teams for dropdown
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT TeamID, TeamName FROM TEAMS')
            teams = cursor.fetchall()
            conn.close()
            
            return render_template('create_player_profile.html', teams=teams)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO PLAYERS (UserID, FullName, DateOfBirth, Position, TeamID, Status) VALUES (?, ?, ?, ?, ?, ?)',
                (session['user_id'], full_name, date_of_birth, position, team_id, 'Active')
            )
            conn.commit()
            flash('Player profile created successfully!', 'success')
            conn.close()
            return redirect(url_for('player_dashboard'))
        except Exception as e:
            conn.rollback()
            flash(f'Error creating player profile: {str(e)}', 'danger')
            
            # Get teams for dropdown
            cursor.execute('SELECT TeamID, TeamName FROM TEAMS')
            teams = cursor.fetchall()
            conn.close()
            
            return render_template('create_player_profile.html', teams=teams)
    
    # GET request - show form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT TeamID, TeamName FROM TEAMS')
    teams = cursor.fetchall()
    conn.close()
    
    return render_template('create_player_profile.html', teams=teams)

if __name__ == '__main__':
    app.run(debug=True)
