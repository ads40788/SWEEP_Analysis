import nfl_data_py as nfl
import requests
import pandas as pd
from io import BytesIO

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
        
def view_games(season_data, week = None, team = None):
    season_data_ = season_data.copy()
    if week == None:
        pass
    else:
        season_data_ = season_data_[season_data_['week']==week]
    if team == None:
            pass
    else:
        season_data_ = season_data_[(season_data_['home_team']==team)|(season_data_['away_team']==team)]
    print(season_data_[['game_id','week','home_team','away_team','week']].drop_duplicates().head(50))
    
    return list(season_data_[['game_id','week','home_team','away_team','week']].drop_duplicates()['game_id'])