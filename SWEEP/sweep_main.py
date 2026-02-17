from .sweep_viz import *
from .sweep_data import *

def get_visualization(season_data,the_week=None,the_team=None):
    season_data_ = season_data.copy()
    if the_week == None:
        pass
    else:
        season_data_ = season_data_[season_data_['week']==the_week]
    if the_team == None:
        pass
    else:
        season_data_ = season_data_[(season_data_['home_team']==the_team)|(season_data_['away_team']==the_team)]
    if len(season_data_[['game_id','week','home_team','away_team','week']].drop_duplicates()['game_id'])==0:
        print("This game does not exist!")
        return None
    elif len(season_data_[['game_id','week','home_team','away_team','week']].drop_duplicates()['game_id'])>1:
        print("This returns too many games, specify a team AND a week!") 
        return None
    else:
        game_data = season_data_
        print("Preparing sweep analysis data for visualization.")
        game_plays,home_team,away_team,game_date,season_type,is_playoff,ot_len = make_sweep_data(game_data)
        print("Generating visualization.")
        sweep_viz = run_sweep_viz(game_plays,home_team,away_team)
        sweep_viz.show()
    game_id = game_plays['game_id'].iloc[0]
    return sweep_viz,game_id

def run_sweep_viz(game_plays,home_team,away_team,home_color='#1f77b4',away_color='#ff7f0e'):
    game_fig = create_viz(game_plays)

    ### Add probability/margin plots
    game_fig = viz_probability(game_plays,home_team,game_fig)
    
    ### Core drive visualizations by team
    game_fig = add_team_traces(game_fig,game_plays, home_team,home_color,True)
    game_fig = add_team_traces(game_fig,game_plays, away_team,away_color,False)
    
    ### Add Events for Each Team: Scores, Turnovers, First Downs, Drive Starts, etc.
    game_fig = add_team_events(game_fig,game_plays, home_team, home_color,True)
    game_fig = add_team_events(game_fig,game_plays, away_team, away_color,False)
    
    ### Add Extra Point Data
    game_fig = add_score_details(game_fig,game_plays, home_team, home_color,True)
    game_fig = add_score_details(game_fig,game_plays, away_team, away_color,False)
    
    ### Add possession change events:
    game_fig = add_kicks(game_fig,game_plays)
    game_fig = add_turnovers(game_fig,game_plays)
    
    ### Add Scoring Labels and Descriptive Tables
    game_fig = add_score_labels(game_fig,game_plays,home_color,away_color)
    game_fig = add_game_table(game_fig,game_plays)
    game_fig = add_exciting_table(game_fig,game_plays)
    
    
    ### Clean main layout and format.
    game_fig = update_axes(game_fig,game_plays)
    game_fig = format_main_layout(game_fig,game_plays,home_color,away_color)

    return game_fig


def make_sweep_data(game_plays): 
    ### 1. Get Game Overall Stats
    home_team,away_team,game_date,season_type,is_playoff,ot_len = get_game_info(game_plays)
    
    ### 2. Eliminate Period End/Timeout Events
    game_plays = filter_non_plays(game_plays)
    
    ### 3. Add columns for time and yard and score differntial data
    game_plays = enhance_time_and_field(game_plays,ot_len,home_team)
    
    ### 4. Label and categorize different game events (Adds columns 'play_category','special_outcome')
    game_plays = categorize_game_data(game_plays)
    
    ### 5. labels 1st Dowsns and Drive Starts. (Adds columns 'is_drive_start','is_first_down')
    game_plays = label_drives_firsts(game_plays)
    
    ### 6. Calcualte excitement via change in win probability. (Adds columns 'play_excitement' and support columns )
    game_plays = calculate_excitement(game_plays,home_team)
    
    ### 7. Make Final Additions to Data Before Visualizations. (Adds columns 'yards_gained_display' and 'hover_text' )
    game_plays = create_final_display_data(game_plays)
    
    return game_plays,home_team,away_team,game_date,season_type,is_playoff,ot_len