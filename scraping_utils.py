import pandas as pd
from bs4 import BeautifulSoup
import requests

nb_pages = 50
base_url = "https://books.toscrape.com/catalogue/"


def get_book_url(product):
    book_url = product.find('a').get('href')
    return book_url

def get_book_title(book_soup):
    return book_soup.find('h1').text

def get_book_information(book_soup):
    product_information = {}
    information_table = book_soup.find('table')
    details = information_table.find_all('th')
    for detail in details:
        if detail.text == 'UPC':
            product_information['upc'] = detail.find_next_sibling().text
        if detail.text == 'Price (incl. tax)':
            product_information['price'] = float(detail.find_next_sibling().text[1:])
        if detail.text == 'Availability':
            product_information['availability'] = detail.find_next_sibling().text
    return product_information

def get_book_genre(book_soup):
    return book_soup.select_one('body > div > div > ul > li:nth-child(3) > a').text

def get_book_description(book_soup):
    try:
        return book_soup.select_one('#content_inner > article > p').text
    except:
        return 'no description'
    
def get_book_rating(book_element):
    rating_map = {'One' : 1,
                  'Two' : 2,
                  'Three' : 3,
                  'Four' : 4,
                  'Five' : 5}
    try:
        return rating_map[book_element.select_one('p').get('class')[1]]
    except:
        return pd.nan

def extract_books(books, base_url, min_rating, max_price):
    books_dict = {}
    index = 0
    for book in books:
        book_url = get_book_url(book)
        response = requests.get(base_url + book_url)
        product_page = BeautifulSoup(response.content, "html.parser")
        info = get_book_information(product_page)
        rating = get_book_rating(book)
        if max_price >= info['price'] and min_rating <= rating:
            books_dict[index] = {
            "title": get_book_title(product_page),
            "genre": get_book_genre(product_page),
            "UPC": info['upc'],
            "Price": info['price'],
            "Availability": info['availability'],
            "rating": rating,
            "description": get_book_description(product_page)
            }
            index += 1
    return books_dict

def clean_data(df):
    # Extract the number inside parentheses using regex and convert to int
    df['Availability'] = df['Availability'].str.extract(r'\((\d+)')
    df['Availability'] = pd.to_numeric(df['Availability'], errors='coerce')
    return df

def scrape_books(min_rating, max_price):
    books_dataframes_list = []

    for page_number in range(nb_pages):
        # Print current page number being processed
        print(page_number)
        # Construct URL for current catalog page
        catalog_url = f"page-{page_number + 1}.html"
        # Fetch the catalog page
        response = requests.get(base_url + catalog_url)
        # Parse HTML content using BeautifulSoup
        catalog_page = BeautifulSoup(response.content, "html.parser")
        # Find all book articles on the page
        books = catalog_page.find_all('article', class_='product_pod')
        # Extract book information from products using helper function
        books_dict = extract_books(books, base_url, min_rating, max_price)
        # Convert dictionary of books to pandas DataFrame
        df = pd.DataFrame.from_dict(books_dict, orient='index')
        # Append DataFrame to list of all books
        books_dataframes_list.append(df)

    books_df = pd.concat(books_dataframes_list, ignore_index=True)
    books_df = clean_data(books_df)

    return books_df