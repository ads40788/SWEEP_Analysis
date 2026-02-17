"""
SWEEP: Score & Win-probability Evolution & Excitement Plot
NFL game visualization package
"""

# Import main functions to package level
from .sweep_main import (
    get_visualization,
    run_sweep_viz,
    make_sweep_data
)

from .sweep_viz import (
    create_viz,
    viz_probability,
    add_team_traces,
    update_axes,
    format_main_layout,
    add_team_events,
    add_score_details,
    add_kicks,
    add_turnovers,
    add_score_labels,
    add_game_table,
    wrap_text,
    add_exciting_table
)

from .sweep_data import (
    download_nfl_data_season,
    get_game_info,
    filter_non_plays,
    calculate_time_elapsed,
    calculate_field_position_home_perspective,
    enhance_time_and_field,
    categorize_play,
    identify_special_outcome,
    categorize_game_data,
    label_drives_firsts,
    calculate_excitement,
    create_hover_text,
    create_final_display_data
)

from .sweep_download import (
    download_nfl_data_season,
    view_games
)

# Define what gets imported with "from sweep import *"

# Package metadata
__version__ = '1.0.0'
__author__ = 'Tony Sirianni'