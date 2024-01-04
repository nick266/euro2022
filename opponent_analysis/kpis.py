from opponent_analysis.config import Config
import pandas as pd


class KPIs:
    def __init__(
        self,
    ):
        self.conf = Config()

    def get_time_delta_from_opponent_goal_kick(self, df_preprocessed):
        # Create a boolean mask to identify rows where the value switches to
        # "From Goal Kick"
        mask = (
            df_preprocessed["play_pattern"].shift(1) != "From Goal Kick"
        ) & (  # noqa: E501
            df_preprocessed["play_pattern"] == "From Goal Kick"
        )

        # Get the rows where the mask is True
        result = df_preprocessed[mask]
        df_goal_kick = pd.DataFrame(
            data={
                "event_time": result.minute.values * 60 + result.second.values,
                "opponent": result.team.values,
                "match_id": result.match_id.values,
                "goal_kick_time": result.minute.values * 60
                + result.second.values,  # noqa: E501
            },
            index=result.timestamp.index,
        ).sort_values(["event_time"])
        df_preprocessed.sort_values("event_time", inplace=True)
        df_preprocessed = pd.merge_asof(
            df_preprocessed,
            df_goal_kick,
            on="event_time",
            by=["match_id", "opponent"],
            direction="backward",
        )
        df_preprocessed["delta_goal_kick"] = (
            df_preprocessed["event_time"] - df_preprocessed["goal_kick_time"]
        )
        return df_preprocessed

    def get_center_events_after_opponent_goal_kick(
        self, df_preprocessed, tolerance
    ):  # noqa: E501
        mask = df_preprocessed.apply(
            lambda row: row["player_id"] in row["center_id"], axis=1
        )

        # Get the rows where the mask is True
        df_delta_goal_kick = df_preprocessed[mask][
            ["center_id", "player_id", "location", "delta_goal_kick", "team"]
        ]
        df_result = df_delta_goal_kick[
            df_delta_goal_kick["delta_goal_kick"] < tolerance
        ]
        df_temp = df_result["location"].apply(pd.Series)
        df_temp.columns = ["x", "y"]
        df = pd.concat([df_result, df_temp], axis=1)
        return df

    def get_goals_xg(self, df):
        df_xg = df.groupby(["team", "player"]).shot_statsbomb_xg.sum()
        df_goals = (
            df[df.shot_outcome == "Goal"]
            .groupby(["team", "player"])["shot_outcome"]
            .count()
        )
        df_merged = pd.merge(
            df_xg, df_goals, left_index=True, right_index=True, how="left"
        )
        df_result = df_merged.sort_values(
            ["team", "shot_outcome", "shot_statsbomb_xg"], ascending=False
        )
        df_result.fillna(0, inplace=True)
        return df_result

    def get_assists_to_xg(self, df):
        df_temp = df[["pass_assisted_shot_id", "player"]]
        df_temp.columns = ["id_for_merge", "player_assisted"]
        df_merged = pd.merge(
            df, df_temp, left_on="id", right_on="id_for_merge", how="left"
        )
        df_result = (
            df_merged[["team", "shot_statsbomb_xg", "player_assisted"]]
            .groupby(["team", "player_assisted"])
            .sum()
        )
        return df_result.sort_values(
            ["team", "shot_statsbomb_xg"], ascending=False
        )  # noqa: E501

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

        df_time_delta = self.get_time_delta_from_opponent_goal_kick(
            df_preprocessed
        )  # noqa: E501
        df_iv_position_at_opponent_goal_kick = (
            self.get_center_events_after_opponent_goal_kick(
                df_time_delta, self.conf.goal_kick_tolerance
            )
        )
        df_kpis = df_preprocessed.groupby(["match_id"]).apply(self.create_kpis)
        df_goals_xg = self.get_goals_xg(df_preprocessed)
        df_assists_to_xg = self.get_assists_to_xg(df_preprocessed)
        return (
            df_kpis,
            df_iv_position_at_opponent_goal_kick,
            df_goals_xg,
            df_assists_to_xg,
        )
