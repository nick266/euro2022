import pandas as pd
from statsbombpy import sb
import plotly.express as px
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import streamlit as st


def preprocessing(euro_competition_id, euro_season_id, match_id):
    euro_matches = sb.matches(
        competition_id=euro_competition_id, season_id=euro_season_id
    )
    events_data = sb.events(match_id=match_id)
    score = {
        euro_matches[euro_matches.match_id == match_id]
        .home_team.values[0]: euro_matches[euro_matches.match_id == match_id]
        .home_score.values[0],
        euro_matches[euro_matches.match_id == match_id]
        .away_team.values[0]: euro_matches[euro_matches.match_id == match_id]
        .away_score.values[0],
    }
    events_data.sort_values(["minute", "timestamp"], inplace=True)
    parsed_time = events_data["timestamp"].apply(
        lambda x: datetime.strptime(x, "%H:%M:%S.%f")
    )
    time_differences = parsed_time.diff().dt.total_seconds()
    events_data["time_differences"] = [
        x if ((x > 0) & (x < 60 * 5)) else 0 for x in time_differences
    ]
    return events_data, score


def enrich_data(events_data, team, other_team, score):
    kpi_summary = []
    team_events = events_data[events_data["team"] == team]

    # Total shots
    shots = len(team_events[team_events["type"] == "Shot"])
    # Total xg
    shot_statsbomb_xg = team_events["shot_statsbomb_xg"].sum()
    # Total passes
    passes = len(team_events[team_events["type"] == "Pass"])

    # Pass accuracy
    completed_passes = len(
        team_events[
            (team_events["type"] == "Pass") & (team_events["pass_outcome"].isnull())
        ]
    )
    pass_accuracy = (completed_passes / passes) * 100

    # Total duels won
    duels_won = len(
        team_events[
            (team_events["type"] == "Duel") & (team_events["duel_outcome"] == "Won")
        ]
    )

    # Total tackles
    tackles = len(team_events[team_events["type"] == "Tackle"])

    # Total interceptions
    interceptions = len(team_events[team_events["type"] == "Interception"])

    # Total clearances
    clearances = len(team_events[team_events["type"] == "Clearance"])

    # Percentage of possession
    team_possession = events_data[
        (events_data["possession_team"] == team) & (events_data["type"] != "Pressure")
    ].duration.sum()
    other_team_possession = events_data[
        (events_data["possession_team"] == other_team)
        & (events_data["type"] != "Pressure")
    ].duration.sum()
    possession = team_possession / (team_possession + other_team_possession)
    kpi_summary.append(
        {
            "team": team,
            "score": score[team],
            "shots": shots,
            "shot_statsbomb_xg": shot_statsbomb_xg,
            "passes": passes,
            "pass_accuracy": pass_accuracy,
            "duels_won": duels_won,
            "tackles": tackles,
            "interceptions": interceptions,
            "clearances": clearances,
            "possession": possession,
        }
    )
    return kpi_summary


def get_summary(events_data: pd.DataFrame, score: dict):  # Calculate KPIs for each team
    kpi_summary = pd.DataFrame()
    teams = events_data["team"].unique()

    for team in teams:
        other_team = [opponent for opponent in teams if opponent != team][0]
        df_temp = pd.DataFrame(enrich_data(events_data, team, other_team, score))
        kpi_summary = pd.concat([kpi_summary, df_temp], ignore_index=True)
    return kpi_summary


competitions = sb.competitions()
womens_euro_competition = competitions[
    competitions["competition_name"] == "UEFA Women's Euro"
]
womens_euro_2022 = womens_euro_competition[
    womens_euro_competition["season_name"] == "2022"
]


kpi_summary_df = pd.DataFrame()
euro_competition_id = womens_euro_2022.competition_id.unique()[0]
euro_season_id = womens_euro_2022.season_id.unique()[0]
for match_id in sb.matches(
    competition_id=euro_competition_id, season_id=euro_season_id
).match_id.unique():
    events_data, score = preprocessing(euro_competition_id, euro_season_id, match_id)
    df_temp = get_summary(events_data, score)
    kpi_summary_df = pd.concat([kpi_summary_df, df_temp], ignore_index=True)

df = kpi_summary_df.groupby("team").mean()

st.title("Team Statistics Dashboard")

# Select team
selected_team = st.selectbox("Select a team", df.index)

# Display team statistics
team_stats = df.loc[selected_team]
average = df.mean()
std_dev = df.std()
result_df = pd.DataFrame(
    {"Team Values": team_stats, "Average": average, "STD": std_dev}
)
st.write(f"Statistics for {selected_team}:")
st.write(result_df)
