from opponent_analysis.config import Config
import pandas as pd


class KPIs:
    def __init__(
        self,
    ):
        self.conf = Config()

    def create_kpis(self, df_match):
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
            ].shape[0]

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
                    & (team_events["pass_outcome"].isnull())
                ]
            )
            pass_accuracy = (completed_passes / passes) * 100

            # Total interceptions
            interceptions = len(
                team_events[team_events["type"] == "Interception"]
            )  # noqa: E501

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
                        / (
                            other_team_possession_seconds
                            + team_possession_seconds  # noqa: E501
                        )
                    ],
                },
                index=[team],
            )
            kpi_summary = pd.concat(
                [kpi_summary, kpi_summary_temp], ignore_index=False
            )  # noqa: E501
        return kpi_summary

    def run_kpis(self, df_preprocessed):
        df_kpis = df_preprocessed.groupby(["match_id"]).apply(self.create_kpis)
        return df_kpis
