import pandas as pd
import numpy as np

def load_and_clean_ipl_data(file_path):
    """Loads CSV, cleans column names, and forward-fills match metadata."""
    df = pd.read_csv(file_path)
    
    # Forward-fill match-level information across merged/empty rows
    match_cols = [
        'Date of Match', 'Team A', 'Team B', 
        'Total Runs \nof Team A', 'Total Runs\nof Team B', 'Winner'
    ]
    for col in match_cols:
        if col in df.columns:
            df[col] = df[col].ffill()
            
    # Normalize column headers by removing newline characters
    df.columns = [col.replace('\n', ' ').strip() for col in df.columns]
    return df

def get_player_stats(df):
    """
    Separates Team A and Team B player statistics, standardizes columns,
    combines them into a single record set, and computes aggregated metrics.
    """
    # Extract Team A player stats
    team_a_cols = [c for c in df.columns if 'Team A' in c]
    team_a_df = df[[c for c in team_a_cols if 'Total Runs' not in c and c != 'Team A']].copy()
    
    team_a_df.columns = [
        c.replace('Team A Players', 'Player')
         .replace('by Team A Players', '')
         .replace('of Team A Players Out of Six Bolls How many Runs He Gave', '')
         .replace('of Team A Players', '')
         .replace('Team A', '')
         .strip() 
        for c in team_a_df.columns
    ]
    
    # Extract Team B player stats
    team_b_cols = [c for c in df.columns if 'Team B' in c]
    team_b_df = df[[c for c in team_b_cols if 'Total Runs' not in c and c != 'Team B']].copy()
    
    team_b_df.columns = [
        c.replace('Team B Players', 'Player')
         .replace('by Team B Players', '')
         .replace('of Team B Players', '')
         .replace('Team B', '')
         .strip() 
        for c in team_b_df.columns
    ]
    
    # Combine datasets from both teams
    combined = pd.concat([team_a_df, team_b_df], ignore_index=True)
    combined = combined.dropna(subset=['Player'])
    
    # Aggregate overall stats per player
    player_summary = combined.groupby('Player').agg({
        'Runs By': 'sum',
        'Balls Faced': 'sum',
        'Fours': 'sum',
        'Sixes': 'sum',
        'Wickets By': 'sum',
        'Overs Bowled': 'sum',
        'Runs Conceded': 'sum',
        'Catches': 'sum'
    }).reset_index()
    
    # Compute career Batting Strike Rate and Bowling Economy Rate
    player_summary['Strike Rate'] = np.where(
        player_summary['Balls Faced'] > 0, 
        (player_summary['Runs By'] / player_summary['Balls Faced']) * 100, 
        0
    )
    player_summary['Economy'] = np.where(
        player_summary['Overs Bowled'] > 0, 
        player_summary['Runs Conceded'] / player_summary['Overs Bowled'], 
        0
    )
    
    return player_summary.round(2)

def get_match_summaries(df):
    """Generates unique match outcomes and team scores."""
    match_summary = df[['Date of Match', 'Team A', 'Total Runs of Team A', 'Team B', 'Total Runs of Team B', 'Winner']].drop_duplicates()
    return match_summary

if __name__ == "__main__":
    file_path = "IPL Dashboard Excel Data.csv"
    
    # 1. Clean raw dataset
    ipl_df = load_and_clean_ipl_data(file_path)
    
    # 2. Get aggregated player stats
    player_performance = get_player_stats(ipl_df)
    
    # 3. Get match results summary
    match_results = get_match_summaries(ipl_df)
    
    print("--- Top 5 Run Scorers ---")
    print(player_performance.sort_values(by='Runs By', ascending=False).head())
    
    print("\n--- Top 5 Wicket Takers ---")
    print(player_performance.sort_values(by='Wickets By', ascending=False).head())

    # Optionally export cleaned output to Excel for interactive dashboards
    # with pd.ExcelWriter("Cleaned_IPL_Dashboard.xlsx") as writer:
    #     player_performance.to_excel(writer, sheet_name="Player Stats", index=False)
    #     match_results.to_excel(writer, sheet_name="Match Results", index=False)