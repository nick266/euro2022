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

    def run_preprocessing(self, df_raw):
        df_center = self.get_center_ids(df_raw)
        df_preprocessed = df_center.sort_values(
            ["match_id", "minute", "timestamp"]
        )  # noqa: E501
        df_preprocessed.reset_index(inplace=True)
        return df_preprocessed
