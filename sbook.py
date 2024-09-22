##### import all modules, seturl etc...

import requests, time, random
from bs4 import BeautifulSoup
import pandas as pd

def scrape_books(min_rate, max_price):
    ### 1a make it dynamic so to account for all pages (and not the first 2 results)

    response_list=[]
    for i in range(1,51):
        response = requests.get(f"https://books.toscrape.com/catalogue/page-{i}.html")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            response_list.append(soup)
            
        else:
            print(f"Failed to get #{i}")
            
        time.sleep(random.uniform(0.5, 2))
        
    ### make a list of products

    book_dict = {}
    k_value = 1

    for page in response_list:
        products = page.find_all("li", attrs = {"class":"col-xs-6"})
        for prod in products:
            #get title
            title = prod.find_all("a")[1]["title"]
            #price
            price = float(prod.find_all("p")[1].get_text().replace("£",""))
            #rating
            rating = prod.find_all("p")[0]["class"][1]
            # href
            url="https://books.toscrape.com/catalogue/"
            href = url + prod.find_all("a")[1]["href"]
            extra = BeautifulSoup(requests.get(href).content, 'html.parser')
            # genre
            genre = extra.find_all("ul")[0]
            genre = genre.find_all("li")[2].get_text().strip()
            # availability
            availability = extra.find_all("p")[1].get_text().strip()
            # description
            description = extra.find_all("p")[3].get_text()
            # UPC
            upc = extra.find_all("td")[0].get_text()        
            #UPC, Title, Price (£), Rating, Genre, Availability, Description    
            book_dict[k_value] = {"title": title,
                                    "price (£)": price,
                                    "rating": rating,
                                    "genre":genre,
                                    "availability": availability,
                                    "description": description,
                                    "href": href,
                                    "UPC": upc
                                    }
            
            k_value += 1
        
    # 2. filter the results by requirements

    s_book_data = pd.DataFrame.from_dict(book_dict, orient='index')
    s_book_data["rating"] = s_book_data["rating"].map({"One":1, "Two":2, "Three":3, "Four":4, "Five":5})

    filtered_data = s_book_data[(s_book_data["rating"] >= min_rate) & (s_book_data["price (£)"] <= max_price)]

    # def scrape_books(min_rate, max_price):

    print(filtered_data)

