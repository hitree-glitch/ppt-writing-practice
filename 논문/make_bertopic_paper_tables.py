from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency


TOPIC_LABEL_MAP = {
    -1: "outlier",
    0: "international_security_north_china_russia",
    1: "yoon_martial_law_legal_investigation",
    2: "general_reaction_jokes",
    3: "middle_east_conflict_gaza",
    4: "lee_jae_myung_electoral_politics",
    5: "japan_nationalism_historical_politics",
    6: "party_competition_domestic_politics",
    7: "mixed_celebrity_symbolic_politics",
    8: "election_voting_candidates",
    9: "maga_christian_right_protest",
    10: "prison_punishment_mixed",
    11: "courts_trials_judiciary",
    12: "gender_military_service",
    13: "party_local_elections",
    14: "language_identity_politics",
    15: "technology_companies_data",
    16: "translation_english_ai",
    17: "political_fatigue_criticism",
    18: "birthrate_women_rights",
    19: "conservative_liberal_extremism",
    20: "youtube_media_content",
    21: "sejong_capital_city_planning",
    22: "housing_economy_policy",
    23: "democracy_dictatorship_discourse",
    24: "treason_prison_death_penalty",
    25: "diaspora_overseas_korean_identity",
    26: "youth_gender_policy",
    27: "party_history_education_mixed",
    28: "starbucks_corporate_consumption",
}

USE_TOPICS = [0, 1, 3, 4, 5, 8, 11, 12, 14, 22, 23, 25]


def flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out.columns = [
        "_".join(str(part) for part in col if str(part) != "")
        if isinstance(col, tuple)
        else str(col)
        for col in out.columns
    ]
    return out


def main() -> None:
    df = pd.read_csv("political_comments_strict_vader_bertopic.csv")
    topic_info = pd.read_csv("bertopic_topic_info.csv")

    df["topic_label"] = df["bertopic_topic"].map(TOPIC_LABEL_MAP).fillna("other")
    topic_info["manual_label"] = topic_info["Topic"].map(TOPIC_LABEL_MAP).fillna("other")

    df_main_topics = df[df["bertopic_topic"].isin(USE_TOPICS)].copy()

    topic_year_summary = (
        df_main_topics.groupby(["bertopic_topic", "topic_label", "year"])
        .size()
        .reset_index(name="n")
    )
    year_totals = df.groupby("year").size().reset_index(name="year_total")
    topic_year_summary = topic_year_summary.merge(year_totals, on="year")
    topic_year_summary["ratio"] = topic_year_summary["n"] / topic_year_summary["year_total"]

    topic_year_wide = (
        topic_year_summary.pivot_table(
            index=["bertopic_topic", "topic_label"],
            columns="year",
            values=["n", "ratio"],
            fill_value=0,
        )
        .reset_index()
    )
    topic_year_wide = flatten_columns(topic_year_wide)

    topic_chi_table = pd.crosstab(df_main_topics["year"], df_main_topics["bertopic_topic"])
    chi2, p, dof, expected = chi2_contingency(topic_chi_table)
    n_total = int(topic_chi_table.to_numpy().sum())
    r, k = topic_chi_table.shape
    cramers_v = float(np.sqrt(chi2 / (n_total * (min(r, k) - 1))))
    topic_chi_result = pd.DataFrame(
        {
            "chi2": [chi2],
            "df": [dof],
            "p": [p],
            "cramers_v": [cramers_v],
            "n_total": [n_total],
        }
    )

    topic_sentiment_main = (
        df_main_topics.groupby(["year", "bertopic_topic", "topic_label"])
        .agg(
            n=("vader_compound", "size"),
            mean_compound=("vader_compound", "mean"),
            negative_ratio=("sentiment_label", lambda x: (x == "negative").mean()),
            positive_ratio=("sentiment_label", lambda x: (x == "positive").mean()),
        )
        .reset_index()
        .sort_values(["bertopic_topic", "year"])
    )

    topic_ratio_wide = (
        topic_year_summary.pivot_table(
            index=["bertopic_topic", "topic_label"],
            columns="year",
            values=["n", "ratio"],
            fill_value=0,
        )
        .reset_index()
    )
    topic_ratio_wide = flatten_columns(topic_ratio_wide)
    topic_ratio_wide = topic_ratio_wide.rename(
        columns={
            "n_2025": "n_2025",
            "n_2026": "n_2026",
            "ratio_2025": "ratio_2025",
            "ratio_2026": "ratio_2026",
        }
    )
    for col in ["n_2025", "n_2026", "ratio_2025", "ratio_2026"]:
        if col not in topic_ratio_wide.columns:
            topic_ratio_wide[col] = 0

    topic_ratio_wide["n_change"] = topic_ratio_wide["n_2026"] - topic_ratio_wide["n_2025"]
    topic_ratio_wide["ratio_change"] = topic_ratio_wide["ratio_2026"] - topic_ratio_wide["ratio_2025"]

    sentiment_wide = (
        topic_sentiment_main.pivot_table(
            index=["bertopic_topic", "topic_label"],
            columns="year",
            values=["mean_compound", "negative_ratio"],
            fill_value=np.nan,
        )
        .reset_index()
    )
    sentiment_wide = flatten_columns(sentiment_wide)
    sentiment_wide = sentiment_wide.rename(
        columns={
            "mean_compound_2025": "mean_2025",
            "mean_compound_2026": "mean_2026",
            "negative_ratio_2025": "neg_2025",
            "negative_ratio_2026": "neg_2026",
        }
    )
    for col in ["mean_2025", "mean_2026", "neg_2025", "neg_2026"]:
        if col not in sentiment_wide.columns:
            sentiment_wide[col] = np.nan

    sentiment_wide["mean_change"] = sentiment_wide["mean_2026"] - sentiment_wide["mean_2025"]
    sentiment_wide["neg_change"] = sentiment_wide["neg_2026"] - sentiment_wide["neg_2025"]

    topic_change_summary = (
        topic_ratio_wide.merge(
            sentiment_wide,
            on=["bertopic_topic", "topic_label"],
            how="left",
        )
        .sort_values("ratio_change", ascending=False)
        .reset_index(drop=True)
    )

    topic_info.to_csv("bertopic_topic_info_labeled.csv", index=False, encoding="utf-8-sig")
    topic_year_summary.to_csv("bertopic_major_topic_year_summary.csv", index=False, encoding="utf-8-sig")
    topic_year_wide.to_csv("bertopic_major_topic_year_wide.csv", index=False, encoding="utf-8-sig")
    topic_sentiment_main.to_csv("bertopic_major_topic_sentiment.csv", index=False, encoding="utf-8-sig")
    topic_change_summary.to_csv("bertopic_major_topic_change_summary.csv", index=False, encoding="utf-8-sig")
    topic_chi_result.to_csv("bertopic_major_topic_chi_square.csv", index=False, encoding="utf-8-sig")
    df.to_csv("political_comments_strict_vader_bertopic_labeled.csv", index=False, encoding="utf-8-sig")

    print("=== topic_change_summary ===")
    print(topic_change_summary.to_string(index=False))
    print("\n=== topic_chi_result ===")
    print(topic_chi_result.to_string(index=False))
    print("\n=== topic_sentiment_main ===")
    print(topic_sentiment_main.to_string(index=False))
    print("\n=== saved_files ===")
    print("bertopic_topic_info_labeled.csv")
    print("bertopic_major_topic_year_summary.csv")
    print("bertopic_major_topic_year_wide.csv")
    print("bertopic_major_topic_sentiment.csv")
    print("bertopic_major_topic_change_summary.csv")
    print("bertopic_major_topic_chi_square.csv")
    print("political_comments_strict_vader_bertopic_labeled.csv")


if __name__ == "__main__":
    main()
