import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_viz(game_plays):
    
    fig = go.Figure()

    return fig


def viz_probability(game_plays,home_team,fig):
    """Add probability and margin traces to figure"""
    # Define colors for each team


    # Win Probability (if available)
    wp_column = 'vegas_wp' if 'vegas_wp' in game_plays.columns else 'wp'
    
    if wp_column in game_plays.columns:
        all_plays_for_wp = game_plays[['time_elapsed_min', wp_column, 'posteam']].dropna().copy()
        all_plays_for_wp = all_plays_for_wp.sort_values('time_elapsed_min').reset_index(drop=True)
        
        # Convert WP to always be from home team perspective
        # If away team has possession, wp is their win prob, so home wp = 1 - wp
        all_plays_for_wp['home_wp'] = all_plays_for_wp.apply(
            lambda row: row[wp_column] if row['posteam'] == home_team else 1 - row[wp_column],
            axis=1
        )
        
        # Convert WP from 0-1 to -50 to +50 scale (matching field position)
        # 0% home WP (away wins) = -50, 50% = 0, 100% (home wins) = +50
        all_plays_for_wp['wp_scaled'] = (all_plays_for_wp['home_wp'] - 0.5) * 100
        
        fig.add_trace(
            go.Scatter(
                x=all_plays_for_wp['wp_scaled'],
                y=all_plays_for_wp['time_elapsed_min'],
                fill='tozerox',  # Fill to x=0 (50/50 game)
                fillcolor='rgba(100, 150, 200, 0.08)',  # Light blue, very transparent
                line=dict(color='rgba(80, 120, 180, 0.3)', width=2),
                mode='lines',
                name=f'{home_team} Win Prob (Vegas)',
                customdata=all_plays_for_wp['home_wp'] * 100,  # Store actual percentage
                hovertemplate='<b>Win Prob (Vegas)</b>: %{customdata:.1f}%<br><b>Time</b>: %{y:.1f} min<extra></extra>',
                showlegend=True,
                legendrank=500  # Background traces at bottom
            )
        )
    
    # Add model-based WP trace (if wp column exists separately from vegas_wp)
    if 'wp' in game_plays.columns and wp_column == 'vegas_wp':
        all_plays_for_model_wp = game_plays[['time_elapsed_min', 'wp', 'posteam']].dropna().copy()
        all_plays_for_model_wp = all_plays_for_model_wp.sort_values('time_elapsed_min').reset_index(drop=True)
        
        # Convert model WP to home team perspective (same logic)
        all_plays_for_model_wp['home_wp'] = all_plays_for_model_wp.apply(
            lambda row: row['wp'] if row['posteam'] == home_team else 1 - row['wp'],
            axis=1
        )
        
        # Scale to field position range
        all_plays_for_model_wp['wp_scaled'] = (all_plays_for_model_wp['home_wp'] - 0.5) * 100
        
        fig.add_trace(
            go.Scatter(
                x=all_plays_for_model_wp['wp_scaled'],
                y=all_plays_for_model_wp['time_elapsed_min'],
                fill='tozerox',  # Fill to x=0 (50/50 game)
                fillcolor='rgba(200, 100, 150, 0.05)',  # Light purple/pink, very transparent
                line=dict(color='rgba(180, 80, 120, 0.3)', width=2, dash='dot'),
                mode='lines',
                name=f'{home_team} Win Prob (Model)',
                customdata=all_plays_for_model_wp['home_wp'] * 100,
                hovertemplate='<b>Win Prob (Model)</b>: %{customdata:.1f}%<br><b>Time</b>: %{y:.1f} min<extra></extra>',
                visible='legendonly',  # Hidden by default, can toggle on
                showlegend=True,
                legendrank=501  # Background traces at bottom
            )
        )
    
    # Score Margin (always show this)
    all_plays_for_score = game_plays[['time_elapsed_min', 'score_margin']].dropna().copy()
    all_plays_for_score = all_plays_for_score.sort_values('time_elapsed_min').reset_index(drop=True)
    
    fig.add_trace(
        go.Scatter(
            x=all_plays_for_score['score_margin'],
            y=all_plays_for_score['time_elapsed_min'],
            fill='tozerox',
            fillcolor='rgba(200, 200, 200, 0.12)',  # Light gray
            line=dict(color='rgba(100, 100, 100, 0.3)', width=1.5),
            mode='lines',
            name='Score Margin (Home - Away)',
            hovertemplate='<b>Margin</b>: %{x}<br><b>Time</b>: %{y:.1f} min<extra></extra>',
            showlegend=True,
            legendrank=502  # Background traces at bottom
        )
    )
    return fig





#game_plays['next_time_elapsed_min'] = game_plays['time_elapsed_min'].shift(-1)

# Function to add traces for a team with proper run/pass/penalty line differentiation
def add_team_traces(fig,game_plays, team_name, color,home=True):
    """Add traces for a team, connecting ALL plays within drives including penalties"""
    valid_plays = game_plays[game_plays['field_position'].notna() & 
                          game_plays['play_category'].isin(['run', 'pass', 'punt', 'penalty'])].copy()
    team_plays =  valid_plays[(valid_plays['posteam'] == team_name)&(valid_plays['down']>0)]
    if len(team_plays) == 0:
        return
    
    # Get unique drives for this team
    drives = team_plays.groupby('drive')
    
    for drive_num, drive_data in drives:
        # Sort by play order within drive
        drive_data = drive_data.sort_values('play_id').reset_index(drop=True)
        
        # Connect consecutive plays (including penalties) with lines
        
        for i in range(len(drive_data)):
            #print(drive_data)
            current_play = drive_data.iloc[i]
            play_type = current_play['play_category']
            
            # Determine line style and legend group based on play type
            if play_type == 'run':
                line_dash = 'solid'
                marker_symbol = 'circle'
                marker_line_color = 'white'
                legend_group = f"{team_name}_run"
            elif play_type == 'pass':
                line_dash = 'dot'
                marker_symbol = 'circle-open'
                marker_line_color = color
                legend_group = f"{team_name}_pass"
            elif play_type == 'penalty':
                line_dash = 'dot'  # Red dots for penalties
                marker_symbol = 'triangle-up'
                marker_line_color = color
                legend_group = f"{team_name}_penalty"
            else:  # punt or other
                line_dash = 'dashdot'
                marker_symbol = 'circle-open'
                marker_line_color = 'gray'
                legend_group = f"{team_name}_other"
            
            # Connect to previous play in drive (ANY play type)
            if i >= 0 and len(drive_data)>1:
                prev_play = drive_data.iloc[i-1]
                
                try:
                    next_play = drive_data.iloc[i+1]
                    next_time = current_play['next_time_elapsed_min'] 

                    #next_time = next_play['time_elapsed_min']     
                except:
                    next_time = current_play['next_time_elapsed_min'] 

                # Penalty lines are ALWAYS bright red, regardless of team
                line_color = 'rgb(255, 50, 50)' if play_type == 'penalty' else color

                if current_play['home_team'] == current_play['posteam']:
                    field_pos_shift = current_play['yards_gained_display']
                else:
                    field_pos_shift = -1*current_play['yards_gained_display']

                if play_type =='penalty':
                    field_pos_shift = next_play['field_position']-current_play['field_position']
                
                # Add a line segment from previous play to current play
                fig.add_trace(
                    go.Scatter(
                        x=[current_play['field_position'], current_play['field_position']+field_pos_shift],
                        y=[current_play['time_elapsed_min'], next_play['time_elapsed_min']],
                        mode='lines',
                        line=dict(color=line_color, width=2, dash=line_dash),
                        showlegend=False,
                        legendgroup=legend_group,  # LINK TO LEGEND GROUP
                        hoverinfo='skip'
                    )
                )
            
            # Add marker for current play (skip punts since they have their own markers)
            if play_type not in ['punt']:
                # Penalties get yellow triangles, others get standard markers
                marker_size = 8 if play_type == 'penalty' else 7
                marker_color = 'yellow' if play_type == 'penalty' else color
                
                fig.add_trace(
                    go.Scatter(
                        x=[current_play['field_position']],
                        y=[current_play['time_elapsed_min']],
                        mode='markers',
                        name=f'{team_name} - {play_type.capitalize()}',
                        marker=dict(
                            size=marker_size,
                            color=marker_color,
                            symbol=marker_symbol,
                            line=dict(width=1.5, color=marker_line_color)
                        ),
                        hovertext=[current_play['hover_text']],
                        hovertemplate='%{hovertext}<extra></extra>',
                        showlegend=False,
                        legendgroup=legend_group
                    )
                )

    
    # Add explicit legend entries for run/pass/penalty by team
    team = team_name
    #for team in [home_team, away_team]:
    rank_offset = 0 if home else 100  # Home team entries first
        
        # Run legend entry
    fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode='lines+markers',
                name=f'{team} - Run',
                line=dict(color=color, width=2, dash='solid'),
                marker=dict(size=7, color=color, symbol='circle', line=dict(width=1.5, color='white')),
                showlegend=True,
                legendgroup=f"{team}_run",
                legendrank=1 + rank_offset
            )
        )
        
        # Pass legend entry
    fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode='lines+markers',
                name=f'{team} - Pass',
                line=dict(color=color, width=2, dash='dot'),
                marker=dict(size=7, color=color, symbol='circle-open', line=dict(width=1.5, color=color)),
                showlegend=True,
                legendgroup=f"{team}_pass",
                legendrank=2 + rank_offset
            )
        )
        
        # Penalty legend entry - RED DOTTED LINE for visibility
    fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode='lines+markers',
                name=f'{team} - Penalty',
                line=dict(color='rgb(255, 50, 50)', width=2, dash='dot'),  # BRIGHT RED DOTS
                marker=dict(size=8, color='yellow', symbol='triangle-up', line=dict(width=1.5, color=color)),
                showlegend=True,
                legendgroup=f"{team}_penalty",
                legendrank=3 + rank_offset
            )
        )
        
    return fig



# ============================================================================
# 9. Format the Figure
# ============================================================================
def update_axes(fig,game_plays):

    home_team = game_plays['home_team'].iloc[0]
    away_team = game_plays['away_team'].iloc[0]
    
    # Update x-axis (field position on bottom)
    fig.update_xaxes(
        title_text=f"Field Position ({home_team} ← | → {away_team}) | Win Probability Background",
        range=[-55, 55],
        tickvals=[-50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50],
        ticktext=['HOME 0', '10', '20', '30', '40', '50', '40', '30', '20', '10', 'AWAY 0'],
        showgrid=True,
        gridcolor='lightgray',
        zeroline=True,
        zerolinecolor='black',
        zerolinewidth=2,
        domain=[0, 0.75]  # Only use left 75% of width for plot
    )
    
    # Update y-axis (time elapsed - FLIPPED so game starts at top)
    # Check if game went to overtime and calculate max time
    max_time = game_plays['time_elapsed_min'].max()
    went_to_ot = max_time > 60
    
    if went_to_ot:
        # Game went to overtime - extend range dynamically based on actual game length
        y_range = [max_time + 3, 0]  # Add 3 min buffer at bottom
        
        # Build tick marks dynamically
        tick_vals = [0, 15, 30, 45, 60]  # Standard quarters
        tick_text = ['0:00', '15:00', '30:00 (Half)', '45:00', '60:00 (END REG)']
        
        # Add OT tick marks every 5 minutes after regulation
        ot_time = 65  # Start at 65 minutes
        while ot_time < max_time:
            tick_vals.append(ot_time)
            tick_text.append(f'{int(ot_time)}:00 (OT)')
            ot_time += 5
    else:
        # Regular game - standard 60 min range
        y_range = [65, 0]
        tick_vals = [0, 15, 30, 45, 60]
        tick_text = ['0:00', '15:00', '30:00 (Half)', '45:00', '60:00']
    
    fig.update_yaxes(
        title_text="Time Elapsed (minutes)",
        range=y_range,  # Reversed range - starts at top, dynamically sized
        showgrid=True,
        gridcolor='lightgray',
        tickvals=tick_vals,
        ticktext=tick_text,
        dtick=15  # Major tick every 15 minutes
    )
    
    # Add visual separator line at end of regulation if OT
    if went_to_ot:
        fig.add_shape(
            type='line',
            x0=-55, x1=55,
            y0=60, y1=60,  # At 60 minutes (end of regulation)
            line=dict(color='darkgrey', width=3, dash='solid'),
            opacity=0.7
        )
    return fig



def add_team_events(fig,game_plays,team_name,color,home=True):
    valid_plays = game_plays[game_plays['field_position'].notna() & 
                          game_plays['play_category'].isin(['run', 'pass', 'punt', 'penalty'])].copy()
    team_plays =  valid_plays[(valid_plays['posteam'] == team_name)&(valid_plays['down']>0)]
    if len(team_plays) == 0:
        return

    drive_starts = valid_plays[valid_plays['is_drive_start'] == True].copy()
    team_drive_starts = drive_starts[drive_starts['posteam'] == team_name].copy()
    
    if len(team_drive_starts) > 0:
        fig.add_trace(
            go.Scatter(
                x=team_drive_starts['field_position'],
                y=team_drive_starts['time_elapsed_min'],
                mode='markers',
                name=f'{team_name} - Drive Start',
                marker=dict(
                    size=11,
                    color=color,
                    symbol='hexagon',
                    line=dict(width=2, color='white')
                ),
                hovertext=team_drive_starts['hover_text'],
                hovertemplate='%{hovertext}<extra></extra>',
                showlegend=True,
                legendgroup=f"{team_name}_highlights",
                legendrank=200 + (0 if home else 50)  # Highlights after main plays
            )
        )


    first_downs = valid_plays[valid_plays['is_first_down'] == True].copy()
    team_first_downs = first_downs[first_downs['posteam'] == team_name].copy()
        
    if len(team_first_downs) > 0:
        fig.add_trace(
            go.Scatter(
                x=team_first_downs['field_position'],
                y=team_first_downs['time_elapsed_min'],
                mode='markers',
                name=f'{team_name} - 1st Down',
                marker=dict(
                    size=11,
                    color=color,
                    symbol='hexagon-open',  # Hollow hexagon like drive starts
                    line=dict(width=2, color=color)
                ),
                hovertext=team_first_downs['hover_text'],
                hovertemplate='%{hovertext}<extra></extra>',
                showlegend=True,
                legendgroup=f"{team_name}_highlights",
                legendrank=201 + (0 if home else 50)  # Highlights after main plays
            )
        )

    # Add markers for each special outcome, colored by team
    special_outcomes_to_plot = [
        'touchdown', 'field_goal_made', 'field_goal_missed',
        'interception', 'fumble_lost', 'punt', 'turnover_on_downs'
    ]
    
    for outcome in special_outcomes_to_plot:
        outcome_plays = game_plays[game_plays['special_outcome'] == outcome].copy()
        
        if len(outcome_plays) > 0:
            # Separate by team to use team colors
            
                # For touchdowns, use td_team if available (handles defensive TDs)
            if outcome == 'touchdown' and 'td_team' in outcome_plays.columns:
                team_outcome = outcome_plays[outcome_plays['td_team'] == team_name].copy()
            else:
                team_outcome = outcome_plays[outcome_plays['posteam'] == team_name].copy()
                
            if len(team_outcome) > 0:
                # Define marker style based on outcome type
                if outcome == 'touchdown':
                    marker_style = dict(symbol='star', size=15, color=color, 
                                          line=dict(color='black', width=2))
                elif outcome == 'field_goal_made':
                        marker_style = dict(symbol='diamond', size=12, color=color, 
                                          line=dict(color='black', width=1))
                elif outcome == 'field_goal_missed':
                        marker_style = dict(symbol='x', size=12, color=color, 
                                          line=dict(width=2))
                elif outcome == 'interception':
                        marker_style = dict(symbol='triangle-down', size=12, color=color, 
                                          line=dict(color='black', width=1))
                elif outcome == 'fumble_lost':
                        marker_style = dict(symbol='triangle-down', size=12, color=color, 
                                          line=dict(color='black', width=1))
                elif outcome == 'punt':
                        marker_style = dict(symbol='circle-open', size=10, color=color, 
                                          line=dict(width=2))
                elif outcome == 'turnover_on_downs':
                        marker_style = dict(symbol='square', size=10, color=color, 
                                          line=dict(color='black', width=1))
                else:
                    continue
                    
                # Determine legend name and rank
                legend_name = f"{team_name} - {outcome.replace('_', ' ').title()}"
                    
                # Set legend rank based on outcome type
                if outcome in ['touchdown', 'field_goal_made']:
                    legend_rank = 300 + (0 if home else 50)  # Scoring first
                elif outcome in ['interception', 'fumble_lost', 'turnover_on_downs']:
                    legend_rank = 350 + (0 if home else 50)  # Turnovers second
                else:
                    legend_rank = 400 + (0 if home else 50)  # Other events last
                    
                fig.add_trace(
                    go.Scatter(
                            x=team_outcome['field_position'],
                            y=team_outcome['time_elapsed_min'],
                            mode='markers',
                            name=legend_name,
                            marker=marker_style,
                            hovertext=team_outcome['hover_text'],
                            hovertemplate='%{hovertext}<extra></extra>',
                            showlegend=True,  # Show in legend
                            legendgroup=f"{team_name}_events",
                            legendrank=legend_rank
                    )
                )
    return fig

def add_score_details(fig,game_plays,team_name,color,home=True):
# Identify extra point and 2-point conversion attempts separately
    xp_1pt = game_plays[game_plays['extra_point_result'].notna()].copy()
    xp_2pt = game_plays[game_plays['two_point_conv_result'].notna()].copy()
    
    # Process 1-point extra point attempts
    if len(xp_1pt) > 0:
        
        team_xp = xp_1pt[xp_1pt['posteam'] == team_name].copy()
            
        if len(team_xp) > 0:
            # Determine x position
            xp_x_position = -50 if not home else 50
                
            # Separate successful and failed attempts
            successful_xp = team_xp[team_xp['extra_point_result'] == 'good'].copy()
            failed_xp = team_xp[team_xp['extra_point_result'].isin(['failed', 'blocked', 'missed'])].copy()
                
            # Plot successful 1pt conversions
            if len(successful_xp) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[xp_x_position] * len(successful_xp),
                        y=successful_xp['time_elapsed_min'],
                        mode='markers',
                        name=f'{team_name} - XP Made',
                        marker=dict(
                            symbol='diamond',
                            size=9,
                            color=color,
                            line=dict(color='gold', width=2)
                        ),
                        hovertext=successful_xp['hover_text'],
                        hovertemplate='%{hovertext}<extra></extra>',
                        showlegend=True,
                        legendgroup=f"{team_name}_events"
                    )
                )
                
            # Plot failed 1pt conversions
            if len(failed_xp) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[xp_x_position] * len(failed_xp),
                        y=failed_xp['time_elapsed_min'],
                        mode='markers',
                        name=f'{team_name} - XP Failed',
                        marker=dict(
                            symbol='diamond-open',
                            size=9,
                            color=color,
                            line=dict(color='red', width=2)
                        ),
                        hovertext=failed_xp['hover_text'],
                        hovertemplate='%{hovertext}<extra></extra>',
                        showlegend=True,
                        legendgroup=f"{team_name}_events"
                    )
                )
    
    # Process 2-point conversion attempts
    if len(xp_2pt) > 0:
        team_2pt = xp_2pt[xp_2pt['posteam'] == team_name].copy()
            
        if len(team_2pt) > 0:
            # Determine x position
            xp_x_position = -50 if not home else 50
                
            # Separate successful and failed attempts
            successful_2pt = team_2pt[team_2pt['two_point_conv_result'] == 'success'].copy()
            failed_2pt = team_2pt[team_2pt['two_point_conv_result'] == 'failure'].copy()
            
            # Plot successful 2pt conversions
            if len(successful_2pt) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[xp_x_position] * len(successful_2pt),
                        y=successful_2pt['time_elapsed_min'],
                        mode='markers',
                        name=f'{team_name} - 2PT Made',
                        marker=dict(
                            symbol='square',
                            size=10,
                            color=color,
                            line=dict(color='gold', width=2)
                        ),
                        hovertext=successful_2pt['hover_text'],
                        hovertemplate='%{hovertext}<extra></extra>',
                        showlegend=True,
                        legendgroup=f"{team_name}_events"
                    )
                )
            
            # Plot failed 2pt conversions
            if len(failed_2pt) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=[xp_x_position] * len(failed_2pt),
                        y=failed_2pt['time_elapsed_min'],
                        mode='markers',
                        name=f'{team_name} - 2PT Failed',
                        marker=dict(
                            symbol='square-open',
                            size=10,
                            color=color,
                            line=dict(color='red', width=2)
                        ),
                        hovertext=failed_2pt['hover_text'],
                        hovertemplate='%{hovertext}<extra></extra>',
                        showlegend=True,
                        legendgroup=f"{team_name}_events"
                    )
                )
    return fig

def add_kicks(fig,game_plays):
    kickoff_plays = game_plays[game_plays['play_category'] == 'kickoff'].copy()

    if len(kickoff_plays) > 0:
    # Add each kickoff as a line segment trace with hover text
        for idx, row in kickoff_plays.iterrows():
            # Create hover text for this specific kickoff
            
            hover_text = []
            hover_text = (
                f"<b>KICKOFF - Q{row['qtr']} {row['time']}</b><br>"
                f"{row['posteam']} kicks off<br>"
                f"{row['desc']}"
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[-55, 55],  # Horizontal line across entire field
                    y=[row['time_elapsed_min'], row['time_elapsed_min']],
                    mode='lines',
                    line=dict(color='purple', width=1.5, dash='dash'),
                    name='Kickoffs',
                    text=[hover_text, hover_text],  # One for each endpoint
                    hovertemplate='%{text}<extra></extra>',
                    showlegend=False,  # We'll add one legend entry below
                    legendgroup='kickoffs',
                    opacity=0.4
                )
            )
        
        # Add single legend entry for all kickoffs
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode='lines',
                name='Kickoffs',
                line=dict(color='purple', width=1.5, dash='dash'),
                showlegend=True,
                legendgroup='kickoffs',
                legendrank=550,  # Near bottom with other events
                opacity=0.4
            )
        )
    return fig

def add_turnovers(fig,game_plays):
    turnover_plays = game_plays[game_plays['special_outcome'].isin([
        'interception', 'fumble_lost', 'turnover_on_downs'
    ])].copy()
    
    if len(turnover_plays) > 0:
        # Add each turnover as a line segment trace with hover text
        for idx, row in turnover_plays.iterrows():
            # Create hover text for this specific turnover
            hover_text = (
                f"<b>TURNOVER - Q{row['qtr']} {row['time']}</b><br>"
                f"{row['posteam']} → {row['defteam']}<br>"
                f"{row['special_outcome'].replace('_', ' ').title()}<br>"
                f"{row['desc'][:100]}"
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[-55, 55],  # Horizontal line across entire field
                    y=[row['time_elapsed_min'], row['time_elapsed_min']],
                    mode='lines',
                    line=dict(color='red', width=1.5, dash='dot'),
                    name='Turnovers',
                    text=[hover_text, hover_text],  # One for each endpoint
                    hovertemplate='%{text}<extra></extra>',  # Use %{text} to suppress x,y
                    showlegend=False,  # We'll add one legend entry below
                    legendgroup='turnovers',
                    opacity=0.5
                )
            )
        
        # Add single legend entry for all turnovers
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode='lines',
                name='Turnovers',
                line=dict(color='red', width=1.5, dash='dot'),
                showlegend=True,
                legendgroup='turnovers',
                legendrank=550,  # Right after kickoffs
                opacity=0.5
            )
        )
    return fig

def add_score_labels(fig,game_plays,home_color='#1f77b4',away_color='#ff7f0e'):
    # Identify all scoring plays (touchdowns and field goals)
    # For touchdowns, we want to show the score AFTER the XP/2PT attempt
    scoring_plays_raw = game_plays[game_plays['special_outcome'].isin(['touchdown', 'field_goal_made'])].copy()
    score_annotations = []
    
    # Create annotation data for each scoring play
    for idx, row in scoring_plays_raw.iterrows():
        # For defensive TDs, use td_team instead of posteam
        # td_team indicates who scored, posteam indicates who had possession
        if 'td_team' in row.index and pd.notna(row['td_team']):
            scoring_team = row['td_team']
        else:
            scoring_team = row['posteam']
        
        # For touchdowns, try to find the subsequent XP/2PT attempt to get final score
        if row['special_outcome'] == 'touchdown':
            # Look for XP/2PT attempt in next few plays
            next_plays = game_plays[game_plays['play_id'] > row['play_id']].head(3)
            xp_play = next_plays[
                (next_plays['extra_point_result'].notna()) | 
                (next_plays['two_point_conv_result'].notna())
            ]
            
            if len(xp_play) > 0:
                # Use score after XP/2PT
                score_row = xp_play.iloc[0]
            else:
                # No XP found, use TD score
                score_row = row
        else:
            # Field goal - use immediately
            score_row = row
        
        home_score = int(score_row['total_home_score'])
        away_score = int(score_row['total_away_score'])
        
        home_team = game_plays['home_team'].iloc[0]
        away_team = game_plays['away_team'].iloc[0]
        # Determine color and position based on which team scored
        team_colors={home_team:home_color,away_team:away_color}
        
        text_color = team_colors[scoring_team]
        
        # Position on the side of the team that scored
        if scoring_team == home_team:
            text_x = 52  # Right side for home team
            text_anchor = 'left'
        else:  # away team
            text_x = -52  # Left side for away team
            text_anchor = 'right'
        
        # Format score text (away-home)
        score_text = f"{away_score}-{home_score}"
        
        text_y = row['time_elapsed_min']  # Use original play time for positioning
        
        score_annotations.append(
            dict(
                x=text_x,
                y=text_y,
                text=score_text,
                showarrow=False,
                font=dict(
                    size=13,
                    color=text_color,
                    family="Arial Black, sans-serif"
                ),
                xanchor=text_anchor,
                # No background box - just text
            )
        )
    try:
        current_annotations = list(fig.layout.annotations)
        current_annotations.append(score_annotations)
        fig.update_layout(annotations=current_annotations)
    except:
        fig.update_layout(annotations=score_annotations)

     
    return fig

def format_main_layout(fig,game_plays,home_color='#1f77b4',away_color='#ff7f0e'):
    home_team = game_plays['home_team'].iloc[0]
    away_team = game_plays['away_team'].iloc[0]
    game_date = game_plays['game_date'].iloc[0]

    final_home_score =game_plays['home_score'].iloc[0]
    final_away_score = game_plays['away_score'].iloc[0]
    
    fig.update_layout(
        title=dict(
            text=(
                f"<span style='color:{away_color}'>{away_team}</span> {final_away_score} @ "
                f"<span style='color:{home_color}'>{home_team}</span> {final_home_score} - {game_date}<br>"
                f"<b>SWEEP</b> Analysis<br>"
                f"<sub>Score & Win-probability Evolution & Excitement Plot</sub>"
            ),
            x=0.5,
            xanchor='center'
        ),
        height=1000,
        width=1200,  # Wider to accommodate side tables
        hovermode='closest',
        plot_bgcolor='white',
        margin=dict(r=320, b=150),  # Right margin for tables, MORE bottom space for legend (increased from 130)
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="top",
            y=-0.10,  # ADJUSTED from -0.18
            xanchor="center",
            x=0.35,  # Shifted left to make room
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='black',
            borderwidth=1
        ),
        font=dict(size=11))
    return fig

    
# Create combined game stats table
def add_game_table(fig,game_plays):
    home_team = game_plays['home_team'].iloc[0]
    away_team = game_plays['away_team'].iloc[0]
    
    # Table 1: Scoring Events & Lead Changes
    scoring_events = game_plays[game_plays['special_outcome'].isin(['touchdown', 'field_goal_made'])].copy()
    
    home_tds = len(scoring_events[(scoring_events['posteam'] == home_team) & (scoring_events['special_outcome'] == 'touchdown')])
    away_tds = len(scoring_events[(scoring_events['posteam'] == away_team) & (scoring_events['special_outcome'] == 'touchdown')])
    home_fgs = len(scoring_events[(scoring_events['posteam'] == home_team) & (scoring_events['special_outcome'] == 'field_goal_made')])
    away_fgs = len(scoring_events[(scoring_events['posteam'] == away_team) & (scoring_events['special_outcome'] == 'field_goal_made')])
    
    # Calculate lead changes
    lead_changes = 0
    prev_leader = None
    for idx, row in game_plays.iterrows():
        margin = row['score_margin']
        if margin > 0:
            current_leader = home_team
        elif margin < 0:
            current_leader = away_team
        else:
            current_leader = 'Tie'
        
        if prev_leader is not None and current_leader != prev_leader and current_leader != 'Tie' and prev_leader != 'Tie':
            lead_changes += 1
        prev_leader = current_leader
    
    # Table 2: Drive & Yards Summary
    drive_summary = game_plays[game_plays['play_type'].isin(['pass', 'run'])].groupby('posteam').agg({
        'drive': 'nunique',
        'yards_gained': 'sum',
        'play_id': 'count'
    }).reset_index()
    
    drive_summary.columns = ['team', 'drives', 'total_yards', 'plays']
    
    # Calculate passing vs rushing yards
    pass_yards = game_plays[game_plays['play_type'] == 'pass'].groupby('posteam')['yards_gained'].sum()
    rush_yards = game_plays[game_plays['play_type'] == 'run'].groupby('posteam')['yards_gained'].sum()
    
    # Penalty yards
    penalty_yards = game_plays[game_plays['penalty'] == 1].groupby('posteam')['penalty_yards'].sum()
    
    # Get final values
    home_drives = drive_summary[drive_summary['team'] == home_team]['drives'].values[0] if len(drive_summary[drive_summary['team'] == home_team]) > 0 else 0
    away_drives = drive_summary[drive_summary['team'] == away_team]['drives'].values[0] if len(drive_summary[drive_summary['team'] == away_team]) > 0 else 0

    
    # Calculate points per drive
    final_home_score = int(game_plays['total_home_score'].iloc[-1])
    final_away_score = int(game_plays['total_away_score'].iloc[-1])
    home_ppd = final_home_score / home_drives if home_drives > 0 else 0
    away_ppd = final_away_score / away_drives if away_drives > 0 else 0
    
    home_pass_yds = pass_yards.get(home_team, 0)
    away_pass_yds = pass_yards.get(away_team, 0)
    home_rush_yds = rush_yards.get(home_team, 0)
    away_rush_yds = rush_yards.get(away_team, 0)
    
    home_penalty_yds = penalty_yards.get(home_team, 0)
    away_penalty_yds = penalty_yards.get(away_team, 0)
    
    home_total_plays = drive_summary[drive_summary['team'] == home_team]['plays'].values[0] if len(drive_summary[drive_summary['team'] == home_team]) > 0 else 0
    away_total_plays = drive_summary[drive_summary['team'] == away_team]['plays'].values[0] if len(drive_summary[drive_summary['team'] == away_team]) > 0 else 0

    real_plays = game_plays[game_plays['is_real_play']]
    avg_excitement = real_plays['play_excitement'].mean()
    avg_unpredictability = real_plays['play_unpredictability'].mean()
    
    combined_stats_text = (
        f"<b>Scoring Summary</b><br>"
        f"{home_team}: {home_tds} TD, {home_fgs} FG<br>"
        f"{away_team}: {away_tds} TD, {away_fgs} FG<br>"
        f"Lead Changes: {lead_changes}<br>"
        f"<br>"
        f"<b>Drive & Yards</b><br>"
        f"<b>{home_team}</b>: {int(home_drives)} drives, {int(home_total_plays)} plays<br>"
        f"  Pass: {int(home_pass_yds)} | Rush: {int(home_rush_yds)} | Pen: {int(home_penalty_yds)} yds<br>"
        f"  PPD: {home_ppd:.2f}<br>"
        f"<b>{away_team}</b>: {int(away_drives)} drives, {int(away_total_plays)} plays<br>"
        f"  Pass: {int(away_pass_yds)} | Rush: {int(away_rush_yds)} | Pen: {int(away_penalty_yds)} yds<br>"
        f"  PPD: {away_ppd:.2f}<br>"
        f"<br>"
        f"<b>Game Metrics</b><br>"
        f"Avg Excitement: {avg_excitement:.2f} pp<br>"
        f"Avg Unpredictability: {avg_unpredictability:.3f}"
    )
    
    combined_stats_dict =dict(text=combined_stats_text,
            xref="paper", yref="paper",
            x=0.87, y=0,  # ADJUSTED x from 0.80 to 0.81
            showarrow=False,
            font=dict(size=8, family='monospace'),  # Smaller font to fit more
            align='left',
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='black',
            borderwidth=1,
            borderpad=8
        )

    fig.add_annotation(combined_stats_dict)

    return fig

def wrap_text(text, width=50):
        """Wrap text to specified width"""
        if pd.isna(text):
            return ""
        words = str(text).split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '<br>    '.join(lines)  # Indent wrapped lines

def add_exciting_table(fig,game_plays):
    ###Get 10 most exciting plays (only real plays with actual excitement)
    
    # Set excitement to 0 for non-real plays (timeouts, 2-min warnings, etc.)
    #game_plays.loc[~game_plays['is_real_play'], 'play_excitement'] = 0
    exciting_candidates = game_plays[game_plays['is_real_play'] & (game_plays['play_excitement'] > 0)]
    #print(exciting_candidates)
    
    most_exciting = exciting_candidates.nlargest(10, 'play_excitement')[
        ['time_elapsed_min', 'desc', 'play_excitement', 'posteam', 'qtr', 'time']
    ].copy()
    
    # Create quarter/time labels
    most_exciting['qtr_time'] = most_exciting['qtr'].astype(str) + 'Q ' + most_exciting['time'].astype(str)
    # Wrap descriptions to max 50 chars per line
    most_exciting['desc_wrapped'] = most_exciting['desc'].apply(lambda x: wrap_text(x, 45))

    # Most exciting plays table
    exciting_plays_text = "<b>Top 10 Exciting Plays</b><br>"
    for idx, (i, row) in enumerate(most_exciting.iterrows(), 1):
        exciting_plays_text += f"<b>{idx}. {row['qtr_time']} (+{row['play_excitement']:.1f}pp)</b><br>"
        exciting_plays_text += f"    {row['desc_wrapped']}<br><br>"
        
    exciting_plays_dict = dict(
            text=exciting_plays_text,
            xref="paper", yref="paper",
            x=0.87, y=0.98,  # ADJUSTED x from 0.78 to 0.81
            showarrow=False,
            font=dict(size=8, family='monospace'),
            align='left',
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255,255,255,0.95)',
            bordercolor='black',
            borderwidth=1,
            borderpad=8
        )
    #try:
    #current_annotations = list(fig.layout.annotations)
    #current_annotations.append((exciting_plays_dict))
    #fig.update_layout(annotations=current_annotations)
    #except:
    fig.add_annotation(exciting_plays_dict)

    return fig
    