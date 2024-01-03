from opponent_analysis.config import Config
import pandas as pd
from statsbombpy import sb
import streamlit as st


class Data:
    def __init__(
        self,
    ):
        self.conf = Config()

    @st.cache_data
    def get_match_id(_self):

        competitions = sb.competitions()
        womens_euro_competition = competitions[
            competitions["competition_name"] == _self.conf.competition_name
        ]
        womens_euro_2022 = womens_euro_competition[
            womens_euro_competition["season_name"] == _self.conf.season_name
        ]
        euro_competition_id = womens_euro_2022.competition_id.unique()[0]
        euro_season_id = womens_euro_2022.season_id.unique()[0]
        match_ids = sb.matches(
            competition_id=euro_competition_id, season_id=euro_season_id
        ).match_id
        return match_ids

    @st.cache_data
    def load_statsbomb_data(_self, match_ids):
        event_data_tot = pd.DataFrame()
        for match_id in match_ids:
            event_data = sb.events(match_id=match_id)
            df_360 = pd.read_json(
                f"/Users/borgwardt/Documents/repos/open-data/data/three-sixty/{match_id}.json"  # noqa: E501
            )
            df_merged = pd.merge(
                event_data,
                df_360,
                how="left",
                left_on="id",
                right_on="event_uuid",  # noqa: E501
            )
            event_data_tot = pd.concat(
                [event_data_tot, df_merged], ignore_index=True
            )  # noqa: E501
        return event_data_tot

    @st.cache_data
    def get_data(_self):
        match_ids = _self.get_match_id()
        event_data_tot = _self.load_statsbomb_data(match_ids)
        return event_data_tot
