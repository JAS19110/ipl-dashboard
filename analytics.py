from pathlib import Path

import pandas as pd
import numpy as np

# ==========================================
# 1. LOAD DATA & CLEAN COLUMNS
# ==========================================
script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent

csv_search_patterns = [
    "IPL*.csv",
    "*Dashboard*.csv",
    "*Excel*.csv",
    "IPL.Dashboard.Excel.Data.csv",
    "IPL Dashboard Excel Data.csv",
]

csv_candidates = []
for directory in [script_dir, project_dir]:
    for pattern in csv_search_patterns:
        csv_candidates.extend(directory.glob(pattern))

csv_candidates = sorted({path.resolve() for path in csv_candidates if path.is_file()})
file_path = csv_candidates[0] if csv_candidates else None

if file_path is None:
    checked_paths = [script_dir / "IPL Dashboard Excel Data.csv", project_dir / "IPL Dashboard Excel Data.csv"]
    raise FileNotFoundError(
        "Could not find the IPL dataset CSV.\n"
        f"Looked in: {', '.join(str(path) for path in checked_paths)}"
    )

df = pd.read_csv(file_path)

# Clean column headers by removing newlines and extra spacing
df.columns = [c.replace('\n', ' ').strip() for c in df.columns]

print(f"Dataset Shape: {df.shape[0]} rows, {df.shape[1]} columns")
print("=" * 60)

# ==========================================
# 2. MATCH & TEAM LEVEL ANALYTICS
# ==========================================
match_df = df.dropna(subset=['Winner']).copy()
total_matches = len(match_df)

# Team Win Standings
team_wins = match_df['Winner'].value_counts().reset_index()
team_wins.columns = ['Team', 'Total Wins']
team_wins['Win Percentage (%)'] = ((team_wins['Total Wins'] / total_matches) * 100).round(2)

print("\n--- TEAM WIN STANDINGS ---")
print(team_wins.head(10).to_string(index=False))

# ==========================================
# 3. PLAYER BATTING ANALYTICS
# ==========================================
# Extract Team A and Team B Batting stats
batting_a = df[['Team A Players', 'Runs  By  Team A Players', 'Balls Faced  by Team A Players', 
                'Fours by  Team A Players', 'Sixes by  Team A Players', 'Dismissed  Team A Players']].rename(columns={
    'Team A Players': 'Player', 'Runs  By  Team A Players': 'Runs', 
    'Balls Faced  by Team A Players': 'Balls', 'Fours by  Team A Players': 'Fours', 
    'Sixes by  Team A Players': 'Sixes', 'Dismissed  Team A Players': 'Dismissals'
})

batting_b = df[['Team B Players', 'Runs  By  Team B Players', 'Balls Faced  by  Team B Players', 
                'Fours by Team B Players', 'Sixes  by  Team B Players', 'Dismissed  Team B Players']].rename(columns={
    'Team B Players': 'Player', 'Runs  By  Team B Players': 'Runs', 
    'Balls Faced  by  Team B Players': 'Balls', 'Fours by Team B Players': 'Fours', 
    'Sixes  by  Team B Players': 'Sixes', 'Dismissed  Team B Players': 'Dismissals'
})

batting_all = pd.concat([batting_a, batting_b]).dropna(subset=['Player'])

# Aggregate Batting Statistics
batting_summary = batting_all.groupby('Player').agg(
    Innings=('Runs', 'count'),
    Total_Runs=('Runs', 'sum'),
    Total_Balls=('Balls', 'sum'),
    Total_Fours=('Fours', 'sum'),
    Total_Sixes=('Sixes', 'sum'),
    Total_Dismissals=('Dismissals', 'sum')
).reset_index()

# Calculate Derived Batting Metrics
batting_summary['Batting Average'] = (batting_summary['Total_Runs'] / batting_summary['Total_Dismissals'].replace(0, 1)).round(2)
batting_summary['Strike Rate'] = ((batting_summary['Total_Runs'] / batting_summary['Total_Balls'].replace(0, np.nan)) * 100).round(2)
top_batters = batting_summary.sort_values(by='Total_Runs', ascending=False)

print("\n--- TOP 10 ALL-TIME RUN SCORERS ---")
print(top_batters[['Player', 'Innings', 'Total_Runs', 'Batting Average', 'Strike Rate', 'Total_Sixes']].head(10).to_string(index=False))

# ==========================================
# 4. PLAYER BOWLING ANALYTICS
# ==========================================
# Extract Team A and Team B Bowling stats
bowling_a = df[['Team A Players', 'Wickets  By  Team A Players', 'Overs Bowled  by  Team A Players', 
                'Runs Conceded  by  Team A Players', 'Dot Balls  by  Team A Players']].rename(columns={
    'Team A Players': 'Player', 'Wickets  By  Team A Players': 'Wickets', 
    'Overs Bowled  by  Team A Players': 'Overs', 'Runs Conceded  by  Team A Players': 'Runs_Conceded', 
    'Dot Balls  by  Team A Players': 'Dot_Balls'
})

bowling_b = df[['Team B Players', 'Wickets  By  Team B Players', 'Overs Bowled  by  Team B Players', 
                'Runs Conceded by Team B Players', 'Dot Balls by Team B Players']].rename(columns={
    'Team B Players': 'Player', 'Wickets  By  Team B Players': 'Wickets', 
    'Overs Bowled  by  Team B Players': 'Overs', 'Runs Conceded by Team B Players': 'Runs_Conceded', 
    'Dot Balls by Team B Players': 'Dot_Balls'
})

bowling_all = pd.concat([bowling_a, bowling_b]).dropna(subset=['Player'])

# Aggregate Bowling Statistics
bowling_summary = bowling_all.groupby('Player').agg(
    Innings=('Wickets', 'count'),
    Total_Wickets=('Wickets', 'sum'),
    Total_Overs=('Overs', 'sum'),
    Total_Runs_Conceded=('Runs_Conceded', 'sum'),
    Total_Dot_Balls=('Dot_Balls', 'sum')
).reset_index()

# Calculate Derived Bowling Metrics
bowling_summary['Economy Rate'] = (bowling_summary['Total_Runs_Conceded'] / bowling_summary['Total_Overs'].replace(0, np.nan)).round(2)
bowling_summary['Bowling Strike Rate'] = ((bowling_summary['Total_Overs'] * 6) / bowling_summary['Total_Wickets'].replace(0, np.nan)).round(2)
top_bowlers = bowling_summary.sort_values(by='Total_Wickets', ascending=False)

print("\n--- TOP 10 ALL-TIME WICKET TAKERS ---")
print(top_bowlers[['Player', 'Innings', 'Total_Wickets', 'Total_Overs', 'Economy Rate', 'Total_Dot_Balls']].head(10).to_string(index=False))

# ==========================================
# 5. FIELDING ANALYTICS
# ==========================================
fielding_a = df[['Team A Players', 'Catches  by  Team A Players', 'Stumpings by Team A Players', 'Run Outs  by  Team A Players']].rename(columns={
    'Team A Players': 'Player', 'Catches  by  Team A Players': 'Catches', 
    'Stumpings by Team A Players': 'Stumpings', 'Run Outs  by  Team A Players': 'Run_Outs'
})

fielding_b = df[['Team B Players', 'Catches by  Team B Players', 'Stumpings by  Team B Players', 'Run Outs by  Team B Players']].rename(columns={
    'Team B Players': 'Player', 'Catches by  Team B Players': 'Catches', 
    'Stumpings by  Team B Players': 'Stumpings', 'Run Outs by  Team B Players': 'Run_Outs'
})

fielding_all = pd.concat([fielding_a, fielding_b]).dropna(subset=['Player'])

fielding_summary = fielding_all.groupby('Player').agg(
    Catches=('Catches', 'sum'),
    Stumpings=('Stumpings', 'sum'),
    Run_Outs=('Run_Outs', 'sum')
).reset_index()

fielding_summary['Total Dismissals'] = fielding_summary['Catches'] + fielding_summary['Stumpings'] + fielding_summary['Run_Outs']
top_fielders = fielding_summary.sort_values(by='Total Dismissals', ascending=False)
print("\n--- TOP 10 FIELDERS & KEEPERS ---")
print(top_fielders.head(10).to_string(index=False))

# ==========================================
# 6. OVERALL STATISTICAL SUMMARY
# ==========================================
print("\n--- DATASET METRIC DESCRIPTIVE STATS ---")
print(batting_summary[['Total_Runs', 'Batting Average', 'Strike Rate']].describe().round(2))
