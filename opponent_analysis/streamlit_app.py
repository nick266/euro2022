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
    ) = kpis.run_kpis(df_preprocessed)
    return (
        df_kpis,
        df_iv_position_at_opponent_goal_kick,
        df_goals_xg,
        df_assists_to_xg,
    )  # noqa: E501


(
    df_kpis,
    df_iv_position_at_opponent_goal_kick,
    df_goals_xg,
    df_assists_to_xg,
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
#  to do:
#  caching (check)
#  colors for dashboard (check)
#  possession in percentag (check)
#  defender distance (check)
#  filter for dates
#  average position (cant do)
#  soccer field metric (eg pass direction)
#  list of players with xgoals and xassits (check)
#  unit tests
#  doc strings
#  new metric based on difference in thread of scoring or conceding a goal
#  in after an event
#  hide std, mean and other column
#  one table for goals, xg and assists
