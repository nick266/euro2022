import pandas as pd
from statsbombpy import sb
import streamlit as st


def get_data(match_ids):
    event_data_tot = pd.DataFrame()
    for match_id in match_ids:
        event_data = sb.events(match_id=match_id)
        df_360 = pd.read_json(
            f"/Users/borgwardt/Documents/repos/open-data/data/three-sixty/{match_id}.json"  # noqa: E501
        )
        df_merged = pd.merge(
            event_data, df_360, how="left", left_on="id", right_on="event_uuid"
        )
        event_data_tot = pd.concat(
            [event_data_tot, df_merged], ignore_index=True
        )  # noqa: E501
    return event_data_tot


def preprocess_data(df_raw):
    df_preprocessed = df_raw.sort_values(["match_id", "minute", "timestamp"])
    df_preprocessed.reset_index(inplace=True)
    return df_preprocessed


def create_kpis(team_events):
    # Total goals
    goals = team_events[team_events["shot_outcome"] == "Goal"].shape[0]

    # Total shots
    shots = len(team_events[team_events["type"] == "Shot"])
    # Total xg
    shot_statsbomb_xg = team_events["shot_statsbomb_xg"].sum()
    # Total passes
    passes = len(team_events[team_events["type"] == "Pass"])

    # Pass accuracy
    completed_passes = len(
        team_events[
            (team_events["type"] == "Pass")
            & (team_events["pass_outcome"].isnull())  # noqa: E501
        ]
    )
    pass_accuracy = (completed_passes / passes) * 100

    # Total duels won
    duels_won = len(
        team_events[
            (team_events["type"] == "Duel")
            & (team_events["duel_outcome"] == "Won")  # noqa: E501
        ]
    )

    # Total tackles
    tackles = len(team_events[team_events["type"] == "Tackle"])

    # Total interceptions
    interceptions = len(team_events[team_events["type"] == "Interception"])

    # Total clearances
    clearances = len(team_events[team_events["type"] == "Clearance"])

    # Percentage of possession
    team_possession_seconds = team_events[
        (team_events["type"] != "Pressure")
    ].duration.sum()
    kpi_summary = pd.DataFrame(
        {
            "goals": [goals],
            "shots": [shots],
            "shot_statsbomb_xg": [shot_statsbomb_xg],
            "passes": [passes],
            "pass_accuracy": [pass_accuracy],
            "duels_won": [duels_won],
            "tackles": [tackles],
            "interceptions": [interceptions],
            "clearances": [clearances],
            "possession_seconds": [team_possession_seconds],
        }
    )
    return kpi_summary


competitions = sb.competitions()
womens_euro_competition = competitions[
    competitions["competition_name"] == "UEFA Women's Euro"
]
womens_euro_2022 = womens_euro_competition[
    womens_euro_competition["season_name"] == "2022"
]
euro_competition_id = womens_euro_2022.competition_id.unique()[0]
euro_season_id = womens_euro_2022.season_id.unique()[0]
match_ids = sb.matches(
    competition_id=euro_competition_id, season_id=euro_season_id
).match_id

df_raw = get_data(match_ids)
df_preprocessed = preprocess_data(df_raw)
df_kpis = df_preprocessed.groupby(["match_id", "team"]).apply(create_kpis)
df_kpis.reset_index(level=2, drop=True, inplace=True)

st.title("Team Statistics Dashboard")

# Select team
selected_team = st.selectbox(
    "Select a team", df_kpis.index.get_level_values(1)
)  # noqa: E501

# Display team statistics
team_stats = df_kpis.xs(selected_team, level=1).mean()
average = df_kpis.mean()
std_dev = df_kpis.std()
result_df = pd.DataFrame(
    {"Team Values": team_stats, "Average": average, "STD": std_dev}
)
st.write(f"Statistics for {selected_team}:")
st.write(result_df)
