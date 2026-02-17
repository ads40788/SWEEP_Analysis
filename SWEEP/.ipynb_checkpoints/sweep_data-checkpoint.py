import nfl_data_py as nfl
import pandas as pd
import numpy as np

def download_nfl_data_season(season=2025):
    """Download NFL data using requests library"""
    url = f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv.gz"
    
    print(f"Downloading {season} season...")
    
    # Download with SSL verification disabled
    response = requests.get(url, verify=False)
    
    if response.status_code == 200:
        print(f"✓ Download complete")
        # Load directly from bytes
        pbp = pd.read_csv(BytesIO(response.content), compression='gzip', low_memory=False)
        print(f"✓ Loaded {len(pbp):,} plays")
        return pbp
    else:
        print(f"✗ Error: {response.status_code}")
        return None

def get_game_info(game_plays,print = False):
    
    home_team = game_plays['home_team'].iloc[0]
    away_team = game_plays['away_team'].iloc[0]
    game_date = game_plays['game_date'].iloc[0]
    season_type = game_plays['season_type'].iloc[0] if 'season_type' in game_plays.columns else 'REG'
    
    # Determine actual OT period length by looking at first OT play
    is_playoff = season_type in ['POST', 'WC', 'DIV', 'CON', 'SB']  # Playoff game types


    if game_plays['qtr'].max() >= 5:
        first_ot_play = game_plays[game_plays['qtr'] == 5].iloc[0]
        first_ot_time_remaining = first_ot_play.get('quarter_seconds_remaining', np.nan)
    
        if pd.notna(first_ot_time_remaining):
            # Round to nearest minute to handle ~600 or ~900 values
            detected_length = round(first_ot_time_remaining / 60) * 60
            ot_period_length = detected_length
            #print(f"OT Period Length detected from data: {ot_period_length} seconds ({ot_period_length // 60} min)")
        else:
            # Fallback to playoff detection
            ot_period_length = 900 if is_playoff else 600
            #print(f"OT Period Length (fallback based on season type): {ot_period_length // 60} min")
    else:
        # No OT, but set a default in case needed
        ot_period_length = 900 if is_playoff else 600

    if print:
        print(f"\n{away_team} @ {home_team} - {game_date}")
        print(f"Season Type: {season_type} {'(PLAYOFF)' if is_playoff else '(REGULAR SEASON)'}")
        print(f"Total plays: {len(game_plays)}")
    
    return home_team,away_team,game_date,season_type,is_playoff,ot_period_length


def filter_non_plays(game_plays,exclude_strings = ['imeout','END QUARTER','END GAME']):
    for string in exclude_strings:
        game_plays= game_plays[np.where(game_plays['desc'].str.contains(string),False,True)]
    return(game_plays)

def calculate_time_elapsed(row,ot_length = 10):
    """
    Convert game situation to total seconds elapsed.
    Uses game_seconds_remaining when available to handle both regular season (10 min OT) 
    and playoff (15 min OT) correctly.
    """
    qtr = row['qtr']
    if pd.isna(qtr):
        return np.nan
    
    # Primary method: use game_seconds_remaining if available
    # This should work for both regulation and OT
    game_seconds_remaining = row.get('game_seconds_remaining', np.nan)
    
    if pd.notna(game_seconds_remaining):
        # For regulation (Q1-Q4), game_seconds_remaining counts down from 3600
        # For OT, it continues counting (can be negative or very large depending on data source)
        
        if qtr <= 4:
            # Regulation - straightforward
            if 0 <= game_seconds_remaining <= 3600:
                return 3600 - game_seconds_remaining
        else:
            # Overtime - game_seconds_remaining might be unreliable
            # Fall through to quarter-based calculation
            pass
    
    # Fallback: calculate based on quarter and quarter_seconds_remaining
    qtr_seconds_remaining = row.get('quarter_seconds_remaining', np.nan)
    
    if pd.notna(qtr_seconds_remaining):
        if qtr <= 4:
            # Regulation quarters are always 900 seconds (15 min)
            elapsed_qtrs = qtr - 1
            elapsed = (elapsed_qtrs * 900) + (900 - qtr_seconds_remaining)
        else:
            # For OT, we need to figure out the period length
            # We'll estimate based on the data: if quarter_seconds_remaining > 600, assume 15 min (playoffs)
            # Otherwise assume 10 min (regular season)
            ot_period = qtr - 5  # 0 for Q5, 1 for Q6, etc.
            if ot_length==10:
                elapsed_OT = 600 -qtr_seconds_remaining
                elapsed = 3600 + (ot_period * 600) + elapsed_OT
            else:
                elapsed_OT = 900 -qtr_seconds_remaining
                elapsed = 3600 + (ot_period * 900) + elapsed_OT
            #ot_period_length = 900 if qtr_seconds_remaining > 600 else 600
            
            # Q5 starts at 3600 (end of regulation)
           
            #elapsed = 3600 + (ot_period * ot_period_length) + (ot_period_length - qtr_seconds_remaining)
        
        return elapsed
    
    # Last resort: estimate based on quarter only
    if qtr <= 4:
        return (qtr - 1) * 900  # Start of quarter
    else:
        return 3600 + ((qtr - 5) * 600)  # Assume 10 min OT if we have no better info
    
    return np.nan


def calculate_field_position_home_perspective(row,home_team):
    """
    Convert field position to home team perspective.
    Returns: -50 to +50 (negative = home team's side, positive = away team's side)
    0 = 50 yard line
    """
    if pd.isna(row['yardline_100']):
        return np.nan
    
    posteam = row['posteam']
    yardline_100 = row['yardline_100']  # Distance to opponent's goal
    
    if posteam == home_team:
        # Home team has the ball
        # If 100 yards to opponent's goal = at own goal line = -50 in our scale
        # If 0 yards to opponent's goal = at opponent's goal line = +50 in our scale
        return (100 - yardline_100) - 50
    else:
        # Away team has the ball
        # If 100 yards to opponent's goal = at own goal line = +50 in our scale
        # If 0 yards to opponent's goal = at opponent's goal line = -50 in our scale
        return 50 - (100 - yardline_100)

    
#game_plays['field_position'] = game_plays.apply(calculate_field_position_home_perspective, axis=1)

def enhance_time_and_field(game_plays,ot_length,home_team):
    #Create elapsed time metrics 
    game_plays['time_elapsed'] = game_plays.apply(calculate_time_elapsed, args=([ot_length]),axis=1)
    game_plays['time_elapsed_min'] = game_plays['time_elapsed'] / 60
    game_plays['next_time_elapsed_min'] = game_plays['time_elapsed_min'].shift(-1)

    #Normalize field position
    game_plays['field_position'] = game_plays.apply(calculate_field_position_home_perspective,axis=1,home_team=home_team)

    #get score margin:
    game_plays['score_margin'] = game_plays['total_home_score'] - game_plays['total_away_score']

    return(game_plays)


def categorize_play(row):
    """Categorize play type"""
    play_type = row.get('play_type', '')
    desc = str(row.get('desc', '')).lower()
    penalty = row.get('penalty', 0)
    
    # If there's a penalty, categorize as penalty
    if penalty == 1:
        return 'penalty'
    elif play_type == 'run':
        return 'run'
    elif play_type == 'pass':
        return 'pass'
    elif play_type == 'punt':
        return 'punt'
    elif play_type == 'field_goal':
        return 'field_goal'
    elif 'kickoff' in str(play_type).lower():
        return 'kickoff'
    else:
        return 'other'

def identify_special_outcome(row):
    """Identify special play outcomes"""
    desc = str(row.get('desc', '')).lower()
    
    # Check for touchdowns
    if row.get('touchdown') == 1:
        return 'touchdown'
    
    # Check for field goals
    if row.get('field_goal_result') == 'made':
        return 'field_goal_made'
    elif row.get('field_goal_result') == 'missed':
        return 'field_goal_missed'
    
    # Check for turnovers
    if row.get('interception') == 1:
        return 'interception'
    if row.get('fumble_lost') == 1:
        return 'fumble_lost'
    
    # Check for punts
    if row.get('punt_attempt') == 1:
        return 'punt'
    
    # Turnover on downs
    if row.get('fourth_down_failed') == 1:
        return 'turnover_on_downs'
    
    return None


    
def categorize_game_data(game_plays):

    game_plays['play_category'] = game_plays.apply(categorize_play, axis=1)
    game_plays['special_outcome'] = game_plays.apply(identify_special_outcome, axis=1)

    return game_plays



def label_drives_firsts(game_plays):
    game_plays = game_plays.reset_index()
    game_plays['down']= game_plays['down'].fillna(0)
    
    # Identify drive start plays (first play of each drive)
    drive_plays = game_plays[game_plays['down']>0]
    
    drive_plays['is_drive_start'] = drive_plays['drive'] != drive_plays['drive'].shift(1)
    drive_plays_ = drive_plays[['is_drive_start','index']]

    game_plays=game_plays.merge(drive_plays_,on='index',how='left')
    #game_plays_['is_drive_start'].fillna(False)
    
    # Identify first down conversions - check multiple possible column names
    # We want to mark the FIRST down play, not the play that earned it
    if 'first_down' in game_plays.columns:
        # Mark plays where the PREVIOUS play converted
        first_down_converted = (game_plays['first_down'].shift(1) == 1) & (game_plays['play_type'].isin(['pass', 'run']))
        # Or if this is a 1st down play (down == 1) after a conversion
        game_plays['is_first_down'] = (game_plays['down'] == 1) & first_down_converted
    elif 'first_down_pass' in game_plays.columns or 'first_down_rush' in game_plays.columns:
        first_down_converted = (
            (game_plays.get('first_down_pass', 0).shift(1) == 1) | 
            (game_plays.get('first_down_rush', 0).shift(1) == 1)
        )
        game_plays_['is_first_down'] = (game_plays_['down'] == 1) & first_down_converted
    else:
        # Check if this is a 1st down play following a conversion
        game_plays['is_first_down'] = (
            (game_plays['down'] == 1) & 
            (game_plays['down'].shift(1).notna()) & 
            (game_plays['down'].shift(1) != 1) &
            (game_plays['drive'] == game_plays['drive'].shift(1))  # Same drive
        )

    return game_plays


def calculate_excitement(game_plays,home_team):
    
    # Calculate play excitement (change in win probability percentage)
    # excitement = |WP_after - WP_before| * 100 (as percentage points)
    # Use vegas_wp or wp column
    wp_col = 'vegas_wp' if 'vegas_wp' in game_plays.columns else 'wp'
    
    if wp_col in game_plays.columns:
        # Check if WP is in 0-1 or 0-100 scale
        max_wp = game_plays[wp_col].max()
        wp_scale = 1 if max_wp <= 1 else 100
        
        # Forward fill WP values to handle timeouts, penalties, END QUARTER, etc.
        # These administrative plays shouldn't have their own WP, they inherit from previous play
        # Replace 0s and NaNs, then forward fill
        game_plays[wp_col + '_filled'] = game_plays[wp_col].replace(0, np.nan).ffill()#.bfill()  # bfill for first play
        
        # ALSO forward-fill posteam for administrative plays (timeouts, END QUARTER, etc.)
        # This ensures we use the correct team perspective when converting WP
        game_plays['posteam_filled'] = game_plays['posteam'].ffill().bfill()  # bfill for first play
        
        # Convert WP to home team perspective for EVERY row
        # If home team has possession, WP is already from home perspective
        # If away team has possession, WP is from away perspective, so flip it
        # NOTE: The WP in the data represents win probability AT THE START of the play
        
    
        game_plays['home_wp'] = game_plays.apply(
            lambda row: (row[wp_col + '_filled'] if row['posteam_filled'] == home_team 
                         else 1 - row[wp_col + '_filled']) if pd.notna(row[wp_col + '_filled']) 
                         else np.nan,
            axis=1
        )
        
        # Calculate excitement as absolute change in home WP from this play to next
        # Shift home_wp backward by 1 to get next play's home_wp
        game_plays['home_wp_next'] = game_plays['home_wp'].shift(-1)
        game_plays['posteam_filled_next'] = game_plays['posteam_filled'].shift(-1)
    
        '''
        game_plays['home_wp_next'] = game_plays.apply(
            lambda row: row['home_wp_next_'] if row['posteam_filled']==row['posteam_filled_next']
                else 1 - row['home_wp_next_'],
            axis=1
        )
        '''
    
        
        # Calculate excitement as absolute change in home WP from this play to next
        # The WP value represents the win probability AT THE START of a play
        # So to measure the excitement of a play, we need: |WP_after_play - WP_before_play|
        # WP_after_play = the WP at the start of the NEXT play
        # WP_before_play = the WP at the start of THIS play
        
        # Get next play's WP (represents state AFTER current play completes)
        game_plays['home_wp_next'] = game_plays['home_wp'].shift(-1)
        
        # Excitement = |WP_after - WP_before| = impact of THIS play
        game_plays['play_excitement'] = abs(game_plays['home_wp_next'] - game_plays['home_wp']) * 100
            
        # Special handling for last play of half/game where there is no "next play"
        # For these plays, excitement should be 0 since we can't measure the change
        game_plays['play_excitement'] = game_plays['play_excitement'].fillna(0)
        
        # Also set excitement to 0 for plays at end of quarters where next play is a kickoff
        # (the WP reset makes the "excitement" artificially high)
        next_play_is_kickoff = game_plays['play_type'].shift(-1) == 'kickoff'
        game_plays.loc[next_play_is_kickoff, 'play_excitement'] = 0
        
        # Add diagnostic: check if possession changed
        game_plays['possession_changed'] = game_plays['posteam'] != game_plays['posteam'].shift(1)
        
        # Only calculate excitement for actual plays
        # Include: pass, run, punt, field_goal (without penalties)
        # AND: all penalties (including no_play penalties) since they affect WP
        game_plays['is_real_play'] = (
            game_plays['play_type'].isin(['pass', 'run', 'punt', 'field_goal']) |
            (game_plays['penalty'] == 1)  # Include ALL penalties
        )
        
        # Set excitement to 0 for non-real plays (timeouts, 2-min warnings, etc.)
        game_plays.loc[~game_plays['is_real_play'], 'play_excitement'] = 0

        game_plays['play_unpredictability'] = abs(0.5 - game_plays['home_wp'])
        
        # Game-level metrics (only real plays)
        #real_plays = game_plays[game_plays['is_real_play']]
        #avg_excitement = real_plays['play_excitement'].mean()
        #avg_unpredictability = real_plays['play_unpredictability'].mean()
    else:
        game_plays['play_excitement'] = 0
        game_plays['play_unpredictability'] = 0
        game_plays['is_real_play'] = True
        #avg_excitement = 0
        #avg_unpredictability = 0
        
    return game_plays

###Get Hover Text for Visualization
def create_hover_text(row):
    """Create detailed hover text for each play"""
    qtr = row.get('qtr', '?')
    time = row.get('time', '?')
    down = row.get('down', '')
    ydstogo = row.get('ydstogo', '')
    yardline = row.get('yrdln', '?')
    desc = row.get('desc', 'No description')
    posteam = row.get('posteam', '?')
        
    # Score info - use correct column names
    home_score = row.get('total_home_score', 0)
    away_score = row.get('total_away_score', 0)
    home_team= row.get('home_team', 0)
    away_team = row.get('away_team', 0)
    
    # Yards gained
    yards_gained = row.get('yards_gained_display', 0)
        
    # Excitement metrics
    excitement = row.get('play_excitement', 0)
        
    # Build hover text
    hover = f"<b>Q{qtr} {time}</b><br>"
        
    if pd.notna(down) and down > 0:
        hover += f"{int(down)} & {int(ydstogo)} at {yardline}<br>"
        
    hover += f"<b>{posteam}</b> possession<br>"
    hover += f"Score: {away_team} {int(away_score)} - {home_team} {int(home_score)}<br>"
    hover += f"Yards gained: {yards_gained:.0f}<br>"
        
    if excitement > 0:
        hover += f"Play excitement: {excitement:.1f}%<br>"
    if len(desc)<150:
        hover += f"<br>{desc[:150]}"  # Truncate long descriptions
    else:
        hover+= desc[:150]+'<br>'+desc[150:300]
    return hover
    

def create_final_display_data(game_plays):
    ### Calcualte total yards gained

    game_plays['yards_gained_display'] = game_plays.apply(
    lambda row: row.get('penalty_yards', 0) if row['play_category'] == 'penalty' and pd.notna(row.get('penalty_yards'))
    else row.get('yards_gained', 0),
    axis=1)

    ### Calcualte Hover Text using Helper Function
    game_plays['hover_text'] = game_plays.apply(create_hover_text, axis=1)
    
    return game_plays 

    