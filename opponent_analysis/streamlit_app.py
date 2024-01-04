import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import numpy as np
from opponent_analysis.preprocessing import Preprocessing
from opponent_analysis.data import Data
from opponent_analysis.kpis import KPIs
from opponent_analysis.config import Config

conf = Config()


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


def create_pass_analysis(filtered_data):
    # Create the figure
    fig, ax = plt.subplots(figsize=(10, 6), tight_layout=True)

    # Initialize the pitch
    pitch = Pitch(pitch_type="statsbomb", line_zorder=2)

    pitch.draw(ax=ax)

    for idx, row in filtered_data.iterrows():
        if not isinstance(row["pass_outcome"], float):
            color = "red"
            width = 0.5
        elif not isinstance(row["pass_shot_assist"], float):
            color = "silver"
            width = 1
        elif not isinstance(row["pass_goal_assist"], float):
            color = "gold"
            width = 2
        else:
            color = "blue"
            width = 0.5
        pitch.arrows(
            row["location"][0],
            row["location"][1],
            row["pass_end_location"][0],
            row["pass_end_location"][1],
            ax=ax,
            width=width,
            headwidth=5,
            color=color,
            zorder=3,
            alpha=0.7,
        )
    return fig


def create_high_of_center_analysis(df, team):
    if len(df[df.team == team]) == 0:
        return None, None, None

    # Create the figure
    fig, ax = plt.subplots(figsize=(10, 6), tight_layout=True)

    # Initialize the pitch
    pitch = Pitch(pitch_type="statsbomb", line_zorder=2)

    # Create the pitch plot
    pitch.draw(ax=ax)

    # Calculate the average y-coordinate
    average_coord = sum(df[df.team == team].x) / len(df[df.team == team].x)
    average_tot = sum(df.x) / len(df.x)

    # Draw horizontal line through the middle of the points
    ax.vlines(
        x=average_coord,
        ymin=0,
        ymax=pitch.dim.bottom,
        color="blue",
        linestyle="-",
        linewidth=3,
        alpha=0.6,
    )
    ax.vlines(
        x=average_tot,
        ymin=0,
        ymax=pitch.dim.bottom,
        color="black",
        linestyle="--",
        linewidth=1,
        alpha=0.6,
    )
    pitch.scatter(
        114, 34, s=300, color="white", edgecolors="black", zorder=3, ax=ax
    )  # noqa: E501
    # Plot the points
    pitch.scatter(
        df[df.team == team].x,
        df[df.team == team].y,
        s=150,
        color="red",
        edgecolors="black",
        zorder=3,
        ax=ax,
    )

    return fig, average_coord, average_tot


@st.cache_data
def run_code():
    data = Data()
    df_raw = data.get_data()
    p = Preprocessing()
    df_preprocessed = p.run_preprocessing(df_raw)
    kpis = KPIs()
    (
        df_kpis,
        df_iv_position_at_opponent_goal_kick,
        df_goals_xg,
        df_assists_to_xg,
        df_passed_opponents,
    ) = kpis.run_kpis(df_preprocessed)
    return (
        df_kpis,
        df_iv_position_at_opponent_goal_kick,
        df_goals_xg,
        df_assists_to_xg,
        df_preprocessed,
        df_passed_opponents,
    )  # noqa: E501


(
    df_kpis,
    df_iv_position_at_opponent_goal_kick,
    df_goals_xg,
    df_assists_to_xg,
    df_preprocessed,
    df_passed_opponents,
) = run_code()


st.title("Team Statistics Dashboard")

# Select team
selected_team = st.selectbox(
    "Select a team", df_kpis.index.get_level_values(1).unique()
)

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

st.write("Goals scored by player and their expected goals.")
st.write(
    df_goals_xg[df_goals_xg.index.get_level_values("team") == selected_team]
)  # noqa: E501

st.write("Players with assist to expected goals.")
st.write(
    df_assists_to_xg[
        df_assists_to_xg.index.get_level_values("team") == selected_team
    ]  # noqa: E501
)

opponent_filter = st.selectbox(
    "Select Match ID",
    np.append(
        df_preprocessed[df_preprocessed["team"] == selected_team][
            "opponent"
        ].unique(),  # noqa: E501
        np.array(["all"]),
    ),
)
if opponent_filter != "all":
    player_filter = st.selectbox(
        "Select Player",
        np.append(
            df_preprocessed[
                (df_preprocessed["team"] == selected_team)
                & (df_preprocessed["opponent"] == opponent_filter)
            ]["player"].unique(),
            np.array(["all"]),
        ),
    )
else:
    player_filter = st.selectbox(
        "Select Player",
        np.append(
            df_preprocessed[(df_preprocessed["team"] == selected_team)][
                "player"
            ].unique(),
            np.array(["all"]),
        ),
    )
filtered_data = df_preprocessed[(df_preprocessed["team"] == selected_team)]
if opponent_filter != "all":
    filtered_data = filtered_data[
        (filtered_data["opponent"] == opponent_filter)
    ]  # noqa: E501
if player_filter != "all":
    filtered_data = filtered_data[(filtered_data["player"] == player_filter)]
filtered_data = filtered_data[
    [
        "location",
        "pass_end_location",
        "team",
        "match_id",
        "player",
        "pass_outcome",
        "pass_goal_assist",
        "pass_shot_assist",
    ]
].dropna(subset=["location", "pass_end_location"])

st.write(
    f"All passes of {player_filter} in  the match vs {opponent_filter}. "
    + "Complete passes are blue, incomplete passes are red. "
    + "Assists to shots are silver and assists to goals are golden."  # noqa: E501
)
fig = create_pass_analysis(filtered_data)
st.pyplot(fig)
st.write("List of players with passed opponents by passing.")
st.write(
    df_passed_opponents[
        df_passed_opponents.index.get_level_values("team") == selected_team
    ]
)

fig, average_coord, average_tot = create_high_of_center_analysis(
    df=df_iv_position_at_opponent_goal_kick, team=selected_team
)
st.write(
    f"Events of the centers after opponent goal kick (within {conf.goal_kick_tolerance}s)"  # noqa: E501
)
if fig:
    st.pyplot(fig)
    st.write(
        f"The averge distance from the own goal for {selected_team} is {np.round(average_coord,1)} yards. \n The tournament average is the dashed black line ({np.round(average_tot,1)} yards)."  # noqa: E501
    )
else:
    st.write(f"No events found for {selected_team}.")
