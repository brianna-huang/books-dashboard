import logging
import time

import requests
import streamlit as st

from config import GOOGLE_BOOKS_API_KEY

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
logging.basicConfig(level=logging.WARNING)  # no-op if a handler already exists
logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600, show_spinner=False)
def _search_google_books(query):
    """Low-level call to the Google Books API.

    Returns (items, error). Splitting these apart matters: a `None` result used to
    mean either "no book matched" or "the HTTP request itself failed" (timeout,
    blocked network, rate limit, bad response)- and there was no way to tell which
    from the UI. Now the caller gets the real error string when something goes wrong.

    Retries once on 429 (rate limited), since Google's unauthenticated quota is
    shared across every anonymous caller and can produce occasional transient
    429s even under light use. If GOOGLE_BOOKS_API_KEY is set, requests use that
    key's own quota instead of the shared anonymous pool, which is the real fix.
    """
    params = {"q": query, "maxResults": 1, "country": "US"}
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY

    last_error = None
    for attempt in range(2):  # initial try + 1 retry
        try:
            resp = requests.get(
                GOOGLE_BOOKS_URL,
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (compatible; BooksDashboard/1.0)"},
                timeout=10,
            )
            if resp.status_code == 429:
                last_error = "429 Too Many Requests"
                retry_after = float(resp.headers.get("Retry-After", 1.5))
                if attempt == 0:
                    time.sleep(min(retry_after, 3))
                    continue
                return None, last_error
            resp.raise_for_status()
            return resp.json().get("items"), None
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            break
 
    return None, last_error


def get_cover_url(title, author):
    """Look up a book cover thumbnail via the Google Books API. Returns None if not found."""
    logger.warning("get_cover_url called | title=%r | author=%r", title, author)

    if not title:
        return None

    def _extract_cover(items):
        if not items:
            return None
        image_links = items[0].get("volumeInfo", {}).get("imageLinks", {})
        url = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        return url.replace("http://", "https://") if url else None

    # Build query attempts in order of specificity: full title+author, then a
    # de-parenthesized title (e.g. "(Xenogenesis Book 1)" often hurts matching),
    # then title-only in case author formatting doesn't match Google's records.
    stripped_title = title.split("(")[0].strip()
    queries = [f'intitle:"{title}"' + (f' inauthor:"{author}"' if author else "")]
    if stripped_title and stripped_title != title:
        queries.append(f'intitle:"{stripped_title}"' + (f' inauthor:"{author}"' if author else ""))
    queries.append(f'intitle:"{stripped_title or title}"')
 
    for query in queries:
        items, error = _search_google_books(query)
        if error:
            # If we're being rate limited, further fallback queries will just
            # fail the same way. Stop burning through the limit and bail out.
            if "429" in error:
                break
            continue
        cover = _extract_cover(items)
        if cover:
            return cover
 
    return None