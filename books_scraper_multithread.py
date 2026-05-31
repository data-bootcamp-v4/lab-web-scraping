from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import time
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor

thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()

    return thread_local.session

def scrape_book_link(url):
    book_links = list()

    start = time.time()
    print("Start to fetch book links.")
    session = requests.Session()
    
    for i in range(1,51):
        try:
            if i == 1:
                page = url
            else:
                page = f"https://books.toscrape.com/catalogue/page-{i}.html"
            response = session.get(page, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            links = soup.select("article.product_pod h3 a")
            
            if not links:
                print(f"Page error, book links not found: {page}")
                continue
    
            for a in links:
                book_link = urljoin(
                    page,
                    a["href"]
                )
    
                book_links.append(book_link)
    
        except requests.exceptions.RequestException:
            print(f"Failed to fetch page: {page}")
            continue

    end = time.time()
    print(f"Fetch book links successfully! Time used: {end-start:.2f}s")
    return book_links

def scrape_one_book(book_url):
    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }

    session = get_session()
    
    try:
        response = session.get(book_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        book_info = soup.select_one("article.product_page")
        genre = soup.select("ul.breadcrumb li")[2].get_text(strip=True)
          
        if book_info is None:
            print(f"page error, book info not found: {book}")
            return None
    
        info = {}
        for row in book_info.select("table.table.table-striped tr"):
            key = row.select_one("th").get_text(strip=True)
            value = row.select_one("td").get_text(strip=True)
            info[key]=value
    
        description_tag = book_info.find("p", recursive=False)
            
        return {
             'upc': info['UPC'],
             'title': book_info.select_one('.product_main h1').text.strip(),
             'price': float(info['Price (incl. tax)'].replace('£', '')),
             'rating': rating_map[book_info.select_one(".product_main p.star-rating")["class"][1]],
             'genre': genre,
             'availability': info['Availability'],
             'description': description_tag.get_text(strip=True) if description_tag else ''
        }
    
    except Exception as e:
        print(f"Failed: {book_url}")
        return None
            
def scrape_book(book_links):
    start = time.time()
    print("Start to scrape books' info.")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        books = [
            result
            for result in executor.map(scrape_one_book, book_links)
            if result is not None
        ]
    
    end = time.time()
    print(f"Complete! Time used: {end-start:.2f}s")

    return pd.DataFrame(books)
