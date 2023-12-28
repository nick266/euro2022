import pandas as pd
from statsbombpy import sb
import streamlit as st


@st.cache_data
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


@st.cache_data
def preprocess_data(df_raw):
    df_preprocessed = df_raw.sort_values(["match_id", "minute", "timestamp"])
    df_preprocessed.reset_index(inplace=True)
    return df_preprocessed


@st.cache_data
def create_kpis(df_match):
    kpi_summary = pd.DataFrame()
    for team in df_match.team.unique():
        other_team = [t for t in df_match.team.unique() if t != team]
        team_events = df_match[df_match.team == team]
        other_team_events = df_match[df_match.team == other_team[0]]

        # Total goals
        goals_scored = team_events[
            team_events["shot_outcome"] == "Goal"
        ].shape[  # noqa: E501
            0
        ]  # noqa: E501
        goals_conceded = other_team_events[
            other_team_events["shot_outcome"] == "Goal"
        ].shape[
            0
        ]  # noqa: E501

        # Total shots
        shots = len(team_events[team_events["type"] == "Shot"])
        # Total xg
        shot_statsbomb_xg_scored = team_events["shot_statsbomb_xg"].sum()
        shot_statsbomb_xg_conceded = other_team_events[
            "shot_statsbomb_xg"
        ].sum()  # noqa: E501
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

        # Total interceptions
        interceptions = len(team_events[team_events["type"] == "Interception"])

        # Total clearances
        clearances = len(team_events[team_events["type"] == "Clearance"])

        # Percentage of possession
        team_possession_seconds = team_events[
            (team_events["type"] != "Pressure")
        ].duration.sum()
        other_team_possession_seconds = other_team_events[
            (other_team_events["type"] != "Pressure")
        ].duration.sum()

        kpi_summary_temp = pd.DataFrame(
            {
                "goals_scored": [goals_scored],
                "goals_conceded": [goals_conceded],
                "shot_statsbomb_xg_scored": [shot_statsbomb_xg_scored],
                "shot_statsbomb_xg_conceded": [shot_statsbomb_xg_conceded],
                "shots": [shots],
                "passes": [passes],
                "pass_accuracy": [pass_accuracy],
                "interceptions": [interceptions],
                "clearances": [clearances],
                "possession": [
                    team_possession_seconds
                    / (other_team_possession_seconds + team_possession_seconds)
                ],
            },
            index=[team],
        )
        kpi_summary = pd.concat(
            [kpi_summary, kpi_summary_temp], ignore_index=False
        )  # noqa: E501
    return kpi_summary


def color_cells(row):
    cell_color = []
    for val in row:
        if row["high_is_good"] * row["Team Values"] < row["high_is_good"] * (
            row["Average"] - 0.25 * row["STD"]
        ):
            color = "red"
        elif row["high_is_good"] * row["Team Values"] > row["high_is_good"] * (
            row["Average"] + 0.25 * row["STD"]
        ):
            color = "green"
        else:
            color = "orange"
        cell_color.append(f"color: {color}")
    return cell_color


@st.cache_data
def run_code(euro_competition_id, euro_season_id):
    match_ids = sb.matches(
        competition_id=euro_competition_id, season_id=euro_season_id
    ).match_id

    df_raw = get_data(match_ids)
    df_preprocessed = preprocess_data(df_raw)
    df_kpis = df_preprocessed.groupby(["match_id"]).apply(create_kpis)
    return df_kpis


competitions = sb.competitions()
womens_euro_competition = competitions[
    competitions["competition_name"] == "UEFA Women's Euro"
]
womens_euro_2022 = womens_euro_competition[
    womens_euro_competition["season_name"] == "2022"
]
euro_competition_id = womens_euro_2022.competition_id.unique()[0]
euro_season_id = womens_euro_2022.season_id.unique()[0]

df_kpis = run_code(euro_competition_id, euro_season_id)


st.title("Team Statistics Dashboard")

# Select team
selected_team = st.selectbox(
    "Select a team", df_kpis.index.get_level_values(1).unique()
)  # noqa: E501

# Display team statistics
team_stats = df_kpis.xs(selected_team, level=1).mean()
average = df_kpis.mean()
std_dev = df_kpis.std()
high_is_good = [1, -1, 1, -1, 1, 1, 1, 1, 1, 1]
result_df = pd.DataFrame(
    {
        "Team Values": team_stats,
        "Average": average,
        "STD": std_dev,
        "high_is_good": high_is_good,
    }
)
styled_result_df = result_df.style.apply(color_cells, axis=1)
st.write(f"Statistics for {selected_team}:")
st.write(styled_result_df)
#  to do:
#  caching (check)
#  colors for dashboard
#  possession in percentag (check)
#  defender distance
#  filter for dates
#  soccer field metric (eg pass direction)
#  list of players with xgoals and xassits
#  unit tests
#  doc strings
#  new metric based on difference in thread of scoring or conceding a goal
#  in after an event
