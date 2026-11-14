
import re
import time
import requests
import pandas as pd

from bs4 import BeautifulSoup


# Endereço principal do site
BASE_URL = "https://books.toscrape.com/"


# Função para construir URLs sem utilizar urljoin
def construir_url(url_atual, link):

    # Se o link já for um endereço completo
    if link.startswith("http://") or link.startswith("https://"):
        return link

    # Se o link começar por uma barra
    if link.startswith("/"):
        dominio = "https://books.toscrape.com"
        return dominio + link

    # Obter a pasta da página atual
    pasta = url_atual.rsplit("/", 1)[0]

    # Juntar a pasta com o link relativo
    return pasta + "/" + link


# Função principal de Web Scraping
def scrape_books(min_rating, max_price):

    # Validar os parâmetros
    if not 1 <= min_rating <= 5:
        raise ValueError("A avaliação deve estar entre 1 e 5.")

    if max_price < 0:
        raise ValueError("O preço máximo não pode ser negativo.")

    # Criar uma sessão para as requisições
    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    # Lista que irá guardar os dados dos livros
    books_data = []

    # URL inicial do catálogo
    current_url = BASE_URL

    try:

        # Percorrer todas as páginas do catálogo
        while current_url:

            print(f"\nConsultando página: {current_url}")

            # Fazer a requisição HTTP
            response = session.get(current_url, timeout=20)

            # Verificar se ocorreu algum erro HTTP
            response.raise_for_status()

            # Interpretar o HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Encontrar todos os cartões de livros
            book_cards = soup.select("article.product_pod")

            # Percorrer cada livro da página
            for card in book_cards:

               
                # 1. Extrair o título
            
                title_element = card.select_one("h3 a")

                if title_element is None:
                    continue

                title = title_element.get("title", "").strip()

               
                # 2. Extrair o preço
               
                price_element = card.select_one("p.price_color")

                if price_element is None:
                    continue

                price_text = price_element.get_text(strip=True)

                # Extrair o número do preço
                price_match = re.search(
                    r"\d+(?:\.\d+)?",
                    price_text
                )

                if not price_match:
                    continue

                price = float(price_match.group())

               
                # 3. Extrair a avaliação
                

                rating_element = card.select_one("p.star-rating")

                if rating_element is None:
                    continue

                rating_classes = rating_element.get("class", [])

                # Converter palavras em números
                rating_map = {
                    "One": 1,
                    "Two": 2,
                    "Three": 3,
                    "Four": 4,
                    "Five": 5
                }

                rating = None

                for css_class in rating_classes:

                    if css_class in rating_map:
                        rating = rating_map[css_class]
                        break

                if rating is None:
                    continue

           
                # 4. Aplicar os filtros
                

                # Ignorar livros abaixo da avaliação mínima
                if rating < min_rating:
                    continue

                # Ignorar livros acima do preço máximo
                if price > max_price:
                    continue

               
                # 5. Construir o link do livro
                
                relative_url = title_element.get("href")

                if not relative_url:
                    continue

                book_url = construir_url(
                    current_url,
                    relative_url
                )

                print(f"Livro selecionado: {title}")

                # Pequena pausa entre requisições
                time.sleep(0.2)

                
                # 6. Acessar a página individual
              

                detail_response = session.get(
                    book_url,
                    timeout=20
                )

                detail_response.raise_for_status()

                detail_soup = BeautifulSoup(
                    detail_response.text,
                    "html.parser"
                )

             
                # 7. Extrair o UPC
                
                upc = None

                rows = detail_soup.select(
                    "table.table-striped tr"
                )

                for row in rows:

                    header = row.find("th")

                    if (
                        header
                        and header.get_text(strip=True) == "UPC"
                    ):

                        value = row.find("td")

                        if value:
                            upc = value.get_text(strip=True)

                        break

                
                # 8. Extrair o gênero
                

                genre = None

                breadcrumb = detail_soup.select(
                    "ul.breadcrumb li"
                )

                if len(breadcrumb) >= 3:
                    genre = breadcrumb[2].get_text(strip=True)

                
                # 9. Extrair a disponibilidade
                

                availability_element = detail_soup.select_one(
                    "p.instock.availability"
                )

                if availability_element:

                    availability = availability_element.get_text(
                        " ",
                        strip=True
                    )

                else:

                    availability = "Disponibilidade desconhecida"

                
                # 10. Extrair a descrição
                

                description = None

                description_heading = detail_soup.select_one(
                    "#product_description"
                )

                if description_heading:

                    description_element = (
                        description_heading.find_next_sibling("p")
                    )

                    if description_element:

                        description = description_element.get_text(
                            " ",
                            strip=True
                        )

                
                # 11. Guardar os dados do livro
                

                books_data.append({
                    "UPC": upc,
                    "Title": title,
                    "Price (£)": price,
                    "Rating": rating,
                    "Genre": genre,
                    "Availability": availability,
                    "Description": description
                })

            
            # 12. Encontrar a próxima página
           

            next_link = soup.select_one("li.next a")

            if next_link and next_link.get("href"):

                next_relative_url = next_link["href"]

                current_url = construir_url(
                    current_url,
                    next_relative_url
                )

            else:

                # Não existem mais páginas
                current_url = None

    finally:

        # Fechar a sessão HTTP
        session.close()

    
    # 13. Criar o DataFrame
    

    columns = [
        "UPC",
        "Title",
        "Price (£)",
        "Rating",
        "Genre",
        "Availability",
        "Description"
    ]

    df = pd.DataFrame(
        books_data,
        columns=columns
    )

    return df



# EXECUTAR O PROGRAMA

if __name__ == "__main__":

    # Chamar a função com os parâmetros do exercício
    df_books = scrape_books(
        min_rating=4.0,
        max_price=20.0
    )

    # Mostrar os resultados no terminal
    print("\n========== RESULTADOS ==========")

    print(df_books.to_string(index=False))

    # Mostrar a quantidade de livros
    print(f"\nTotal de livros encontrados: {len(df_books)}")

    # Guardar os resultados num arquivo CSV
    df_books.to_csv(
        "books_filtered.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nArquivo criado: books_filtered.csv")
