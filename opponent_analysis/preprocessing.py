from opponent_analysis.config import Config
import pandas as pd


class Preprocessing:
    def __init__(
        self,
    ):
        self.conf = Config()

    def get_center_ids(self, event_data_tot):
        center_back = pd.DataFrame()
        for index, row in event_data_tot.iterrows():

            if isinstance(row.tactics, dict):
                player_temp = []
                match_id = row.match_id
                team = row.team
                index = row["index"]
                for player in row.tactics["lineup"]:
                    if 2 < player["position"]["id"] < 6:
                        player_temp.append(player["player"]["id"])
                center_back_temp = pd.DataFrame(
                    {
                        "match_id": [match_id],
                        "team": [team],
                        "index": [index],
                        "center_id": [player_temp],
                    }
                )
                center_back = pd.concat([center_back, center_back_temp])
        df_center = pd.merge(
            event_data_tot,
            center_back,
            how="left",
            on=["match_id", "index", "team"],  # noqa: E501
        ).sort_values(["match_id", "team", "index"])
        df_center["center_id"].ffill(inplace=True)
        return df_center

    def add_oppnent_team(self, df_preprocessed):
        grouped_teams = df_preprocessed.groupby("match_id").team.unique()
        teams_df_1 = grouped_teams.apply(pd.Series)

        # Rename the columns
        teams_df_1.columns = ["team_1", "team_2"]

        # Reset the index to have match_id as a column
        teams_df_1.reset_index(inplace=True)
        teams_df_2 = teams_df_1.copy()
        teams_df_2.columns = ["match_id", "team_2", "team_1"]
        df_teams = pd.concat([teams_df_2, teams_df_1])
        df_teams.columns = ["match_id", "team", "opponent"]
        df_preprocessed = df_preprocessed.merge(
            df_teams, how="left", on=["match_id", "team"]
        )
        return df_preprocessed

    def run_preprocessing(self, df_raw):
        df_center = self.get_center_ids(df_raw)
        df_with_opponent = self.add_oppnent_team(df_center)
        df_preprocessed = df_with_opponent.sort_values(["match_id", "index"])
        df_preprocessed["event_time"] = (
            df_preprocessed.minute.values * 60 + df_preprocessed.second.values
        )
        df_preprocessed.reset_index(inplace=True)
        return df_preprocessed
