import requests
from bs4 import BeautifulSoup
import pandas as pd
import re


# Helper function to map star-rating classes to numbers
def get_star_rating(star_tag):
    rating_mapping = {
        'One': 1,
        'Two': 2,
        'Three': 3,
        'Four': 4,
        'Five': 5
    }
    rating_class = star_tag['class'][1]
    return rating_mapping.get(rating_class, 0)  # Return 0 if no rating found


def scrape_books(min_rating=4.0, max_price=20.0):
    base_url = "https://books.toscrape.com/catalogue/page-{}.html"
    total_pages = 50
    all_books_data = []

    # Loop through all pages
    for page_num in range(1, total_pages + 1):
        page_url = base_url.format(page_num)
        response = requests.get(page_url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all books on the current page
        all_books = soup.find_all('h3')

        for book in all_books:
            book_url = book.find('a')['href']
            full_book_url = f"https://books.toscrape.com/catalogue/{book_url}"

            # Request book details page
            book_response = requests.get(full_book_url)
            book_soup = BeautifulSoup(book_response.text, "html.parser")

            # Extract UPC, title, genre, price, rating, availability, and description
            book_title = book_soup.find('h1').text
            product_info = book_soup.find('table', class_='table table-striped')
            info_cells = product_info.find_all('td')
            upc = info_cells[0].text
            price = float(re.sub(r'[^\d.]', '', info_cells[3].text))

            availability = info_cells[5].text.strip()

            # Extract rating
            rating_tag = book_soup.find('p', class_='star-rating')
            rating = get_star_rating(rating_tag)

            # Extract genre (last breadcrumb element is the genre)
            genre = book_soup.find('ul', class_='breadcrumb').find_all('li')[2].text.strip()

            # Extract description (last paragraph)
            description_tag = book_soup.find('div', id='product_description')
            if description_tag:
                book_description = description_tag.find_next_sibling('p').text.strip()
            else:
                book_description = "No description available."

            # Filter based on min_rating and max_price
            if rating >= min_rating and price <= max_price:
                all_books_data.append({
                    'UPC': upc,
                    'Title': book_title,
                    'Price (£)': price,
                    'Rating': rating,
                    'Genre': genre,
                    'Availability': availability,
                    'Description': book_description
                })

    # Convert the data to a pandas DataFrame
    books_df = pd.DataFrame(all_books_data)

    # Return the DataFrame
    return books_df


# Scrape books with minimum rating of 4.0 and maximum price of £20
books_df = scrape_books(min_rating=4.0, max_price=20.0)

# Display the DataFrame
print(books_df)
