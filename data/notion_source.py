import pandas as pd
import streamlit as st
from notion_client import Client

from config import NOTION_TOKEN, DATABASE_ID, PROPERTY_MAP


def format_author_name(name):
    """Convert 'Last, First' -> 'First Last' for display. Leaves other formats alone."""
    if not isinstance(name, str) or "," not in name:
        return name
    parts = [p.strip() for p in name.split(",", 1)]
    if len(parts) == 2 and parts[0] and parts[1]:
        return f"{parts[1]} {parts[0]}"
    return name


@st.cache_data(ttl=600)  # cache for 10 minutes so we're not hitting the API on every interaction
def fetch_books():
    """Pull every row from the configured Notion database and return it as a tidy DataFrame."""
    client = Client(auth=NOTION_TOKEN)
    db = client.databases.retrieve(database_id=DATABASE_ID)
    data_source_id = db["data_sources"][0]["id"]

    rows = []
    cursor = None

    while True:
        response = client.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=cursor,
        )
        rows.extend(response["results"])
        cursor = response.get("next_cursor")
        if not cursor:
            break

    records = [_parse_row(row["properties"]) for row in rows]

    df = pd.DataFrame(records)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["author"] = df["author"].apply(format_author_name)
        df["title"] = df["title"].str.strip()
    return df


def _parse_row(props):
    """Extract one normalized book record from a Notion page's raw `properties` payload."""
    record = {}

    # Title (title-type property)
    title_prop = props.get(PROPERTY_MAP["title"], {})
    title_items = title_prop.get("title", [])
    record["title"] = title_items[0]["plain_text"] if title_items else None

    # Author (handles rich_text or select)
    author_prop = props.get(PROPERTY_MAP["author"], {})
    if "rich_text" in author_prop:
        texts = author_prop["rich_text"]
        record["author"] = texts[0]["plain_text"] if texts else None
    elif "select" in author_prop:
        record["author"] = author_prop["select"]["name"] if author_prop["select"] else None
    else:
        record["author"] = None

    # Rating (number)
    rating_prop = props.get(PROPERTY_MAP["rating"], {})
    record["rating"] = rating_prop.get("number")

    # Reviewer (handles people, select, or rich_text)
    reviewer_prop = props.get(PROPERTY_MAP["reviewer"], {})
    if "people" in reviewer_prop:
        people = reviewer_prop["people"]
        record["reviewer"] = people[0]["name"] if people else None
    elif "select" in reviewer_prop:
        record["reviewer"] = reviewer_prop["select"]["name"] if reviewer_prop["select"] else None
    elif "rich_text" in reviewer_prop:
        texts = reviewer_prop["rich_text"]
        record["reviewer"] = texts[0]["plain_text"] if texts else None
    else:
        record["reviewer"] = None

    # Date
    date_prop = props.get(PROPERTY_MAP["date"], {})
    date_obj = date_prop.get("date")
    record["date"] = date_obj["start"] if date_obj else None

    # Genre (handles select or multi_select)
    genre_prop = props.get(PROPERTY_MAP["genre"], {})
    if "multi_select" in genre_prop:
        options = genre_prop["multi_select"]
        record["genre"] = ", ".join(o["name"] for o in options) if options else None
    elif "select" in genre_prop:
        record["genre"] = genre_prop["select"]["name"] if genre_prop["select"] else None
    else:
        record["genre"] = None

    # Status (Notion's dedicated "status" property type, distinct from "select")
    status_prop = props.get(PROPERTY_MAP["status"], {})
    if "status" in status_prop:
        record["status"] = status_prop["status"]["name"] if status_prop["status"] else None
    elif "select" in status_prop:
        record["status"] = status_prop["select"]["name"] if status_prop["select"] else None
    else:
        record["status"] = None

    # Review (rich_text)
    review_prop = props.get(PROPERTY_MAP["review"], {})
    review_texts = review_prop.get("rich_text", [])
    record["review"] = "".join(t["plain_text"] for t in review_texts) if review_texts else None

    return record