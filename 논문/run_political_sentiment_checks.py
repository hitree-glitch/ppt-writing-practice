from __future__ import annotations

from pathlib import Path

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


INPUT_PATH = Path(
    r"C:\Users\user\OneDrive\D 대학원 박사\A 아주대\2. 사회심리학과 빅데이터 (박현준)"
    r"\데이터\Reddit 탄핵 이후\data_clean\political_comments_strict.csv"
)


def sentiment_label(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    analyzer = SentimentIntensityAnalyzer()

    text_col = "text_clean"
    df[text_col] = df[text_col].fillna("").astype(str)

    scores = df[text_col].apply(analyzer.polarity_scores)
    df["vader_neg"] = scores.apply(lambda x: x["neg"])
    df["vader_neu"] = scores.apply(lambda x: x["neu"])
    df["vader_pos"] = scores.apply(lambda x: x["pos"])
    df["vader_compound"] = scores.apply(lambda x: x["compound"])
    df["sentiment_label"] = df["vader_compound"].apply(sentiment_label)

    summary = (
        df.groupby("year")
        .agg(
            n=("vader_compound", "size"),
            mean_compound=("vader_compound", "mean"),
            median_compound=("vader_compound", "median"),
            sd_compound=("vader_compound", "std"),
            positive_ratio=("sentiment_label", lambda s: (s == "positive").mean()),
            neutral_ratio=("sentiment_label", lambda s: (s == "neutral").mean()),
            negative_ratio=("sentiment_label", lambda s: (s == "negative").mean()),
        )
        .reset_index()
    )
    summary.to_csv("vader_sentiment_summary_strict.csv", index=False, encoding="utf-8-sig")

    sentiment_table = pd.crosstab(df["year"], df["sentiment_label"])
    sentiment_table.to_csv("vader_sentiment_table_strict.csv", encoding="utf-8-sig")
    df.to_csv("political_comments_strict_vader.csv", index=False, encoding="utf-8-sig")

    print("sentiment_summary")
    print(summary.to_string(index=False))
    print()
    print("sentiment_label_counts")
    print(df["sentiment_label"].value_counts().to_string())
    print()
    print("sentiment_table")
    print(sentiment_table.to_string())
    print()
    print("political_comments_strict_vader.csv")
    print("vader_sentiment_summary_strict.csv")
    print("vader_sentiment_table_strict.csv")


if __name__ == "__main__":
    main()
