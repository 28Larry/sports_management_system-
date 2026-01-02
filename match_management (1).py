# match_management.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import pyodbc
from datetime import datetime

match_bp = Blueprint('match', __name__)

# Database connection
def get_db_connection():
    conn = pyodbc.connect(r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
                          r'DBQ=./sports_management_system.accdb;')
    return conn

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
@match_bp.route('/matches')
@login_required
def matches():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all matches with team names and venue
    cursor.execute('''
        SELECT M.*, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam, V.VenueName 
        FROM MATCHES M
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        JOIN VENUES V ON M.VenueID = V.VenueID
        ORDER BY M.MatchDateTime DESC
    ''')
    matches = cursor.fetchall()
    conn.close()
    
    return render_template('matches.html', matches=matches)

@match_bp.route('/matches/upcoming')
@login_required
def upcoming_matches():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get upcoming matches
    cursor.execute('''
        SELECT M.*, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam, V.VenueName 
        FROM MATCHES M
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        JOIN VENUES V ON M.VenueID = V.VenueID
        WHERE M.MatchDateTime > NOW()
        ORDER BY M.MatchDateTime
    ''')
    matches = cursor.fetchall()
    conn.close()
    
    return render_template('upcoming_matches.html', matches=matches)

@match_bp.route('/matches/past')
@login_required
def past_matches():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get past matches
    cursor.execute('''
        SELECT M.*, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam, V.VenueName 
        FROM MATCHES M
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        JOIN VENUES V ON M.VenueID = V.VenueID
        WHERE M.MatchDateTime <= NOW()
        ORDER BY M.MatchDateTime DESC
    ''')
    matches = cursor.fetchall()
    conn.close()
    
    return render_template('past_matches.html', matches=matches)

@match_bp.route('/matches/<int:match_id>')
@login_required
def match_details(match_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get match details
    cursor.execute('''
        SELECT M.*, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam, V.VenueName, V.Location 
        FROM MATCHES M
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        JOIN VENUES V ON M.VenueID = V.VenueID
        WHERE M.MatchID = ?
    ''', (match_id,))
    match = cursor.fetchone()
    
    if not match:
        conn.close()
        flash('Match not found!', 'danger')
        return redirect(url_for('match.matches'))
    
    # Get player stats for this match
    cursor.execute('''
        SELECT PS.*, P.FullName, P.Position, T.TeamName
        FROM PLAYER_STATS PS
        JOIN PLAYERS P ON PS.PlayerID = P.PlayerID
        JOIN TEAMS T ON P.TeamID = T.TeamID
        WHERE PS.MatchID = ?
        ORDER BY PS.PerformanceRating DESC
    ''', (match_id,))
    stats = cursor.fetchall()
    
    # Get fan engagements for this match
    cursor.execute('''
        SELECT FE.*, U.Username
        FROM FAN_ENGAGEMENT FE
        JOIN FANS F ON FE.FanID = F.FanID
        JOIN USERS U ON F.UserID = U.UserID
        WHERE FE.MatchID = ?
        ORDER BY FE.EngagementDate DESC
    ''', (match_id,))
    engagements = cursor.fetchall()
    
    conn.close()
    
    return render_template('match_details.html', 
                          match=match, 
                          stats=stats, 
                          engagements=engagements)

@match_bp.route('/matches/create', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'coach'])
def create_match():
    if request.method == 'POST':
        home_team_id = request.form['home_team_id']
        away_team_id = request.form['away_team_id']
        match_date = request.form['match_date']
        match_time = request.form['match_time']
        venue_id = request.form['venue_id']
        
        # Validate
        if not home_team_id or not away_team_id or not match_date or not match_time or not venue_id:
            flash('All fields are required!', 'danger')
            
            # Get teams and venues for dropdowns
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT TeamID, TeamName FROM TEAMS')
            teams = cursor.fetchall()
            cursor.execute('SELECT VenueID, VenueName FROM VENUES')
            venues = cursor.fetchall()
            conn.close()
            
            return render_template('create_match.html', teams=teams, venues=venues)
        
        if home_team_id == away_team_id:
            flash('Home team and away team cannot be the same!', 'danger')
            
            # Get teams and venues for dropdowns
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT TeamID, TeamName FROM TEAMS')
            teams = cursor.fetchall()
            cursor.execute('SELECT VenueID, VenueName FROM VENUES')
            venues = cursor.fetchall()
            conn.close()
            
            return render_template('create_match.html', teams=teams, venues=venues)
        
        # Combine date and time
        match_datetime = f"{match_date} {match_time}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''INSERT INTO MATCHES 
                   (HomeTeamID, AwayTeamID, MatchDateTime, VenueID, Status) 
                   VALUES (?, ?, ?, ?, ?)''',
                (home_team_id, away_team_id, match_datetime, venue_id, 'Scheduled')
            )
            conn.commit()
            flash('Match scheduled successfully!', 'success')
            conn.close()
            return redirect(url_for('match.matches'))
        except Exception as e:
            conn.rollback()
            flash(f'Error scheduling match: {str(e)}', 'danger')
            
            # Get teams and venues for dropdowns
            cursor.execute('SELECT TeamID, TeamName FROM TEAMS')
            teams = cursor.fetchall()
            cursor.execute('SELECT VenueID, VenueName FROM VENUES')
            venues = cursor.fetchall()
            conn.close()
            
            return render_template('create_match.html', teams=teams, venues=venues)
    
    # GET request - show form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT TeamID, TeamName FROM TEAMS')
    teams = cursor.fetchall()
    cursor.execute('SELECT VenueID, VenueName FROM VENUES')
    venues = cursor.fetchall()
    conn.close()
    
    return render_template('create_match.html', teams=teams, venues=venues)

@match_bp.route('/matches/update/<int:match_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'coach'])
def update_match(match_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        home_score = request.form['home_score']
        away_score = request.form['away_score']
        status = request.form['status']
        
        try:
            cursor.execute(
                '''UPDATE MATCHES 
                   SET HomeScore = ?, AwayScore = ?, Status = ? 
                   WHERE MatchID = ?''',
                (home_score, away_score, status, match_id)
            )
            conn.commit()
            flash('Match updated successfully!', 'success')
            conn.close()
            return redirect(url_for('match.match_details', match_id=match_id))
        except Exception as e:
            conn.rollback()
            flash(f'Error updating match: {str(e)}', 'danger')
            conn.close()
            return redirect(url_for('match.match_details', match_id=match_id))
    
    # GET request - show form
    cursor.execute('''
        SELECT M.*, HT.TeamName as HomeTeam, AT.TeamName as AwayTeam, V.VenueName 
        FROM MATCHES M
        JOIN TEAMS HT ON M.HomeTeamID = HT.TeamID
        JOIN TEAMS AT ON M.AwayTeamID = AT.TeamID
        JOIN VENUES V ON M.VenueID = V.VenueID
        WHERE M.MatchID = ?
    ''', (match_id,))
    match = cursor.fetchone()
    
    if not match:
        conn.close()
        flash('Match not found!', 'danger')
        return redirect(url_for('match.matches'))
    
    conn.close()
    return render_template('update_match.html', match=match)