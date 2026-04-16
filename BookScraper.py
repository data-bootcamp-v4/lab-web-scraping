import requests
from bs4 import BeautifulSoup
import pandas as pd


class BookScraper:
    def __init__(self):
        self.base_url = "https://books.toscrape.com/"
        self.catalogue_url = "https://books.toscrape.com/catalogue/"
        self.start_url = "https://books.toscrape.com/catalogue/page-1.html"
        self.rating_map = {
            "One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5
        }

    def _get_book_details(self, relative_link):
        clean_link = relative_link.replace('../../../', '')
        if "catalogue/" in clean_link:
            book_url = f"{self.base_url}{clean_link}"
        else:
            book_url = f"{self.catalogue_url}{clean_link}"

        try:
            res = requests.get(book_url, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, 'html.parser')


            upc_node = soup.find('th', string='UPC')
            upc = upc_node.find_next_sibling('td').text if upc_node else "N/A"

            breadcrumb = soup.find('ul', class_='breadcrumb')
            genre = "Unknown"
            if breadcrumb:
                items = breadcrumb.find_all('li')
                if len(items) >= 3:
                    genre = items[2].text.strip()

            avail_node = soup.find('p', class_='instock availability')
            availability = avail_node.text.strip() if avail_node else "Unknown"

            desc_header = soup.find('div', id='product_description')
            description = "No description available"
            if desc_header:
                desc_node = desc_header.find_next_sibling('p')
                if desc_node:
                    description = desc_node.text

            return {
                "upc": upc,
                "genre": genre,
                "availability": availability,
                "description": description
            }
        except Exception as e:
            print(f"Error fetching details for {book_url}: {e}")
            return None

    def scrape_books(self, min_rating, max_price):
        try:
            response = requests.get(self.start_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            books_data = []
            articles = soup.find_all('article', class_='product_pod')

            for article in articles:
                rating_tag = article.find('p', class_='star-rating')
                rating_class = rating_tag['class'][1] if rating_tag else "Zero"
                rating_val = self.rating_map.get(rating_class, 0)
                price_tag = article.find('p', class_='price_color')
                price_text = price_tag.text if price_tag else "£0"
                price_val = float(price_text.replace('£', ''))

                # Filter check
                if rating_val >= min_rating and price_val <= max_price:
                    # 3. Extract Title
                    h3_tag = article.find('h3')
                    link_tag = h3_tag.find('a') if h3_tag else None

                    if link_tag:
                        title = link_tag.get('title', link_tag.text)
                        relative_link = link_tag['href']
                        details = self._get_book_details(relative_link)
                        if details:
                            books_data.append({
                                "UPC": details['upc'],
                                "Title": title,
                                "Price (£)": price_val,
                                "Rating": rating_val,
                                "Genre": details['genre'],
                                "Availability": details['availability'],
                                "Description": details['description']
                            })

            return pd.DataFrame(books_data)

        except Exception as e:
            print(f"Critical error during main scrape: {e}")
            return pd.DataFrame()