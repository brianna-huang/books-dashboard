# Books Dashboard

A Streamlit dashboard for a shared book review Notion database. Shows
reading stats, reader of the month, top rated and most-read books (with
covers pulled from Google Books), currently-reading, genre breakdown, rating
distribution, reading pace over time, and a full sortable table.

## Features

- **Everyone's books / just my books** toggle, plus a genre filter
- **Stats row**: books read this year, most-read author, total entries
- **Reader of the month**: whoever logged the most books last calendar month,
  with covers of what they read (hidden when filtering to just your own books)
- **Top 5 most read books**: ranked by how many people logged them, with
  covers and average rating (also hidden in "just my books" view)
- **Top 5 rated books**: ranked by average rating, with covers
- **Currently reading**: covers for whatever's in progress right now
- **Genre breakdown** (pie chart), **rating distribution** (histogram),
  **reading pace over time** (line chart)
- **Longest review award**, with a "read full review" expander so long
  reviews don't take over the page
- Full entries table

## Project structure

```
books_dashboard/
├── app.py                  # Streamlit UI / dashboard rendering only
├── config.py                # env vars, Notion property mapping, your name
├── requirements.txt
├── .env                      # you need to create this — see below (not committed)
└── data/
    ├── __init__.py
    ├── notion_source.py     # pulls and normalizes rows from Notion
    └── covers.py             # Google Books cover lookup
```

## Prerequisites

- Python 3.9+
- A Notion account with a books database (see the property list below)
- A Notion internal integration token
- (Recommended) a Google Books API key, to avoid rate-limit errors on
  cover lookups

## 1. Set up your Notion database

Your database needs these properties (names are configurable — see step 4):

| Property        | Notion type              | Purpose                         |
|-----------------|---------------------------|----------------------------------|
| Title           | Title                     | Book title                       |
| Author          | Text or Select            | Author name                      |
| Rating / 10     | Number                    | Rating out of 10                 |
| Reviewer        | Person, Select, or Text   | Who logged/read the book         |
| Date            | Date                      | Date finished/logged             |
| Genre           | Select or Multi-select    | Genre(s)                         |
| Status          | Select                    | e.g. "To Read", "Current Read", "Finished" |
| Review          | Text                      | Written review                   |

## 2. Create a Notion integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
   and click **New integration**.
2. Give it a name (e.g. "Books Dashboard"), select your workspace, and create it.
3. Copy the **Internal Integration Token** — you'll need it in step 5.
4. Open your books database in Notion, click the **•••** menu in the top
   right → **Connections** → **Connect to** → select your new integration.
   This is required, or the API will return an empty/403 result.
5. While your database is open, copy its **database ID** from the URL:
   ```
   https://www.notion.so/your-workspace/DATABASE_ID?v=...
   ```
   It's the 32-character string right after your workspace name and before `?v=`.

## 3. Get a Google Books API key (recommended)

Without a key, cover lookups share Google's low rate limit across every
anonymous caller on your network, which can cause `429 Too Many Requests`
errors — you'll often see covers fail to load as a result.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project (or select an existing one).
3. Go to **APIs & Services → Library**, search for **Books API**, and enable it.
4. Go to **APIs & Services → Credentials → Create Credentials → API Key**.
5. Copy the key. No billing account is required for this API.

## 4. Install dependencies

Clone or copy this project, then from inside the `books_dashboard/` folder:

```bash
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 5. Configure your environment

Create a file named `.env` in the `books_dashboard/` folder (same level as `app.py`):

```
NOTION_TOKEN=secret_your_integration_token_here
NOTION_DATABASE_ID=your_database_id_here
GOOGLE_BOOKS_API_KEY=your_google_books_api_key_here
```

`GOOGLE_BOOKS_API_KEY` is optional but strongly recommended (see step 3).

If your Notion property names differ from the defaults, or you want to
change whose entries the "just my books" filter shows, edit `config.py`:

```python
PROPERTY_MAP = {
    "title": "Title",
    "author": "Author",
    "rating": "Rating / 10",
    "reviewer": "Reviewer",
    "date": "Date",
    "genre": "Genre",
    "status": "Status",
    "review": "Review",
}

MY_NAME = "bri"  # must match how your name appears in the Reviewer property
```

## 6. Run it

From inside the `books_dashboard/` folder:

```bash
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) — open it
in your browser. Use `Ctrl+C` in the terminal to stop the server.

## 7. Deploy it (so your friends can use it without any setup)
 
The whole point of the reader dropdown is that you can host **one** instance
and everyone just picks their name — friends don't need their own Notion
token, `.env` file, or anything installed. [Streamlit Community
Cloud](https://share.streamlit.io) hosts this for free.
 
1. **Push your repo to GitHub** if you haven't already (make sure `.env` is
   *not* committed — check with `git status`; your `.gitignore` handles this).
2. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in
   with GitHub.
3. Click **"Create app" → "Deploy a public app from GitHub"** and select:
   - **Repository**: your `books-dashboard` repo
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Before deploying, open **"Advanced settings"** and paste your secrets in
   TOML format:
```toml
   NOTION_TOKEN = "secret_your_integration_token_here"
   NOTION_DATABASE_ID = "your_database_id_here"
   GOOGLE_BOOKS_API_KEY = "your_google_books_api_key_here"
```
   Streamlit Cloud exposes these as environment variables at runtime, which
   is exactly what `config.py`'s `os.environ.get(...)` calls already expect —
   no code changes needed.
5. Click **Deploy**. It takes a couple minutes to install dependencies and
   launch, then you'll get a URL like `your-app-name.streamlit.app`.
6. **Restrict access** (recommended, since this shows real names and full
   review text): in the app's settings on Streamlit Cloud, turn off public
   access and invite specific people by email instead. Only invited viewers
   will be able to open the link.
7. Share the link with your friends. They open it, pick their name from the
   **Reader** dropdown, and see their own stats — nothing to configure on
   their end.
 
You can update secrets or re-invite people anytime from the app's settings
page on Streamlit Cloud. Code changes pushed to `main` redeploy automatically.

## Troubleshooting

- **"Set NOTION_TOKEN and NOTION_DATABASE_ID..." error on load** — your
  `.env` file is missing, misnamed, or not in the same folder as `app.py`.
- **"No entries found"** — the integration hasn't been connected to the
  database (see step 2.4), or the database is otherwise empty/inaccessible.
- **Covers not loading / rate limit errors** — add a `GOOGLE_BOOKS_API_KEY`
  (see step 3). Some obscure or self-published titles simply won't have a
  Google Books cover; a 📕 placeholder shows instead.
- **A stat or chart looks empty** — that section requires the underlying
  Notion property to be filled in for at least one row (e.g. no ratings yet
  means no rating distribution).
- Data is cached for 10 minutes and cover lookups for 1 hour, so changes made
  in Notion may take a little while to show up. Refreshing the page doesn't
  bypass the cache — restart the Streamlit server if you need to force one
  right away.