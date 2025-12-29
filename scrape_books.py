import re
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"


RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def _get_soup(url: str) -> BeautifulSoup:
    """Download a page and return a BeautifulSoup object."""
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def _parse_price(text: str) -> float:
    """Convert '£51.77' -> 51.77"""
    # keep digits and dot
    clean = re.sub(r"[^0-9.]", "", text)
    return float(clean) if clean else float("nan")


def _parse_rating_from_classes(tag) -> int:
    """
    In book page/listing: <p class="star-rating Three"> ...
    We take the second class as the rating word.
    """
    classes = tag.get("class", [])
    rating_word = next((c for c in classes if c in RATING_MAP), None)
    return RATING_MAP.get(rating_word, None)


def _extract_detail_fields(book_url: str) -> dict:
    """
    Visit book detail page and extract:
    UPC, Genre (category), Availability, Description.
    """
    soup = _get_soup(book_url)

    # UPC is in the product information table
    upc = None
    table = soup.select_one("table.table.table-striped")
    if table:
        for row in table.select("tr"):
            th = row.select_one("th")
            td = row.select_one("td")
            if th and td and th.get_text(strip=True) == "UPC":
                upc = td.get_text(strip=True)
                break

    # Genre: breadcrumb usually: Home > Books > Category > Book Title
    genre = None
    breadcrumb_items = soup.select("ul.breadcrumb li a")
    # Example: [Home, Books, Travel]
    if len(breadcrumb_items) >= 3:
        genre = breadcrumb_items[2].get_text(strip=True)

    # Availability
    availability = None
    avail_tag = soup.select_one("p.availability")
    if avail_tag:
        availability = " ".join(avail_tag.get_text(strip=True).split())

    # Description (sometimes missing)
    description = None
    desc_header = soup.find("div", id="product_description")
    if desc_header:
        p = desc_header.find_next_sibling("p")
        if p:
            description = p.get_text(strip=True)

    return {
        "UPC": upc,
        "Genre": genre,
        "Availability": availability,
        "Description": description,
    }


def scrape_books(min_rating: float, max_price: float) -> pd.DataFrame:
    """
    Scrape Books to Scrape and return a DataFrame with:
    UPC, Title, Price (£), Rating, Genre, Availability, Description

    Filters:
      - rating >= min_rating
      - price <= max_price
    """
    results = []

    next_url = urljoin(BASE_URL, "catalogue/page-1.html")

    while next_url:
        soup = _get_soup(next_url)

        # Each book on the page is an article.product_pod
        books = soup.select("article.product_pod")

        for book in books:
            title_tag = book.select_one("h3 a")
            price_tag = book.select_one("p.price_color")
            rating_tag = book.select_one("p.star-rating")

            if not title_tag or not price_tag or not rating_tag:
                continue

            title = title_tag.get("title", "").strip()
            price = _parse_price(price_tag.get_text(strip=True))
            rating = _parse_rating_from_classes(rating_tag)

            # Link to detail page (relative -> absolute)
            rel_link = title_tag.get("href", "")
            book_url = urljoin(next_url, rel_link)

            # Apply filters early (faster)
            if rating is None or price != price:
                continue
            if rating < float(min_rating):
                continue
            if price > float(max_price):
                continue

            detail = _extract_detail_fields(book_url)

            results.append({
                "UPC": detail["UPC"],
                "Title": title,
                "Price (£)": price,
                "Rating": rating,
                "Genre": detail["Genre"],
                "Availability": detail["Availability"],
                "Description": detail["Description"],
            })

        # Pagination: look for "next" button
        next_li = soup.select_one("li.next a")
        if next_li and next_li.get("href"):
            # next link is relative to current page location
            next_url = urljoin(next_url, next_li["href"])
        else:
            next_url = None

    return pd.DataFrame(results)


if __name__ == "__main__":
    # Test run:
    df = scrape_books(min_rating=4.0, max_price=20)
    print(df.head(10))
    print(f"\nTotal books returned: {len(df)}")

    # Save results
    df.to_csv("books_scraped.csv", index=False)
    print("\nSaved to books_scraped.csv")
