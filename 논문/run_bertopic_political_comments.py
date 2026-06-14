from __future__ import annotations

import pandas as pd
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP


INPUT_PATH = "political_comments_strict_vader.csv"


CUSTOM_STOP_WORDS = [
    "url", "https", "http", "www", "com",
    "reddit", "subreddit", "subreddits", "findareddit", "signpost",
    "post", "posts", "comment", "comments", "thread",
    "mod", "mods", "moderator", "moderators",
    "bot", "automod", "automoderator",
    "removed", "deleted",
    "korea", "korean", "koreans",
    "people", "person", "someone", "everyone",
    "just", "like", "really", "think", "know",
    "don", "doesn", "didn", "isn", "aren", "wasn", "weren",
    "can", "could", "would", "should",
    "get", "got", "getting",
    "one", "also", "much", "many", "even", "still",
    "make", "made", "way", "thing", "things",
    "going", "said", "say", "says",
    "see", "look", "looks", "want", "need",
    "time", "day", "year", "years",
    "good", "bad", "right", "left",
    "automatically", "communities", "answered", "links",
    "finding", "faq", "performed", "review",
]


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    print("input_shape", df.shape)
    print("year_counts")
    print(df["year"].value_counts().sort_index().to_string())

    df["text_for_topic"] = df["text_clean"].fillna("").astype(str)
    df = df[df["text_for_topic"].str.len() >= 20].copy()
    print("topic_input_shape", df.shape)
    print("topic_year_counts")
    print(df["year"].value_counts().sort_index().to_string())

    vectorizer_model = CountVectorizer(
        stop_words=sorted(set(CUSTOM_STOP_WORDS) | set(ENGLISH_STOP_WORDS)),
        ngram_range=(1, 2),
        min_df=2,
    )
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    umap_model = UMAP(
        n_neighbors=15,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=50,
        min_samples=5,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        language="english",
        calculate_probabilities=False,
        verbose=True,
        min_topic_size=50,
    )

    docs = df["text_for_topic"].tolist()
    topics, _ = topic_model.fit_transform(docs)
    df["bertopic_topic"] = topics

    topic_info = topic_model.get_topic_info()
    topic_year_table = pd.crosstab(df["year"], df["bertopic_topic"])
    topic_year_ratio = pd.crosstab(df["year"], df["bertopic_topic"], normalize="index")

    topic_counts = df["bertopic_topic"].value_counts().reset_index()
    topic_counts.columns = ["topic", "n"]
    major_topics = topic_counts[
        (topic_counts["topic"] != -1) & (topic_counts["n"] >= 100)
    ]["topic"].tolist()

    major_topic_counts = (
        df[df["bertopic_topic"].isin(major_topics)]
        .groupby(["year", "bertopic_topic"])
        .size()
        .reset_index(name="n")
    )
    major_topic_ratio = major_topic_counts.merge(
        df.groupby("year").size().reset_index(name="year_total"),
        on="year",
    )
    major_topic_ratio["ratio"] = major_topic_ratio["n"] / major_topic_ratio["year_total"]

    topic_sentiment = (
        df[df["bertopic_topic"].isin(major_topics)]
        .groupby(["year", "bertopic_topic"])
        .agg(
            n=("vader_compound", "size"),
            mean_compound=("vader_compound", "mean"),
            negative_ratio=("sentiment_label", lambda x: (x == "negative").mean()),
            positive_ratio=("sentiment_label", lambda x: (x == "positive").mean()),
        )
        .reset_index()
    )

    topic_labels = []
    for topic_id in topic_info["Topic"]:
        if topic_id == -1:
            label = "outlier"
            words = ""
        else:
            words_list = topic_model.get_topic(topic_id)
            words = ", ".join([word for word, _ in words_list[:10]])
            label = ""
        topic_labels.append(
            {
                "topic": topic_id,
                "count": int(topic_info.loc[topic_info["Topic"] == topic_id, "Count"].iloc[0]),
                "top_words": words,
                "manual_label": label,
            }
        )
    topic_label_table = pd.DataFrame(topic_labels)

    df.to_csv("political_comments_strict_vader_bertopic.csv", index=False, encoding="utf-8-sig")
    topic_info.to_csv("bertopic_topic_info.csv", index=False, encoding="utf-8-sig")
    topic_year_table.to_csv("bertopic_topic_year_counts.csv", encoding="utf-8-sig")
    topic_year_ratio.to_csv("bertopic_topic_year_ratio.csv", encoding="utf-8-sig")
    topic_sentiment.to_csv("bertopic_topic_sentiment.csv", index=False, encoding="utf-8-sig")
    topic_label_table.to_csv("bertopic_topic_labels_for_manual_edit.csv", index=False, encoding="utf-8-sig")

    print("\n=== topic_info.head(30) ===")
    print(topic_info.head(30).to_string(index=False))
    print("\n=== topic_label_table.head(30) ===")
    print(topic_label_table.head(30).to_string(index=False))
    print("\n=== topic_sentiment ===")
    print(topic_sentiment.to_string(index=False))
    print("\n=== saved_files ===")
    print("political_comments_strict_vader_bertopic.csv")
    print("bertopic_topic_info.csv")
    print("bertopic_topic_year_counts.csv")
    print("bertopic_topic_year_ratio.csv")
    print("bertopic_topic_sentiment.csv")
    print("bertopic_topic_labels_for_manual_edit.csv")


if __name__ == "__main__":
    main()
