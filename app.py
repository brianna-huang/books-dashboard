from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from config import NOTION_TOKEN, DATABASE_ID
from data.notion_source import fetch_books
from data.covers import get_cover_url

# ============================================================
# APP
# ============================================================

st.set_page_config(page_title="Friends Books Dashboard", layout="wide")
st.title("Bri & Friends Books Dashboard")

if NOTION_TOKEN.startswith("PASTE") or DATABASE_ID.startswith("PASTE"):
    st.error(
        "Set NOTION_TOKEN and NOTION_DATABASE_ID as environment variables, "
        "or paste them into config.py."
    )
    st.stop()

df = fetch_books()

if df.empty:
    st.warning("No entries found. Check that your integration has access to the database.")
    st.stop()

# ---- Sidebar filters ----
st.sidebar.header("Filters")
 
reviewers = sorted(df["reviewer"].dropna().unique().tolist())
selected_reviewer = st.sidebar.selectbox("Reader", ["Everyone"] + reviewers)
filtered_df = df.copy() if selected_reviewer == "Everyone" else df[df["reviewer"] == selected_reviewer]
 
st.subheader(f"📚 Showing: {selected_reviewer}" if selected_reviewer == "Everyone" else f"📚 Showing: {selected_reviewer}'s books")
 
selected_genres = []
if filtered_df["genre"].notna().any():
    all_genres = sorted(
        {g.strip() for genres in filtered_df["genre"].dropna() for g in genres.split(",")}
    )
    selected_genres = st.sidebar.multiselect("Genre", all_genres)
    if selected_genres:
        filtered_df = filtered_df[
            filtered_df["genre"].apply(
                lambda g: isinstance(g, str) and any(sel in g for sel in selected_genres)
            )
        ]
 
st.divider()

# ---- Stats row ----
col1, col2, col3 = st.columns(3)

this_year = datetime.now().year
books_this_year = filtered_df[filtered_df["date"].dt.year == this_year].shape[0]
col1.metric(f"Books read in {this_year}", books_this_year)

if filtered_df["author"].notna().any():
    top_author = filtered_df["author"].value_counts().idxmax()
    top_author_count = filtered_df["author"].value_counts().max()
    col2.metric("Most-read author", f"{top_author} ({top_author_count})")
else:
    col2.metric("Most-read author", "—")

col3.metric("Total entries", filtered_df.shape[0])

st.divider()

if selected_reviewer == "Everyone":
    # ---- Reader of the month (previous calendar month) ----
    now = datetime.now()
    first_of_this_month = now.replace(day=1)
    last_month_end = first_of_this_month - pd.Timedelta(days=1)
    target_year, target_month = last_month_end.year, last_month_end.month
    target_month_name = last_month_end.strftime("%B")
    
    st.subheader(f"🥇 Reader of the month ({target_month_name})")
    last_month_df = filtered_df[
        (filtered_df["date"].dt.year == target_year) & (filtered_df["date"].dt.month == target_month)
    ]
    if not last_month_df.empty and last_month_df["reviewer"].notna().any():
        counts = last_month_df["reviewer"].value_counts()
        top_reader = counts.idxmax()
        top_count = counts.max()
        st.success(
            f"**{top_reader}** — {top_count} book{'s' if top_count != 1 else ''} "
            f"reviewed in {target_month_name}! 🎉"
        )
    
        top_reader_books = last_month_df[last_month_df["reviewer"] == top_reader]
        cols = st.columns(len(top_reader_books))
        for col, (_, row) in zip(cols, top_reader_books.iterrows()):
            with col:
                cover_url = get_cover_url(row["title"], row["author"])
                if cover_url:
                    st.image(cover_url, width=140)
                else:
                    st.write("📕")  # placeholder if no cover found
                st.write(f"**{row['title'].strip()}**")
                st.caption(row["author"])
    else:
        st.write(f"No entries from {target_month_name}.")
    
    st.divider()

    # ---- Top 5 most read books (with covers) ----
    st.subheader("📚 Top 5 Most Read Books")
    most_read_df = filtered_df.dropna(subset=["title"]).copy()
    most_read_df["title_key"] = most_read_df["title"].str.strip().str.lower()
 
    most_read_books = (
        most_read_df.groupby("title_key", as_index=False)
        .agg(
            title=("title", "first"),
            author=("author", "first"),
            num_reads=("title", "count"),
            avg_rating=("rating", "mean"),
        )
        .sort_values("num_reads", ascending=False)
        .head(5)
    )
 
    if most_read_books.empty:
        st.write("No entries yet.")
    else:
        cols = st.columns(len(most_read_books))
        for col, (_, row) in zip(cols, most_read_books.iterrows()):
            with col:
                cover_url = get_cover_url(row["title"], row["author"])
                if cover_url:
                    st.image(cover_url, width=140)
                else:
                    st.write("📕")  # placeholder if no cover found
                st.write(f"**{row['title'].strip()}**")
                st.caption(row["author"])
                st.write(f"👥 read by {int(row['num_reads'])} {'people' if row['num_reads'] != 1 else 'person'}")
                if pd.notna(row["avg_rating"]):
                    st.write(f"⭐ {row['avg_rating']:.1f} avg")
 
    st.divider()

# ---- Top 5 rated books (with covers) ----
st.subheader("🏆 Top 5 Rated Books")
rated_df = filtered_df.dropna(subset=["rating"]).copy()
rated_df["title_key"] = rated_df["title"].str.strip().str.lower()

top_books = (
    rated_df.groupby("title_key", as_index=False)
    .agg(
        title=("title", "first"),
        author=("author", "first"),
        avg_rating=("rating", "mean"),
        num_ratings=("rating", "count"),
    )
    .sort_values("avg_rating", ascending=False)
    .head(5)
)

if top_books.empty:
    st.write("No ratings yet.")
else:
    cols = st.columns(len(top_books))
    for col, (_, row) in zip(cols, top_books.iterrows()):
        with col:
            cover_url = get_cover_url(row["title"], row["author"])
            if cover_url:
                st.image(cover_url, width=140)
            else:
                st.write("📕")  # placeholder if no cover found
            st.write(f"**{row['title'].strip()}**")
            st.caption(row["author"])
            st.write(
                f"⭐ {row['avg_rating']:.1f} "
                f"({int(row['num_ratings'])} rating{'s' if row['num_ratings'] != 1 else ''})"
            )

st.divider()

# ---- Currently reading ----
st.subheader("📖 Current Reads")
current_df = filtered_df[filtered_df["status"].str.contains("current", case=False, na=False)]
if not current_df.empty:
    cols = st.columns(len(current_df))
    for col, (_, row) in zip(cols, current_df.iterrows()):
        with col:
            st.write(f"{row['reviewer']} is reading:")
            cover_url = get_cover_url(row["title"], row["author"])
            if cover_url:
                st.image(cover_url, width=140)
            else:
                st.write("📕")  # placeholder if no cover found
            st.write(f"**{row['title'].strip()}**")
            st.caption(row["author"])
else:
    st.write("No one's currently reading anything logged yet.")

st.divider()

# ---- Genre breakdown ----
if not selected_genres:
    st.subheader("🎭 Genre breakdown")
    if filtered_df["genre"].notna().any():
        genre_series = (
            filtered_df["genre"].dropna().str.split(",").explode().str.strip()
        )
        genre_counts = genre_series.value_counts().reset_index()
        genre_counts.columns = ["genre", "count"]
        fig_genre = px.pie(genre_counts, names="genre", values="count")
        st.plotly_chart(fig_genre, use_container_width=True)
    else:
        st.write("No genre data yet.")

# ---- Rating distribution ----
st.subheader("⭐ Rating Distribution")
if filtered_df["rating"].notna().any():
    fig_rating = px.histogram(
        filtered_df.dropna(subset=["rating"]), x="rating", nbins=10
    )
    fig_rating.update_layout(bargap=0.1)
    st.plotly_chart(fig_rating, use_container_width=True)
else:
    st.write("No ratings yet.")

# ---- Books read over time ----
st.subheader("📈 Reading Pace Over Time")
finished_df = filtered_df.dropna(subset=["date"])
if not finished_df.empty:
    monthly = (
        finished_df.set_index("date")
        .resample("MS")
        .size()
        .reset_index(name="books")
    )
    fig_trend = px.line(monthly, x="date", y="books", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.write("No date data yet.")

st.divider()

# ---- Fun stat: longest review (COMMENTED OUT FOR NOW) ---- 
# if filtered_df["review"].notna().any():
#     st.subheader("📝 Longest review award")
#     st.write("Tell us how you really feel...")
#     longest = filtered_df.loc[filtered_df["review"].str.len().idxmax()]
#     st.write(
#         f"**{longest['reviewer']}** on "
#         f"*{longest['title']}* ({len(longest['review'])} characters)"
#     )
#     cover_url = get_cover_url(longest["title"], longest["author"])
#     if cover_url:
#         st.image(cover_url, width=140)
#     else:
#         st.write("📕")  # placeholder if no cover found

#     preview_length = 280
#     review_text = longest["review"]
#     if len(review_text) > preview_length:
#         st.write(review_text[:preview_length].rstrip() + "...")
#         with st.expander("Read full review"):
#             st.write(review_text)
#     else:
#         st.write(review_text)

# st.divider()

# ---- Full table (COMMENTED OUT FOR NOW) ----
# st.subheader("All Entries")
# st.dataframe(
#     filtered_df.sort_values("date", ascending=False),
#     use_container_width=True,
#     hide_index=True,
# )