from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "visualizations"
OUTPUT_DIR.mkdir(exist_ok=True)


def find_dataset():
    candidates = [
        BASE_DIR / "IPL.Dashboard.Excel.Data.csv",
        BASE_DIR / "IPL Dashboard Excel Data.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "IPL dataset not found. Expected one of: "
        + ", ".join(path.name for path in candidates)
    )


def clean_columns(data):
    data = data.copy()
    data.columns = [" ".join(str(column).replace("\n", " ").replace("\r", " ").split()) for column in data.columns]
    return data


def build_player_data(data):
    common = {
        "Runs": "Runs",
        "Balls": "Balls",
        "Fours": "Fours",
        "Sixes": "Sixes",
        "Dismissals": "Dismissals",
        "Wickets": "Wickets",
        "Overs": "Overs",
        "Runs Conceded": "Runs Conceded",
        "Dot Balls": "Dot Balls",
        "Catches": "Catches",
        "Stumpings": "Stumpings",
        "Run Outs": "Run Outs",
    }
    column_groups = {
        "A": {
            "Player": "Team A Players",
            **{key: f"{value} by  Team A Players" for key, value in common.items()},
        },
        "B": {
            "Player": "Team B Players",
            **{key: f"{value} by Team B Players" for key, value in common.items()},
        },
    }

    # The source uses inconsistent spacing in a few Team A headers.
    column_groups["A"].update({
        "Runs": "Runs  By  Team A Players",
        "Balls": "Balls Faced  by  Team A Players",
        "Fours": "Fours by  Team A Players",
        "Sixes": "Sixes by  Team A Players",
        "Dismissals": "Dismissed  Team A Players",
        "Wickets": "Wickets  By  Team A Players",
        "Overs": "Overs Bowled  by  Team A Players",
        "Runs Conceded": "Runs Conceded  by  Team A Players",
        "Dot Balls": "Dot Balls  by  Team A Players",
        "Catches": "Catches  by  Team A Players",
        "Stumpings": "Stumpings by Team A Players",
        "Run Outs": "Run Outs  by  Team A Players",
    })
    column_groups["B"].update({
        "Runs": "Runs  By  Team B Players",
        "Balls": "Balls Faced  by  Team B Players",
        "Fours": "Fours by Team B Players",
        "Sixes": "Sixes  by  Team B Players",
        "Dismissals": "Dismissed  Team B Players",
        "Wickets": "Wickets  By  Team B Players",
        "Overs": "Overs Bowled  by  Team B Players",
        "Runs Conceded": "Runs Conceded by Team B Players",
        "Dot Balls": "Dot Balls by Team B Players",
        "Catches": "Catches by  Team B Players",
        "Stumpings": "Stumpings by Team B Players",
        "Run Outs": "Run Outs by  Team B Players",
    })

    frames = []
    for raw_columns in column_groups.values():
        columns = {key: " ".join(value.split()) for key, value in raw_columns.items()}
        frame = data[list(columns.values())].rename(columns={value: key for key, value in columns.items()})
        frames.append(frame)

    player_data = pd.concat(frames, ignore_index=True).dropna(subset=["Player"])
    numeric_columns = [column for column in player_data.columns if column != "Player"]
    player_data[numeric_columns] = player_data[numeric_columns].apply(pd.to_numeric, errors="coerce").fillna(0)
    return player_data


def save_chart(filename):
    figure = plt.gcf()
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / filename, dpi=300)
    plt.close(figure)


def bar_chart(values, title, xlabel, palette, filename, label_offset):
    plt.figure(figsize=(10, 6))
    axis = sns.barplot(
        x=values.values,
        y=values.index,
        hue=values.index,
        palette=palette,
        legend=False,
    )
    axis.set(title=title, xlabel=xlabel, ylabel="Player or Team")
    for bar in axis.patches:
        value = bar.get_width()
        axis.annotate(
            f"{int(value):,}",
            (value + label_offset, bar.get_y() + bar.get_height() / 2),
            ha="left",
            va="center",
        )
    save_chart(filename)


def main():
    sns.set_theme(style="whitegrid")
    data = clean_columns(pd.read_csv(find_dataset()))
    players = build_player_data(data)

    winners = data.dropna(subset=["Winner"])["Winner"].value_counts().head(10)
    bar_chart(winners, "Top IPL Franchise Victories", "Total Matches Won", "Blues_r", "01_top_wins.png", 1.5)

    runs = players.groupby("Player")["Runs"].sum().sort_values(ascending=False).head(10)
    bar_chart(runs, "Top 10 All-Time Run Scorers", "Total Career Runs", "Purples_r", "02_top_batters.png", 100)

    wickets = players.groupby("Player")["Wickets"].sum().sort_values(ascending=False).head(10)
    bar_chart(wickets, "Top 10 All-Time Wicket Takers", "Total Wickets", "Greens_r", "03_top_bowlers.png", 2)

    batting = players.groupby("Player")[['Runs', 'Balls']].sum()
    batting["Strike Rate"] = batting["Runs"].div(batting["Balls"].replace(0, pd.NA)).mul(100)
    high_scorers = batting[batting["Runs"] >= 3000].reset_index()
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=high_scorers, x="Runs", y="Strike Rate", size="Runs", hue="Strike Rate", palette="viridis", sizes=(50, 400))
    for _, row in high_scorers.iterrows():
        plt.annotate(row["Player"], (row["Runs"] + 60, row["Strike Rate"]))
    plt.title("Batting Impact: Runs vs Strike Rate")
    save_chart("04_runs_vs_strike_rate.png")

    sixes = players.groupby("Player")["Sixes"].sum().sort_values(ascending=False).head(10)
    bar_chart(sixes, "Top 10 Six Hitters", "Total Sixes", "Oranges_r", "05_top_sixes.png", 3)

    fours = players.groupby("Player")["Fours"].sum().sort_values(ascending=False).head(10)
    bar_chart(fours, "Top 10 Four Hitters", "Total Fours", "YlOrBr_r", "06_top_fours.png", 8)

    bowling = players.groupby("Player")[['Wickets', 'Overs', 'Runs Conceded']].sum()
    bowling["Economy"] = bowling["Runs Conceded"].div(bowling["Overs"].replace(0, pd.NA))
    high_wicket_takers = bowling[bowling["Wickets"] >= 120].reset_index()
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=high_wicket_takers, x="Wickets", y="Economy", size="Wickets", hue="Economy", palette="coolwarm", sizes=(50, 350))
    for _, row in high_wicket_takers.iterrows():
        plt.annotate(row["Player"], (row["Wickets"] + 1.5, row["Economy"]))
    plt.title("Bowling Efficiency: Wickets vs Economy")
    save_chart("07_wickets_vs_economy.png")

    dot_balls = players.groupby("Player")["Dot Balls"].sum().sort_values(ascending=False).head(10)
    bar_chart(dot_balls, "Top 10 Dot Ball Specialists", "Total Dot Balls", "YlGnBu_r", "08_top_dot_balls.png", 20)

    players["Field Dismissals"] = players[["Catches", "Stumpings", "Run Outs"]].sum(axis=1)
    fielders = players.groupby("Player")["Field Dismissals"].sum().sort_values(ascending=False).head(10)
    bar_chart(fielders, "Top 10 Fielders and Keepers", "Total Field Dismissals", "rocket", "09_fielding_leaders.png", 2)

    top_players = runs.index
    boundaries = players.groupby("Player")[["Fours", "Sixes"]].sum().loc[top_players]
    boundaries.plot(kind="barh", stacked=True, color=["#1f77b4", "#ff7f0e"], figsize=(10, 6))
    plt.title("Boundary Composition for Top 10 Batters")
    plt.xlabel("Total Boundaries")
    plt.ylabel("Player")
    plt.legend(["Fours", "Sixes"])
    plt.gca().invert_yaxis()
    save_chart("10_boundary_composition.png")

    print(f"Created 10 charts in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
