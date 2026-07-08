import os
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file in the same directory and loads them into os.environ

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "PASTE_YOUR_TOKEN_HERE")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "PASTE_YOUR_DATABASE_ID_HERE")

# Map each field we need to the exact property name in your Notion database.
# Open your database in Notion and check the column headers if unsure.
PROPERTY_MAP = {
    "title": "Title",         # Title-type property (the book name)
    "author": "Author",       # Text or Select property
    "rating": "Rating / 10",  # Number property
    "reviewer": "Reviewer",   # Person, Select, or Text property (who added/reviewed it)
    "date": "Date",           # Date property
    "genre": "Genre",         # Select or Multi-select property
    "status": "Status",       # Select property (e.g. To Read / Current Read / Finished)
    "review": "Review",       # Text property (the written review)
}

# Your name as it appears in the "reviewer" property, so the "just me" filter works
MY_NAME = "bri"

GOOGLE_BOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")