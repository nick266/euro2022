import pandas as pd
import streamlit as st
from opponent_analysis.preprocessing import Preprocessing
from opponent_analysis.data import Data
from opponent_analysis.kpis import KPIs


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
def run_code():
    data = Data()
    df_raw = data.get_data()
    p = Preprocessing()
    df_preprocessed = p.run_preprocessing(df_raw)
    kpis = KPIs()
    df_kpis = kpis.run_kpis(df_preprocessed)
    return df_kpis


df_kpis = run_code()


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
#  to do:
#  caching (check)
#  colors for dashboard (check)
#  possession in percentag (check)
#  defender distance
#  filter for dates
#  average position
#  soccer field metric (eg pass direction)
#  list of players with xgoals and xassits
#  unit tests
#  doc strings
#  new metric based on difference in thread of scoring or conceding a goal
#  in after an event
# hide std, mean and other column
