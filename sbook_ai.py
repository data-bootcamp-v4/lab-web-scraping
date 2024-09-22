## from AI, to try to understand and implement on a near future. NOT to be evaluated.

import aiohttp
import asyncio
import nest_asyncio
from bs4 import BeautifulSoup
import pandas as pd

nest_asyncio.apply()

async def fetch_page(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_all_pages(base_url, start_page, end_page):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(start_page, end_page + 1):
            url = base_url.format(i)
            tasks.append(fetch_page(session, url))
        return await asyncio.gather(*tasks)

def parse_page(content):
    soup = BeautifulSoup(content, 'html.parser')
    products = soup.find_all("li", class_="col-xs-6")
    book_entries = []

    for prod in products:
        title = prod.find("h3").find("a")["title"]
        price = float(prod.find("p", class_="price_color").get_text().replace("£", ""))
        rating = prod.find("p", class_="star-rating")["class"][1]

        url = "https://books.toscrape.com/catalogue/"
        href = url + prod.find("h3").find("a")["href"]

        book_entries.append({"title": title, "price (£)": price, "rating": rating, "href": href})
    return book_entries

def scrape_books(min_rate, max_price):
    base_url = "https://books.toscrape.com/catalogue/page-{}.html"
    start_page = 1
    end_page = 50  # Adjust based on the total number of pages

    loop = asyncio.get_event_loop()
    pages_content = loop.run_until_complete(fetch_all_pages(base_url, start_page, end_page))

    all_books = []
    
    for page_content in pages_content:
        all_books.extend(parse_page(page_content))

    book_dict = {}
    for k, book in enumerate(all_books, start=1):
        extra_response = requests.get(book["href"])
        extra = BeautifulSoup(extra_response.content, 'html.parser')

        genre = extra.select_one("ul.breadcrumb li:nth-of-type(3) a").get_text()
        availability = extra.find("p", class_="instock availability").get_text(strip=True)
        description = extra.find("meta", attrs={"name": "description"})["content"].strip()
        upc = extra.find("th", string="UPC").find_next_sibling("td").get_text()

        book_dict[k] = {
            "title": book["title"],
            "price (£)": book["price (£)"],
            "rating": book["rating"],
            "genre": genre,
            "availability": availability,
            "description": description,
            "href": book["href"],
            "UPC": upc
        }

    s_book_data = pd.DataFrame.from_dict(book_dict, orient='index')
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    s_book_data["rating"] = s_book_data["rating"].map(rating_map)

    filtered_data = s_book_data[
        (s_book_data["rating"] >= min_rate) & (s_book_data["price (£)"] <= max_price)
    ]

    display(filtered_data)

# Example usage
scrape_books(min_rate=3, max_price=20)